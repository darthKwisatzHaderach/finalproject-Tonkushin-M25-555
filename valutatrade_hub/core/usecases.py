"""Бизнес-логика приложения."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.core.utils import (
    PORTFOLIOS_FILE,
    USERS_FILE,
    load_json,
    save_json,
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
