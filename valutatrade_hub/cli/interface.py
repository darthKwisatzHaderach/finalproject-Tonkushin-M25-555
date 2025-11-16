"""Команды CLI интерфейса."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy_currency,
    get_portfolio_info,
    get_rate,
    login_user,
    register_user,
    sell_currency,
)
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater


def cmd_register(args: argparse.Namespace) -> int:
    """
    Обработка команды register.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        user, user_id = register_user(args.username, args.password)
        print(
            f"Пользователь '{user.username}' зарегистрирован (id={user_id}). "
            f"Войдите: login --username {user.username} --password ****"
        )
        return 0
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка регистрации: {e}", file=sys.stderr)
        return 1


def cmd_login(args: argparse.Namespace) -> int:
    """
    Обработка команды login.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        user = login_user(args.username, args.password)
        print(f"Вы вошли как '{user.username}'")
        return 0
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка входа: {e}", file=sys.stderr)
        return 1


def cmd_show_portfolio(args: argparse.Namespace) -> int:
    """
    Обработка команды show-portfolio.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        base_currency = args.base if hasattr(args, "base") and args.base else "USD"
        portfolio_info = get_portfolio_info(base_currency)

        user = portfolio_info["user"]
        base = portfolio_info["base_currency"]
        wallets_info = portfolio_info["wallets_info"]
        total_value = portfolio_info["total_value"]

        print(f"Портфель пользователя '{user.username}' (база: {base}):")

        if not wallets_info:
            print("Кошельков нет")
            return 0

        # Форматируем вывод для каждого кошелька
        for wallet_info in wallets_info:
            currency_code = wallet_info["currency_code"]
            balance = wallet_info["balance"]
            value_in_base = wallet_info["value_in_base"]

            # Форматируем числа с нужным количеством знаков после запятой
            if currency_code in ("BTC", "ETH"):
                balance_str = f"{balance:.4f}"
            else:
                balance_str = f"{balance:.2f}"

            value_str = f"{value_in_base:,.2f}".replace(",", " ")

            print(f"- {currency_code}: {balance_str:>10}  → {value_str:>12} {base}")

        # Итоговая сумма
        total_str = f"{total_value:,.2f}".replace(",", " ")
        print("-" * 40)
        print(f"ИТОГО: {total_str} {base}")

        return 0
    except RuntimeError:
        print("Сначала выполните login", file=sys.stderr)
        return 1
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка отображения портфеля: {e}", file=sys.stderr)
        return 1


def cmd_buy(args: argparse.Namespace) -> int:
    """
    Обработка команды buy.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        purchase_info = buy_currency(args.currency, args.amount)

        currency = purchase_info["currency"]
        amount = purchase_info["amount"]
        old_balance = purchase_info["old_balance"]
        new_balance = purchase_info["new_balance"]
        rate = purchase_info["rate"]
        cost_in_base = purchase_info["cost_in_base"]
        base_currency = purchase_info["base_currency"]

        # Форматируем вывод
        if currency in ("BTC", "ETH"):
            amount_str = f"{amount:.4f}"
            old_balance_str = f"{old_balance:.4f}"
            new_balance_str = f"{new_balance:.4f}"
        else:
            amount_str = f"{amount:.2f}"
            old_balance_str = f"{old_balance:.2f}"
            new_balance_str = f"{new_balance:.2f}"

        rate_str = f"{rate:,.2f}".replace(",", " ")
        cost_str = f"{cost_in_base:,.2f}".replace(",", " ")

        print(
            f"Покупка выполнена: {amount_str} {currency} "
            f"по курсу {rate_str} {base_currency}/{currency}"
        )
        print("Изменения в портфеле:")
        print(f"  {currency}: было {old_balance_str} → стало {new_balance_str}")
        print(f"Оценочная стоимость покупки: {cost_str} {base_currency}")

        return 0
    except RuntimeError:
        print("Ошибка: Сначала выполните login", file=sys.stderr)
        return 1
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "Проверьте список поддерживаемых валют: USD, EUR, RUB, BTC, ETH",
            file=sys.stderr,
        )
        return 1
    except ApiRequestError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "Не удалось получить актуальный курс. Повторите попытку позже.",
            file=sys.stderr,
        )
        return 1
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка покупки: {e}", file=sys.stderr)
        return 1


def cmd_sell(args: argparse.Namespace) -> int:
    """
    Обработка команды sell.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        sale_info = sell_currency(args.currency, args.amount)

        currency = sale_info["currency"]
        amount = sale_info["amount"]
        old_balance = sale_info["old_balance"]
        new_balance = sale_info["new_balance"]
        rate = sale_info["rate"]
        revenue_in_base = sale_info["revenue_in_base"]
        base_currency = sale_info["base_currency"]

        # Форматируем вывод
        if currency in ("BTC", "ETH"):
            amount_str = f"{amount:.4f}"
            old_balance_str = f"{old_balance:.4f}"
            new_balance_str = f"{new_balance:.4f}"
        else:
            amount_str = f"{amount:.2f}"
            old_balance_str = f"{old_balance:.2f}"
            new_balance_str = f"{new_balance:.2f}"

        rate_str = f"{rate:,.2f}".replace(",", " ")
        revenue_str = f"{revenue_in_base:,.2f}".replace(",", " ")

        print(
            f"Продажа выполнена: {amount_str} {currency} "
            f"по курсу {rate_str} {base_currency}/{currency}"
        )
        print("Изменения в портфеле:")
        print(f"  {currency}: было {old_balance_str} → стало {new_balance_str}")
        print(f"Оценочная выручка: {revenue_str} {base_currency}")

        return 0
    except RuntimeError:
        print("Ошибка: Сначала выполните login", file=sys.stderr)
        return 1
    except InsufficientFundsError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "Проверьте баланс кошелька с помощью команды 'show-portfolio'",
            file=sys.stderr,
        )
        return 1
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "Проверьте список поддерживаемых валют: USD, EUR, RUB, BTC, ETH",
            file=sys.stderr,
        )
        return 1
    except ApiRequestError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "Не удалось получить актуальный курс. Повторите попытку позже.",
            file=sys.stderr,
        )
        return 1
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка продажи: {e}", file=sys.stderr)
        return 1


def cmd_update_rates(args: argparse.Namespace) -> int:
    """
    Обработка команды update-rates.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    print("INFO: Starting rates update...")

    try:
        config = ParserConfig()
        clients = []

        # Если указан источник, создаём только нужный клиент
        if hasattr(args, "source") and args.source:
            source = args.source.lower()
            if source == "coingecko":
                clients = [CoinGeckoClient(config)]
            elif source == "exchangerate":
                clients = [ExchangeRateApiClient(config)]
            else:
                print(
                    f"Ошибка: Неизвестный источник '{args.source}'. "
                    "Используйте 'coingecko' или 'exchangerate'",
                    file=sys.stderr,
                )
                return 1
        else:
            # По умолчанию используем все клиенты
            clients = [CoinGeckoClient(config), ExchangeRateApiClient(config)]

        updater = RatesUpdater(config, clients=clients)
        result = updater.run_update()

        # Выводим результаты
        total_pairs = result["total_pairs"]
        errors = result.get("errors", [])
        last_refresh = result.get("timestamp", "")
        sources = result.get("sources", {})

        # Подсчитываем курсы по источникам для вывода
        if not hasattr(args, "source") or not args.source:
            coingecko_count = sum(
                1 for s in sources.values() if s == "CoinGecko"
            )
            exchangerate_count = sum(
                1 for s in sources.values() if s == "ExchangeRate-API"
            )
            if coingecko_count > 0:
                print(f"INFO: Fetching from CoinGecko... OK ({coingecko_count} rates)")
            if exchangerate_count > 0:
                print(
                    f"INFO: Fetching from ExchangeRate-API... "
                    f"OK ({exchangerate_count} rates)"
                )

        # Выводим информацию о записи
        settings = SettingsLoader()
        data_dir = Path(settings.get("data_dir", "data"))
        rates_file = data_dir / "rates.json"
        print(f"INFO: Writing {total_pairs} rates to {rates_file}...")

        if errors:
            print(
                f"Update completed with errors. "
                f"Total rates updated: {total_pairs}. "
                f"Last refresh: {last_refresh}"
            )
            print("Check logs/app.log for details.")
            return 1

        print(
            f"Update successful. Total rates updated: {total_pairs}. "
            f"Last refresh: {last_refresh}"
        )
        return 0

    except ApiRequestError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Check logs/app.log for details.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка обновления курсов: {e}", file=sys.stderr)
        return 1


def cmd_show_rates(args: argparse.Namespace) -> int:
    """
    Обработка команды show-rates.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        # Загружаем данные из кэша
        settings = SettingsLoader()
        data_dir = Path(settings.get("data_dir", "data"))
        rates_file = data_dir / "rates.json"

        if not rates_file.exists():
            print(
                "Локальный кеш курсов пуст. "
                "Выполните 'update-rates', чтобы загрузить данные.",
                file=sys.stderr,
            )
            return 1

        with open(rates_file, encoding="utf-8") as f:
            cache_data = json.load(f)

        # Поддерживаем оба формата: новый (через "pairs") и старый (прямые пары)
        if "pairs" in cache_data:
            # Новый формат
            pairs = cache_data["pairs"]
            last_refresh = cache_data.get("last_refresh", "unknown")
        else:
            # Старый формат - преобразуем в новый
            pairs = {}
            for key, value in cache_data.items():
                if key not in ("source", "last_refresh") and isinstance(value, dict):
                    pairs[key] = value
            last_refresh = cache_data.get("last_refresh", "unknown")

        # Проверяем, есть ли данные
        if not pairs:
            print(
                "Локальный кеш курсов пуст. "
                "Выполните 'update-rates', чтобы загрузить данные.",
                file=sys.stderr,
            )
            return 1

        # Форматируем дату обновления
        try:
            if last_refresh and last_refresh != "unknown":
                updated_at = datetime.fromisoformat(
                    last_refresh.replace("Z", "+00:00")
                )
                updated_at_str = updated_at.strftime("%Y-%m-%dT%H:%M:%S")
            else:
                updated_at_str = "unknown"
        except (ValueError, TypeError):
            updated_at_str = last_refresh

        # Применяем фильтры
        filtered_pairs: list[tuple[str, dict]] = []

        for pair_key, pair_data in pairs.items():
            from_currency, to_currency = pair_key.split("_", 1)

            # Фильтр по валюте
            if hasattr(args, "currency") and args.currency:
                if from_currency.upper() != args.currency.upper():
                    continue

            # Фильтр по базе
            if hasattr(args, "base") and args.base:
                if to_currency.upper() != args.base.upper():
                    continue

            filtered_pairs.append((pair_key, pair_data))

        # Если фильтр по валюте не дал результатов
        if hasattr(args, "currency") and args.currency and not filtered_pairs:
            print(
                f"Курс для '{args.currency}' не найден в кеше.",
                file=sys.stderr,
            )
            return 1

        # Сортировка для --top
        if hasattr(args, "top") and args.top:
            # Сортируем по курсу (по убыванию)
            filtered_pairs.sort(
                key=lambda x: x[1].get("rate", 0), reverse=True
            )
            # Берем только топ N
            filtered_pairs = filtered_pairs[: args.top]
        else:
            # Сортируем по алфавиту
            filtered_pairs.sort(key=lambda x: x[0])

        # Выводим результаты
        print(f"Rates from cache (updated at {updated_at_str}):")

        if not filtered_pairs:
            print("Нет курсов, соответствующих заданным фильтрам.")
            return 0

        for pair_key, pair_data in filtered_pairs:
            rate = pair_data.get("rate", 0)

            # Форматируем курс в зависимости от валюты
            from_currency = pair_key.split("_", 1)[0]
            if from_currency in ("BTC", "ETH"):
                rate_str = f"{rate:.2f}"
            else:
                rate_str = f"{rate:.5f}"

            print(f"- {pair_key}: {rate_str}")

        return 0

    except Exception as e:
        print(f"Ошибка отображения курсов: {e}", file=sys.stderr)
        return 1


def cmd_get_rate(args: argparse.Namespace) -> int:
    """
    Обработка команды get-rate.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        rate_info = get_rate(args.from_currency, args.to_currency)

        from_currency = rate_info["from_currency"]
        to_currency = rate_info["to_currency"]
        rate = rate_info["rate"]
        updated_at_str = rate_info["updated_at"]
        reverse_rate = rate_info["reverse_rate"]

        # Форматируем дату обновления
        try:
            updated_at = datetime.fromisoformat(updated_at_str)
            updated_at_formatted = updated_at.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            updated_at_formatted = updated_at_str

        # Форматируем курс в зависимости от валют
        if to_currency in ("BTC", "ETH"):
            rate_str = f"{rate:.8f}"
        else:
            rate_str = f"{rate:.5f}"

        # Форматируем обратный курс
        # Если обратный курс очень маленький (< 0.01), используем больше знаков
        if reverse_rate < 0.01:
            reverse_rate_str = f"{reverse_rate:.8f}"
        else:
            reverse_rate_str = f"{reverse_rate:,.2f}".replace(",", " ")

        print(
            f"Курс {from_currency}→{to_currency}: {rate_str} "
            f"(обновлено: {updated_at_formatted})"
        )
        print(f"  Обратный курс {to_currency}→{from_currency}: {reverse_rate_str}")

        return 0
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "Поддерживаемые валюты: USD, EUR, RUB, BTC, ETH",
            file=sys.stderr,
        )
        print(
            "Используйте 'get-rate --help' для справки по использованию команды",
            file=sys.stderr,
        )
        return 1
    except ApiRequestError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        print(
            "Возможные причины:",
            file=sys.stderr,
        )
        print(
            "  - Временная недоступность сервиса получения курсов",
            file=sys.stderr,
        )
        print(
            "  - Проблемы с подключением к сети",
            file=sys.stderr,
        )
        print(
            "Рекомендация: Повторите попытку через несколько секунд",
            file=sys.stderr,
        )
        return 1
    except ValueError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка получения курса: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Создать парсер аргументов командной строки.

    Returns:
        Настроенный ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Валютный кошелек - консольное приложение"
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="Доступные команды",
        metavar="COMMAND",
    )

    # Команда register
    register_parser = subparsers.add_parser(
        "register", help="Зарегистрировать нового пользователя"
    )
    register_parser.add_argument(
        "--username",
        type=str,
        required=True,
        help="Имя пользователя (обязательно, уникально)",
    )
    register_parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="Пароль (обязательно, минимум 4 символа)",
    )

    # Команда login
    login_parser = subparsers.add_parser(
        "login", help="Войти в систему"
    )
    login_parser.add_argument(
        "--username",
        type=str,
        required=True,
        help="Имя пользователя (обязательно)",
    )
    login_parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="Пароль (обязательно)",
    )

    # Команда show-portfolio
    show_portfolio_parser = subparsers.add_parser(
        "show-portfolio", help="Показать портфель пользователя"
    )
    show_portfolio_parser.add_argument(
        "--base",
        type=str,
        default="USD",
        help="Базовая валюта конвертации (по умолчанию USD)",
    )

    # Команда buy
    buy_parser = subparsers.add_parser(
        "buy", help="Купить валюту"
    )
    buy_parser.add_argument(
        "--currency",
        type=str,
        required=True,
        help="Код покупаемой валюты (например, BTC)",
    )
    buy_parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Количество покупаемой валюты (в штуках)",
    )

    # Команда sell
    sell_parser = subparsers.add_parser(
        "sell", help="Продать валюту"
    )
    sell_parser.add_argument(
        "--currency",
        type=str,
        required=True,
        help="Код продаваемой валюты",
    )
    sell_parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Количество продаваемой валюты",
    )

    # Команда get-rate
    get_rate_parser = subparsers.add_parser(
        "get-rate", help="Получить курс обмена валют"
    )
    get_rate_parser.add_argument(
        "--from",
        dest="from_currency",
        type=str,
        required=True,
        help="Исходная валюта (например, USD)",
    )
    get_rate_parser.add_argument(
        "--to",
        dest="to_currency",
        type=str,
        required=True,
        help="Целевая валюта (например, BTC)",
    )

    # Команда update-rates
    update_rates_parser = subparsers.add_parser(
        "update-rates", help="Обновить курсы валют из внешних источников"
    )
    update_rates_parser.add_argument(
        "--source",
        type=str,
        choices=["coingecko", "exchangerate"],
        help="Обновить данные только из указанного источника "
        "(по умолчанию - все)",
    )

    # Команда show-rates
    show_rates_parser = subparsers.add_parser(
        "show-rates", help="Показать курсы валют из локального кеша"
    )
    show_rates_parser.add_argument(
        "--currency",
        type=str,
        help="Показать курс только для указанной валюты (например, BTC)",
    )
    show_rates_parser.add_argument(
        "--top",
        type=int,
        help="Показать N самых дорогих криптовалют",
    )
    show_rates_parser.add_argument(
        "--base",
        type=str,
        help="Показать все курсы относительно указанной базы (например, EUR)",
    )

    return parser


def main() -> int:
    """
    Главная функция CLI.

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Маршрутизация команд
    if args.command == "register":
        return cmd_register(args)
    if args.command == "login":
        return cmd_login(args)
    if args.command == "show-portfolio":
        return cmd_show_portfolio(args)
    if args.command == "buy":
        return cmd_buy(args)
    if args.command == "sell":
        return cmd_sell(args)
    if args.command == "get-rate":
        return cmd_get_rate(args)
    if args.command == "update-rates":
        return cmd_update_rates(args)
    if args.command == "show-rates":
        return cmd_show_rates(args)

    print(f"Неизвестная команда: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
