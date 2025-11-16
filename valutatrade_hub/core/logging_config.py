"""Конфигурация логирования для приложения."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.core.settings import SettingsLoader

# Получаем экземпляр SettingsLoader (Singleton)
_settings = SettingsLoader()


def setup_logging() -> None:
    """
    Настроить логирование для приложения.

    Создаёт логгер с ротацией файлов и настраивает формат.
    """
    # Получаем настройки из конфигурации
    log_file = _settings.get("log_file", "logs/app.log")
    log_level_str = _settings.get("log_level", "INFO").upper()

    # Преобразуем строку уровня в константу logging
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Создаём директорию для логов, если её нет
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Удаляем существующие обработчики, чтобы избежать дублирования
    root_logger.handlers.clear()

    # Формат логов (человекочитаемый)
    formatter = logging.Formatter(
        fmt="%(levelname)s %(asctime)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Обработчик для файла с ротацией
    # Максимальный размер файла: 10MB, количество резервных файлов: 5
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Обработчик для консоли (опционально, для отладки)
    # В production можно отключить
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)  # Только WARNING и выше в консоль
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер с указанным именем.

    Args:
        name: Имя логгера (обычно __name__ модуля)

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)

