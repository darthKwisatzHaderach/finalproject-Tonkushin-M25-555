"""Точка входа в приложение."""

import sys

from valutatrade_hub.cli.interface import main as cli_main
from valutatrade_hub.core.logging_config import setup_logging


def main() -> None:
    """Главная функция приложения."""
    # Инициализируем логирование при старте приложения
    setup_logging()
    sys.exit(cli_main())


if __name__ == "__main__":
    main()

