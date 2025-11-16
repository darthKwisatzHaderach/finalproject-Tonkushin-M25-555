"""Бизнес-логика приложения."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
)
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import (
    PORTFOLIOS_FILE,
    RATES_FILE,
    USERS_FILE,
    get_exchange_rate,
    load_json,
    save_json,
    validate_amount,
    validate_currency_code,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader

# Получаем экземпляр SettingsLoader (Singleton)
_settings = SettingsLoader()

# Глобальная переменная для текущего залогиненного пользователя
_current_user: User | None = None
_current_portfolio: Portfolio | None = None


def get_current_user() -> User | None:
    """
    Получить текущего залогиненного пользователя.

    Returns:
        Объект User или None, если пользователь не залогинен
    """
    return _current_user


def get_current_portfolio() -> Portfolio | None:
    """
    Получить портфель текущего пользователя.

    Returns:
        Объект Portfolio или None, если пользователь не залогинен
    """
    return _current_portfolio


def require_login() -> User:
    """
    Проверить, что пользователь залогинен.

    Returns:
        Объект User текущего пользователя

    Raises:
        RuntimeError: Если пользователь не залогинен
    """
    user = get_current_user()
    if user is None:
        raise RuntimeError("Необходимо войти в систему")
    return user


def require_portfolio() -> Portfolio:
    """
    Проверить, что портфель загружен.

    Returns:
        Объект Portfolio текущего пользователя

    Raises:
        RuntimeError: Если портфель не загружен
    """
    portfolio = get_current_portfolio()
    if portfolio is None:
        raise RuntimeError("Портфель не загружен")
    return portfolio


@log_action("REGISTER")
def register_user(username: str, password: str) -> tuple[User, int]:
    """
    Зарегистрировать нового пользователя.

    Args:
        username: Имя пользователя
        password: Пароль пользователя

    Returns:
        Кортеж (объект User, user_id)

    Raises:
        ValueError: Если имя пользователя уже занято или пароль слишком короткий
    """
    # Проверка длины пароля
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    # Загружаем список пользователей
    users_data = load_json(USERS_FILE)

    # Проверка уникальности username
    username_lower = username.lower()
    for user_data in users_data:
        if user_data.get("username", "").lower() == username_lower:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

    # Генерируем user_id (автоинкремент)
    if users_data:
        user_id = max(user.get("user_id", 0) for user in users_data) + 1
    else:
        user_id = 1

    # Генерируем соль и хешируем пароль
    salt = secrets.token_hex(8)
    password_with_salt = password + salt
    hashed_password = hashlib.sha256(
        password_with_salt.encode("utf-8")
    ).hexdigest()

    # Создаём объект User
    registration_date = datetime.now()
    user = User(
        user_id=user_id,
        username=username,
        hashed_password=hashed_password,
        salt=salt,
        registration_date=registration_date,
    )

    # Сохраняем пользователя в users.json
    user_data = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password,
        "salt": salt,
        "registration_date": registration_date.isoformat(),
    }
    users_data.append(user_data)
    save_json(USERS_FILE, users_data)

    # Создаём пустой портфель в portfolios.json
    portfolios_data = load_json(PORTFOLIOS_FILE)
    # Если portfolios.json был объектом, преобразуем в список
    if isinstance(portfolios_data, dict):
        portfolios_data = []
    portfolios_data.append(
        {
            "user_id": user_id,
            "wallets": {},
        }
    )
    save_json(PORTFOLIOS_FILE, portfolios_data)

    return user, user_id


def load_portfolio_from_json(user_id: int) -> Portfolio:
    """
    Загрузить портфель пользователя из JSON.

    Args:
        user_id: Идентификатор пользователя

    Returns:
        Объект Portfolio

    Raises:
        ValueError: Если портфель не найден
    """
    portfolios_data = load_json(PORTFOLIOS_FILE)
    # Если portfolios.json был объектом, преобразуем в список
    if isinstance(portfolios_data, dict):
        portfolios_data = []

    # Ищем портфель пользователя
    portfolio_data = None
    for p in portfolios_data:
        if p.get("user_id") == user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        # Создаём пустой портфель, если не найден
        portfolio_data = {"user_id": user_id, "wallets": {}}
        portfolios_data.append(portfolio_data)
        save_json(PORTFOLIOS_FILE, portfolios_data)

    # Создаём словарь кошельков
    wallets: dict[str, Wallet] = {}
    wallets_data = portfolio_data.get("wallets", {})
    for currency_code, wallet_data in wallets_data.items():
        balance = wallet_data.get("balance", 0.0)
        wallets[currency_code] = Wallet(currency_code, balance)

    # Создаём объект Portfolio
    portfolio = Portfolio(user_id=user_id, wallets=wallets)
    return portfolio


@log_action("LOGIN")
def login_user(username: str, password: str) -> User:
    """
    Войти в систему.

    Args:
        username: Имя пользователя
        password: Пароль пользователя

    Returns:
        Объект User

    Raises:
        ValueError: Если пользователь не найден или неверный пароль
    """
    global _current_user, _current_portfolio

    # Загружаем список пользователей
    users_data = load_json(USERS_FILE)

    # Ищем пользователя по username
    user_data = None
    username_lower = username.lower()
    for u in users_data:
        if u.get("username", "").lower() == username_lower:
            user_data = u
            break

    if user_data is None:
        raise ValueError(f"Пользователь '{username}' не найден")

    # Создаём объект User из данных
    registration_date_str = user_data.get("registration_date", "")
    registration_date = datetime.fromisoformat(registration_date_str)
    user = User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        hashed_password=user_data["hashed_password"],
        salt=user_data["salt"],
        registration_date=registration_date,
    )

    # Проверяем пароль
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    # Загружаем портфель
    portfolio = load_portfolio_from_json(user.user_id)

    # Устанавливаем текущего пользователя и портфель
    _current_user = user
    _current_portfolio = portfolio

    return user


def get_portfolio_info(base_currency: str | None = None) -> dict:
    """
    Получить информацию о портфеле текущего пользователя.

    Args:
        base_currency: Базовая валюта для конвертации
                       (если None, берётся из конфигурации)

    Returns:
        Словарь с информацией о портфеле:
        {
            "user": User,
            "portfolio": Portfolio,
            "base_currency": str,
            "wallets_info": [
                {
                    "currency_code": str,
                    "balance": float,
                    "value_in_base": float
                },
                ...
            ],
            "total_value": float
        }

    Raises:
        RuntimeError: Если пользователь не залогинен
        ValueError: Если базовая валюта неизвестна
    """
    user = require_login()
    portfolio = require_portfolio()

    # Получаем базовую валюту из конфигурации, если не указана
    if base_currency is None:
        base_currency = _settings.get("default_base_currency", "USD")

    # Валидируем базовую валюту
    base_currency = validate_currency_code(base_currency)

    # Загружаем курсы
    rates_data = load_json(RATES_FILE)

    # Проверяем, что базовая валюта поддерживается
    # Пытаемся получить курс USD -> base_currency для проверки
    try:
        get_exchange_rate("USD", base_currency, rates_data)
    except ValueError:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

    wallets_info = []
    total_value = 0.0

    for currency_code, wallet in portfolio.wallets.items():
        balance = wallet.balance
        if balance > 0:
            # Конвертируем в базовую валюту
            if currency_code == base_currency:
                value_in_base = balance
            else:
                rate = get_exchange_rate(currency_code, base_currency, rates_data)
                value_in_base = balance * rate

            wallets_info.append(
                {
                    "currency_code": currency_code,
                    "balance": balance,
                    "value_in_base": value_in_base,
                }
            )
            total_value += value_in_base

    return {
        "user": user,
        "portfolio": portfolio,
        "base_currency": base_currency,
        "wallets_info": wallets_info,
        "total_value": total_value,
    }


def save_portfolio_to_json(portfolio: Portfolio) -> None:
    """
    Сохранить портфель в JSON.

    Безопасная операция: чтение→модификация→запись.
    Все изменения выполняются в памяти перед записью.

    Args:
        portfolio: Объект Portfolio для сохранения
    """
    # Безопасная операция: чтение
    portfolios_data = load_json(PORTFOLIOS_FILE)
    # Если portfolios.json был объектом, преобразуем в список
    if isinstance(portfolios_data, dict):
        portfolios_data = []

    # Ищем портфель пользователя
    portfolio_data = None
    portfolio_index = None
    for i, p in enumerate(portfolios_data):
        if p.get("user_id") == portfolio.user_id:
            portfolio_data = p
            portfolio_index = i
            break

    # Создаём словарь кошельков из объектов Wallet
    wallets_data: dict[str, dict[str, float]] = {}
    for currency_code, wallet in portfolio.wallets.items():
        wallets_data[currency_code] = {"balance": wallet.balance}

    # Обновляем или создаём запись портфеля
    if portfolio_data is not None:
        portfolios_data[portfolio_index]["wallets"] = wallets_data
    else:
        portfolios_data.append(
            {
                "user_id": portfolio.user_id,
                "wallets": wallets_data,
            }
        )

    # Безопасная операция: запись (модификация уже выполнена в памяти)
    save_json(PORTFOLIOS_FILE, portfolios_data)


@log_action("BUY", verbose=True)
def buy_currency(
    currency: str, amount: float, base_currency: str | None = None
) -> dict:
    """
    Купить валюту.

    Args:
        currency: Код покупаемой валюты
        amount: Количество покупаемой валюты
        base_currency: Базовая валюта для расчёта стоимости
                       (если None, берётся из конфигурации)

    Returns:
        Словарь с информацией о покупке:
        {
            "currency": str,
            "amount": float,
            "old_balance": float,
            "new_balance": float,
            "rate": float,
            "cost_in_base": float
        }

    Raises:
        RuntimeError: Если пользователь не залогинен
        CurrencyNotFoundError: Если валюта не найдена
        ValueError: Если валидация не прошла или не удалось получить курс
        ApiRequestError: Если произошла ошибка при обращении к API
    """
    require_login()
    portfolio = require_portfolio()

    # Получаем базовую валюту из конфигурации, если не указана
    if base_currency is None:
        base_currency = _settings.get("default_base_currency", "USD")

    # Валидация amount > 0
    amount = validate_amount(amount)

    # Валидация currency_code через get_currency()
    try:
        currency_obj = get_currency(currency)
        currency = currency_obj.code  # Получаем нормализованный код
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(currency)

    # Валидация base_currency через get_currency()
    try:
        base_currency_obj = get_currency(base_currency)
        base_currency = base_currency_obj.code
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(base_currency)

    # Загружаем курсы (безопасная операция: чтение)
    rates_data = load_json(RATES_FILE)

    # Получаем курс для расчёта стоимости
    try:
        rate = get_exchange_rate(currency, base_currency, rates_data)
    except ValueError as e:
        raise ValueError(
            f"Не удалось получить курс для {currency}→{base_currency}"
        ) from e

    # Получаем или создаём кошелёк для покупаемой валюты
    wallet = portfolio.get_wallet(currency)
    old_balance = 0.0
    if wallet is None:
        wallet = portfolio.add_currency(currency)
    else:
        old_balance = wallet.balance

    # Увеличиваем баланс
    wallet.deposit(amount)
    new_balance = wallet.balance

    # Обновляем глобальный портфель
    global _current_portfolio
    _current_portfolio = portfolio

    # Сохраняем портфель в JSON (безопасная операция: чтение→модификация→запись)
    save_portfolio_to_json(portfolio)

    # Рассчитываем стоимость покупки
    cost_in_base = amount * rate

    return {
        "currency": currency,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "rate": rate,
        "cost_in_base": cost_in_base,
        "base_currency": base_currency,
    }


@log_action("SELL", verbose=True)
def sell_currency(
    currency: str, amount: float, base_currency: str | None = None
) -> dict:
    """
    Продать валюту.

    Args:
        currency: Код продаваемой валюты
        amount: Количество продаваемой валюты
        base_currency: Базовая валюта для расчёта выручки
                       (если None, берётся из конфигурации)

    Returns:
        Словарь с информацией о продаже:
        {
            "currency": str,
            "amount": float,
            "old_balance": float,
            "new_balance": float,
            "rate": float,
            "revenue_in_base": float
        }

    Raises:
        RuntimeError: Если пользователь не залогинен
        CurrencyNotFoundError: Если валюта не найдена
        InsufficientFundsError: Если недостаточно средств
        ValueError: Если валидация не прошла или кошелёк не найден
        ApiRequestError: Если произошла ошибка при обращении к API
    """
    require_login()
    portfolio = require_portfolio()

    # Получаем базовую валюту из конфигурации, если не указана
    if base_currency is None:
        base_currency = _settings.get("default_base_currency", "USD")

    # Валидация amount > 0
    amount = validate_amount(amount)

    # Валидация currency_code через get_currency()
    try:
        currency_obj = get_currency(currency)
        currency = currency_obj.code  # Получаем нормализованный код
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(currency)

    # Валидация base_currency через get_currency()
    try:
        base_currency_obj = get_currency(base_currency)
        base_currency = base_currency_obj.code
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(base_currency)

    # Проверяем, что кошелёк существует
    wallet = portfolio.get_wallet(currency)
    if wallet is None:
        raise ValueError(
            f"У вас нет кошелька '{currency}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    # Сохраняем старый баланс
    old_balance = wallet.balance

    # Уменьшаем баланс (выбросит InsufficientFundsError, если недостаточно средств)
    wallet.withdraw(amount)
    new_balance = wallet.balance

    # Загружаем курсы для расчёта выручки (безопасная операция: чтение)
    rates_data = load_json(RATES_FILE)

    # Получаем курс для расчёта выручки
    try:
        rate = get_exchange_rate(currency, base_currency, rates_data)
    except ValueError as e:
        raise ValueError(
            f"Не удалось получить курс для {currency}→{base_currency}"
        ) from e

    # Опционально: начисляем эквивалент в базовой валюте
    # Если есть кошелёк базовой валюты, начисляем туда выручку
    base_wallet = portfolio.get_wallet(base_currency)
    if base_wallet is not None:
        revenue_in_base = amount * rate
        base_wallet.deposit(revenue_in_base)
    else:
        # Если кошелька базовой валюты нет, просто рассчитываем выручку для отчёта
        revenue_in_base = amount * rate

    # Обновляем глобальный портфель
    global _current_portfolio
    _current_portfolio = portfolio

    # Сохраняем портфель в JSON (безопасная операция: чтение→модификация→запись)
    save_portfolio_to_json(portfolio)

    return {
        "currency": currency,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "rate": rate,
        "revenue_in_base": revenue_in_base,
        "base_currency": base_currency,
    }


def _is_rate_fresh(updated_at_str: str, max_age_seconds: int | None = None) -> bool:
    """
    Проверить, свежий ли курс.

    Args:
        updated_at_str: Строка с датой обновления в формате ISO
        max_age_seconds: Максимальный возраст курса в секундах
                         (если None, берётся из конфигурации)

    Returns:
        True если курс свежий, иначе False
    """
    if max_age_seconds is None:
        # Получаем TTL из конфигурации (Singleton)
        max_age_seconds = _settings.get("rates_ttl_seconds", 300)

    try:
        updated_at = datetime.fromisoformat(updated_at_str)
        age = datetime.now() - updated_at
        return age < timedelta(seconds=max_age_seconds)
    except (ValueError, TypeError):
        return False


def _update_rate_in_cache(
    from_currency: str, to_currency: str, rate: float, rates_data: dict
) -> None:
    """
    Обновить курс в кеше.

    Безопасная операция: модификация→запись.
    Данные уже загружены в памяти (rates_data).

    Args:
        from_currency: Исходная валюта
        to_currency: Целевая валюта
        rate: Курс обмена
        rates_data: Данные курсов для обновления (уже загружены)
    """
    rate_key = f"{from_currency}_{to_currency}"
    now = datetime.now()
    # Модификация в памяти
    rates_data[rate_key] = {
        "rate": rate,
        "updated_at": now.isoformat(),
    }
    rates_data["last_refresh"] = now.isoformat()
    # Безопасная операция: запись
    save_json(RATES_FILE, rates_data)


def _get_rate_from_stub(from_currency: str, to_currency: str) -> float:
    """
    Получить курс из заглушки (фиксированные курсы).

    Args:
        from_currency: Исходная валюта
        to_currency: Целевая валюта

    Returns:
        Курс обмена

    Raises:
        ValueError: Если курс не найден
    """
    # Фиксированные курсы (заглушка)
    fallback_rates: dict[str, float] = {
        "USD": 1.0,
        "EUR": 1.1,
        "BTC": 45000.0,
        "ETH": 3000.0,
        "RUB": 0.011,
    }

    # Если валюты одинаковые
    if from_currency == to_currency:
        return 1.0

    # Конвертируем через USD
    if from_currency in fallback_rates and to_currency in fallback_rates:
        from_to_usd = fallback_rates[from_currency]
        usd_to_to = 1.0 / fallback_rates[to_currency]
        return from_to_usd * usd_to_to

    raise ValueError(f"Курс {from_currency}→{to_currency} не найден в заглушке")


def get_rate(from_currency: str, to_currency: str) -> dict:
    """
    Получить курс обмена между валютами с проверкой кеша.

    Args:
        from_currency: Исходная валюта
        to_currency: Целевая валюта

    Returns:
        Словарь с информацией о курсе:
        {
            "from_currency": str,
            "to_currency": str,
            "rate": float,
            "updated_at": str,
            "reverse_rate": float
        }

    Raises:
        CurrencyNotFoundError: Если валюта не найдена
        ApiRequestError: Если произошла ошибка при обращении к API
        ValueError: Если валидация не прошла
    """
    # Валидация кодов валют через get_currency()
    # Это также проверяет, что валюты существуют в регистре
    try:
        from_currency_obj = get_currency(from_currency)
        from_currency = from_currency_obj.code  # Получаем нормализованный код
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(from_currency)

    try:
        to_currency_obj = get_currency(to_currency)
        to_currency = to_currency_obj.code  # Получаем нормализованный код
    except CurrencyNotFoundError:
        raise CurrencyNotFoundError(to_currency)

    # Если валюты одинаковые
    if from_currency == to_currency:
        now = datetime.now()
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": 1.0,
            "updated_at": now.isoformat(),
            "reverse_rate": 1.0,
        }

    # Загружаем курсы
    rates_data = load_json(RATES_FILE)

    # Пытаемся найти курс в кеше
    rate_key = f"{from_currency}_{to_currency}"
    rate = None
    updated_at_str = None
    needs_update = True

    if rate_key in rates_data and "rate" in rates_data[rate_key]:
        rate_data = rates_data[rate_key]
        rate = float(rate_data["rate"])
        updated_at_str = rate_data.get("updated_at")
        if updated_at_str and _is_rate_fresh(updated_at_str):
            needs_update = False

    # Если курс не свежий или не найден, обновляем
    if needs_update:
        try:
            # TODO: использовать Parser Service вместо заглушки
            rate = _get_rate_from_stub(from_currency, to_currency)
            _update_rate_in_cache(from_currency, to_currency, rate, rates_data)
            updated_at_str = datetime.now().isoformat()
        except ValueError as e:
            # Если не удалось получить курс, пробуем обратный
            reverse_key = f"{to_currency}_{from_currency}"
            if reverse_key in rates_data and "rate" in rates_data[reverse_key]:
                reverse_rate_data = rates_data[reverse_key]
                reverse_rate = float(reverse_rate_data["rate"])
                rate = 1.0 / reverse_rate
                updated_at_str = reverse_rate_data.get("updated_at")
                if updated_at_str and _is_rate_fresh(updated_at_str):
                    # Обновляем прямой курс на основе обратного
                    _update_rate_in_cache(from_currency, to_currency, rate, rates_data)
                    updated_at_str = datetime.now().isoformat()
                else:
                    # Симулируем ошибку API (в реальности здесь был бы запрос)
                    raise ApiRequestError(
                        f"Не удалось получить курс {from_currency}→{to_currency}"
                    ) from e
            else:
                # Симулируем ошибку API (в реальности здесь был бы запрос)
                raise ApiRequestError(
                    f"Не удалось получить курс {from_currency}→{to_currency}"
                ) from e

    # Рассчитываем обратный курс
    reverse_rate = 1.0 / rate if rate != 0 else 0.0

    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": rate,
        "updated_at": updated_at_str or datetime.now().isoformat(),
        "reverse_rate": reverse_rate,
    }
