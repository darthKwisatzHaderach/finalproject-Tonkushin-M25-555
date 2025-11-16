"""Конфигурация API и параметров обновления."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParserConfig:
    """Конфигурация для Parser Service."""

    # API-ключ загружается из переменной окружения
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")

    # Словарь соответствий кодов криптовалют и их ID в CoinGecko
    CRYPTO_ID_MAP: dict = None

    # Пути к файлам (относительно корня проекта)
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10

    def __post_init__(self) -> None:
        """Инициализация значений по умолчанию."""
        if self.CRYPTO_ID_MAP is None:
            self.CRYPTO_ID_MAP = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            }

    def get_exchangerate_url(self) -> str:
        """
        Получить полный URL для ExchangeRate-API.

        Returns:
            Полный URL с API-ключом и базовой валютой
        """
        return (
            f"{self.EXCHANGERATE_API_URL}/{self.EXCHANGERATE_API_KEY}/"
            f"latest/{self.BASE_CURRENCY}"
        )

    def get_coingecko_url(self) -> str:
        """
        Получить полный URL для CoinGecko.

        Returns:
            Полный URL с параметрами запроса
        """
        # Формируем список ID криптовалют
        crypto_ids = [
            self.CRYPTO_ID_MAP.get(code, code.lower())
            for code in self.CRYPTO_CURRENCIES
        ]
        ids_param = ",".join(crypto_ids)
        return f"{self.COINGECKO_URL}?ids={ids_param}&vs_currencies=usd"

    def get_rates_file_path(self) -> Path:
        """
        Получить абсолютный путь к файлу rates.json.

        Returns:
            Путь к файлу rates.json
        """
        # Определяем корень проекта (4 уровня вверх от parser_service/config.py)
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / self.RATES_FILE_PATH

    def get_history_file_path(self) -> Path:
        """
        Получить абсолютный путь к файлу exchange_rates.json.

        Returns:
            Путь к файлу exchange_rates.json
        """
        # Определяем корень проекта (4 уровня вверх от parser_service/config.py)
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / self.HISTORY_FILE_PATH
