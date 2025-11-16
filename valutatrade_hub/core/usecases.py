"""Бизнес-логика приложения."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

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


def get_portfolio_info(base_currency: str = "USD") -> dict:
    """
    Получить информацию о портфеле текущего пользователя.

    Args:
        base_currency: Базовая валюта для конвертации

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

    Args:
        portfolio: Объект Portfolio для сохранения
    """
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

    save_json(PORTFOLIOS_FILE, portfolios_data)


def buy_currency(currency: str, amount: float, base_currency: str = "USD") -> dict:
    """
    Купить валюту.

    Args:
        currency: Код покупаемой валюты
        amount: Количество покупаемой валюты
        base_currency: Базовая валюта для расчёта стоимости (по умолчанию USD)

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
        ValueError: Если валидация не прошла или не удалось получить курс
    """
    require_login()
    portfolio = require_portfolio()

    # Валидация
    currency = validate_currency_code(currency)
    amount = validate_amount(amount)

    # Загружаем курсы
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

    # Сохраняем портфель в JSON
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


def sell_currency(currency: str, amount: float, base_currency: str = "USD") -> dict:
    """
    Продать валюту.

    Args:
        currency: Код продаваемой валюты
        amount: Количество продаваемой валюты
        base_currency: Базовая валюта для расчёта выручки (по умолчанию USD)

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
        ValueError: Если валидация не прошла, кошелёк не найден или недостаточно средств
    """
    require_login()
    portfolio = require_portfolio()

    # Валидация
    currency = validate_currency_code(currency)
    amount = validate_amount(amount)

    # Проверяем, что кошелёк существует
    wallet = portfolio.get_wallet(currency)
    if wallet is None:
        raise ValueError(
            f"У вас нет кошелька '{currency}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    # Проверяем, что достаточно средств
    if wallet.balance < amount:
        if currency in ("BTC", "ETH"):
            balance_str = f"{wallet.balance:.4f}"
            amount_str = f"{amount:.4f}"
        else:
            balance_str = f"{wallet.balance:.2f}"
            amount_str = f"{amount:.2f}"
        raise ValueError(
            f"Недостаточно средств: доступно {balance_str} {currency}, "
            f"требуется {amount_str} {currency}"
        )

    # Сохраняем старый баланс
    old_balance = wallet.balance

    # Уменьшаем баланс
    wallet.withdraw(amount)
    new_balance = wallet.balance

    # Загружаем курсы для расчёта выручки
    rates_data = load_json(RATES_FILE)

    # Получаем курс для расчёта выручки
    try:
        rate = get_exchange_rate(currency, base_currency, rates_data)
    except ValueError as e:
        raise ValueError(
            f"Не удалось получить курс для {currency}→{base_currency}"
        ) from e

    # Опционально: начисляем эквивалент в USD
    # Если есть USD кошелёк, начисляем туда выручку
    usd_wallet = portfolio.get_wallet(base_currency)
    if usd_wallet is not None:
        revenue_in_base = amount * rate
        usd_wallet.deposit(revenue_in_base)
    else:
        # Если USD кошелька нет, просто рассчитываем выручку для отчёта
        revenue_in_base = amount * rate

    # Обновляем глобальный портфель
    global _current_portfolio
    _current_portfolio = portfolio

    # Сохраняем портфель в JSON
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
