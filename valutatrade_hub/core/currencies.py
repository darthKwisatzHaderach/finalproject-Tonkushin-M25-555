"""Регистр валют и фабрика для получения валют по коду."""

from __future__ import annotations

from valutatrade_hub.core.exceptions import CurrencyNotFoundError
from valutatrade_hub.core.models import (
    CryptoCurrency,
    Currency,
    FiatCurrency,
)

# Регистр валют
_CURRENCIES: dict[str, Currency] = {}


def _initialize_currencies() -> None:
    """Инициализировать регистр валют."""
    global _CURRENCIES

    if _CURRENCIES:
        return  # Уже инициализирован

    # Фиатные валюты
    _CURRENCIES["USD"] = FiatCurrency(
        name="US Dollar",
        code="USD",
        issuing_country="United States",
    )
    _CURRENCIES["EUR"] = FiatCurrency(
        name="Euro",
        code="EUR",
        issuing_country="Eurozone",
    )
    _CURRENCIES["RUB"] = FiatCurrency(
        name="Russian Ruble",
        code="RUB",
        issuing_country="Russia",
    )

    # Криптовалюты
    _CURRENCIES["BTC"] = CryptoCurrency(
        name="Bitcoin",
        code="BTC",
        algorithm="SHA-256",
        market_cap=1.12e12,  # Примерная капитализация
    )
    _CURRENCIES["ETH"] = CryptoCurrency(
        name="Ethereum",
        code="ETH",
        algorithm="Ethash",
        market_cap=4.5e11,  # Примерная капитализация
    )


def get_currency(code: str) -> Currency:
    """
    Получить валюту по коду.

    Args:
        code: Код валюты

    Returns:
        Объект Currency (FiatCurrency или CryptoCurrency)

    Raises:
        CurrencyNotFoundError: Если валюта с таким кодом не найдена
    """
    _initialize_currencies()

    code = code.strip().upper()
    if code not in _CURRENCIES:
        raise CurrencyNotFoundError(f"Валюта с кодом '{code}' не найдена")

    return _CURRENCIES[code]

