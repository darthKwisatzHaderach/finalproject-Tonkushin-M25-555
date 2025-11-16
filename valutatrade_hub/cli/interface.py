"""Команды CLI интерфейса."""

import argparse
import sys

from valutatrade_hub.core.usecases import (
    buy_currency,
    get_portfolio_info,
    login_user,
    register_user,
    sell_currency,
)


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
        print(f"- {currency}: было {old_balance_str} → стало {new_balance_str}")
        print(f"Оценочная стоимость покупки: {cost_str} {base_currency}")

        return 0
    except RuntimeError:
        print("Сначала выполните login", file=sys.stderr)
        return 1
    except ValueError as e:
        print(str(e), file=sys.stderr)
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
        print(f"- {currency}: было {old_balance_str} → стало {new_balance_str}")
        print(f"Оценочная выручка: {revenue_str} {base_currency}")

        return 0
    except RuntimeError:
        print("Сначала выполните login", file=sys.stderr)
        return 1
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка продажи: {e}", file=sys.stderr)
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
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

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

    print(f"Неизвестная команда: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
