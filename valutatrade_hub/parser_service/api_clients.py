"""Работа с внешними API (CoinGecko и ExchangeRate-API)."""

from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API-клиентов."""

    def __init__(self, config: ParserConfig) -> None:
        """
        Инициализация клиента.

        Args:
            config: Конфигурация парсера
        """
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """
        Получить курсы валют от API.

        Returns:
            Словарь с курсами в формате {CURRENCY_BASE: rate, ...}
            Например: {"BTC_USD": 59337.21, "EUR_USD": 1.0786}

        Raises:
            ApiRequestError: Если произошла ошибка при обращении к API
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с CoinGecko API."""

    def fetch_rates(self) -> dict[str, float]:
        """
        Получить курсы криптовалют от CoinGecko.

        Returns:
            Словарь с курсами в формате {CRYPTO_USD: rate, ...}

        Raises:
            ApiRequestError: Если произошла ошибка при обращении к API
        """
        url = self.config.get_coingecko_url()

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)

            # Проверяем статус ответа
            if response.status_code != 200:
                raise ApiRequestError(
                    f"CoinGecko API вернул статус {response.status_code}: "
                    f"{response.text[:200]}"
                )

            data = response.json()

            # Преобразуем ответ CoinGecko в стандартизированный формат
            rates: dict[str, float] = {}
            base_currency = self.config.BASE_CURRENCY

            for crypto_code in self.config.CRYPTO_CURRENCIES:
                crypto_id = self.config.CRYPTO_ID_MAP.get(crypto_code)
                if crypto_id and crypto_id in data:
                    crypto_data = data[crypto_id]
                    if "usd" in crypto_data:
                        rate = float(crypto_data["usd"])
                        pair_key = f"{crypto_code}_{base_currency}"
                        rates[pair_key] = rate

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(
                f"Ошибка сети при обращении к CoinGecko: {e}"
            ) from e
        except (KeyError, ValueError, TypeError) as e:
            raise ApiRequestError(
                f"Ошибка парсинга ответа CoinGecko: {e}"
            ) from e


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с ExchangeRate-API."""

    def fetch_rates(self) -> dict[str, float]:
        """
        Получить курсы фиатных валют от ExchangeRate-API.

        Returns:
            Словарь с курсами в формате {FIAT_USD: rate, ...}

        Raises:
            ApiRequestError: Если произошла ошибка при обращении к API
        """
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError(
                "API-ключ для ExchangeRate-API не установлен. "
                "Установите переменную окружения EXCHANGERATE_API_KEY"
            )

        url = self.config.get_exchangerate_url()

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)

            # Проверяем статус ответа
            if response.status_code == 429:
                raise ApiRequestError(
                    "Превышен лимит запросов к ExchangeRate-API. "
                    "Повторите попытку позже."
                )

            if response.status_code != 200:
                raise ApiRequestError(
                    f"ExchangeRate-API вернул статус {response.status_code}: "
                    f"{response.text[:200]}"
                )

            data = response.json()

            # Проверяем успешность ответа
            if data.get("result") != "success":
                error_msg = data.get("error-type", "Unknown error")
                raise ApiRequestError(
                    f"ExchangeRate-API вернул ошибку: {error_msg}"
                )

            # Извлекаем курсы из ответа
            rates: dict[str, float] = {}
            base_currency = data.get("base_code", self.config.BASE_CURRENCY)
            rates_data = data.get("rates", {})

            for fiat_code in self.config.FIAT_CURRENCIES:
                if fiat_code in rates_data:
                    rate = float(rates_data[fiat_code])
                    pair_key = f"{fiat_code}_{base_currency}"
                    rates[pair_key] = rate

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(
                f"Ошибка сети при обращении к ExchangeRate-API: {e}"
            ) from e
        except (KeyError, ValueError, TypeError) as e:
            raise ApiRequestError(
                f"Ошибка парсинга ответа ExchangeRate-API: {e}"
            ) from e
