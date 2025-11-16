"""Основной модуль обновления курсов."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import get_logger
from valutatrade_hub.parser_service.api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage

# Логгер для обновления курсов
_logger = get_logger("parser_service.updater")


class RatesUpdater:
    """Класс для координации процесса обновления курсов."""

    def __init__(
        self,
        config: ParserConfig,
        storage: RatesStorage | None = None,
        clients: list[BaseApiClient] | None = None,
    ) -> None:
        """
        Инициализация обновлятеля курсов.

        Args:
            config: Конфигурация парсера
            storage: Хранилище для сохранения данных
                     (если None, создаётся автоматически)
            clients: Список API-клиентов
                     (если None, создаются автоматически)
        """
        self.config = config
        self.storage = storage or RatesStorage(config)

        # Создаём клиенты, если не переданы
        if clients is None:
            self.clients: list[BaseApiClient] = [
                CoinGeckoClient(config),
                ExchangeRateApiClient(config),
            ]
        else:
            self.clients = clients

    def run_update(self) -> dict[str, Any]:
        """
        Запустить процесс обновления курсов.

        Returns:
            Словарь с результатами обновления:
            {
                "success": bool,
                "total_pairs": int,
                "sources": dict,
                "errors": list
            }

        Raises:
            ApiRequestError: Если все клиенты не смогли получить данные
        """
        _logger.info("Начало обновления курсов валют")

        all_rates: dict[str, float] = {}
        all_sources: dict[str, str] = {}
        errors: list[str] = []

        # Опрашиваем каждого клиента
        for client in self.clients:
            client_name = client.__class__.__name__
            _logger.info(f"Запрос курсов от {client_name}")

            try:
                rates = client.fetch_rates()
                _logger.info(
                    f"{client_name}: получено {len(rates)} курсов"
                )

                # Определяем источник
                if isinstance(client, CoinGeckoClient):
                    source = "CoinGecko"
                elif isinstance(client, ExchangeRateApiClient):
                    source = "ExchangeRate-API"
                else:
                    source = client_name

                # Объединяем курсы
                for pair_key, rate in rates.items():
                    all_rates[pair_key] = rate
                    all_sources[pair_key] = source

                    # Сохраняем в историю
                    from_currency, to_currency = pair_key.split("_", 1)
                    self.storage.save_rate_to_history(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate,
                        source=source,
                        meta={
                            "client": client_name,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

            except ApiRequestError as e:
                error_msg = f"{client_name}: {e}"
                _logger.error(error_msg)
                errors.append(error_msg)
                # Продолжаем работу с другими клиентами
                continue
            except Exception as e:
                error_msg = f"{client_name}: Неожиданная ошибка - {e}"
                _logger.exception(error_msg)
                errors.append(error_msg)
                continue

        # Проверяем, получили ли мы хотя бы какие-то данные
        if not all_rates:
            error_msg = "Не удалось получить курсы ни от одного источника"
            _logger.error(error_msg)
            raise ApiRequestError(error_msg)

        # Обновляем кэш
        _logger.info(f"Обновление кэша: {len(all_rates)} пар валют")
        self.storage.update_rates_cache(all_rates, all_sources)

        result = {
            "success": len(errors) == 0 or len(all_rates) > 0,
            "total_pairs": len(all_rates),
            "sources": all_sources,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        _logger.info(
            f"Обновление завершено: {len(all_rates)} пар, "
            f"ошибок: {len(errors)}"
        )

        return result
