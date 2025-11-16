"""Бизнес-логика приложения."""

from __future__ import annotations

from valutatrade_hub.core.models import Portfolio, User

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
