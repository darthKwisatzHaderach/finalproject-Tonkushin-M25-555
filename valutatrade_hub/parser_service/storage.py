"""Операции чтения/записи exchange_rates.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    """Хранилище для работы с файлами курсов."""

    def __init__(self, config: ParserConfig) -> None:
        """
        Инициализация хранилища.

        Args:
            config: Конфигурация парсера
        """
        self.config = config
        self.rates_file = config.get_rates_file_path()
        self.history_file = config.get_history_file_path()

    def save_rate_to_history(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        source: str,
        meta: dict[str, Any] | None = None,
    ) -> str:
        """
        Сохранить курс в историю (exchange_rates.json).

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            rate: Курс обмена
            source: Источник данных (CoinGecko, ExchangeRate-API)
            meta: Дополнительные метаданные

        Returns:
            ID созданной записи
        """
        # Генерируем уникальный ID
        timestamp = datetime.now(timezone.utc)
        # Форматируем timestamp для ID в формате ISO UTC (Z вместо +00:00)
        timestamp_id = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        record_id = f"{from_currency}_{to_currency}_{timestamp_id}"

        # Создаём запись
        record = {
            "id": record_id,
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "rate": float(rate),
            "timestamp": timestamp.isoformat(),
            "source": source,
            "meta": meta or {},
        }

        # Загружаем существующую историю
        history_data = self._load_history()

        # Добавляем новую запись
        if "records" not in history_data:
            history_data["records"] = []
        history_data["records"].append(record)
        history_data["last_update"] = timestamp.isoformat()

        # Сохраняем атомарно (через временный файл)
        self._save_history_atomic(history_data)

        return record_id

    def update_rates_cache(
        self, rates: dict[str, float], sources: dict[str, str]
    ) -> None:
        """
        Обновить кэш курсов (rates.json).

        Args:
            rates: Словарь с курсами {CURRENCY_BASE: rate, ...}
            sources: Словарь с источниками {CURRENCY_BASE: source, ...}
        """
        # Загружаем существующий кэш
        cache_data = self._load_rates_cache()

        # Обновляем пары
        if "pairs" not in cache_data:
            cache_data["pairs"] = {}

        timestamp = datetime.now(timezone.utc).isoformat()

        for pair_key, rate in rates.items():
            # Проверяем, нужно ли обновлять (если запись свежее, обновляем)
            existing = cache_data["pairs"].get(pair_key, {})
            existing_timestamp = existing.get("updated_at")

            # Обновляем, если записи нет или новая запись свежее
            should_update = True
            if existing_timestamp:
                try:
                    existing_dt = datetime.fromisoformat(
                        existing_timestamp.replace("Z", "+00:00")
                    )
                    new_dt = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )
                    if existing_dt >= new_dt:
                        should_update = False
                except (ValueError, TypeError):
                    pass

            if should_update:
                cache_data["pairs"][pair_key] = {
                    "rate": float(rate),
                    "updated_at": timestamp,
                    "source": sources.get(pair_key, "Unknown"),
                }

        cache_data["last_refresh"] = timestamp

        # Сохраняем атомарно
        self._save_rates_cache_atomic(cache_data)

    def _load_history(self) -> dict[str, Any]:
        """
        Загрузить историю из exchange_rates.json.

        Returns:
            Данные истории
        """
        if not self.history_file.exists():
            return {
                "source": "ParserService",
                "last_update": None,
                "records": [],
            }

        try:
            with open(self.history_file, encoding="utf-8") as f:
                data = json.load(f)
                # Обеспечиваем наличие списка records
                if "records" not in data:
                    data["records"] = []
                return data
        except (json.JSONDecodeError, OSError):
            return {
                "source": "ParserService",
                "last_update": None,
                "records": [],
            }

    def _save_history_atomic(self, data: dict[str, Any]) -> None:
        """
        Сохранить историю атомарно (через временный файл).

        Args:
            data: Данные для сохранения
        """
        # Создаём временный файл
        temp_file = self.history_file.with_suffix(".tmp")

        try:
            # Записываем во временный файл
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Атомарно переименовываем
            temp_file.replace(self.history_file)
        except Exception:
            # Если что-то пошло не так, удаляем временный файл
            if temp_file.exists():
                temp_file.unlink()
            raise

    def _load_rates_cache(self) -> dict[str, Any]:
        """
        Загрузить кэш курсов из rates.json.

        Returns:
            Данные кэша
        """
        if not self.rates_file.exists():
            return {
                "pairs": {},
                "last_refresh": None,
            }

        try:
            with open(self.rates_file, encoding="utf-8") as f:
                data = json.load(f)
                # Обеспечиваем наличие словаря pairs
                if "pairs" not in data:
                    data["pairs"] = {}
                return data
        except (json.JSONDecodeError, OSError):
            return {
                "pairs": {},
                "last_refresh": None,
            }

    def _save_rates_cache_atomic(self, data: dict[str, Any]) -> None:
        """
        Сохранить кэш курсов атомарно (через временный файл).

        Args:
            data: Данные для сохранения
        """
        # Создаём временный файл
        temp_file = self.rates_file.with_suffix(".tmp")

        try:
            # Записываем во временный файл
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Атомарно переименовываем
            temp_file.replace(self.rates_file)
        except Exception:
            # Если что-то пошло не так, удаляем временный файл
            if temp_file.exists():
                temp_file.unlink()
            raise
