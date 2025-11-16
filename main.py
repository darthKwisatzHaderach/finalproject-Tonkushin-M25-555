"""Точка входа в приложение."""

import sys

from valutatrade_hub.cli.interface import main as cli_main


def main() -> None:
    """Главная функция приложения."""
    sys.exit(cli_main())


if __name__ == "__main__":
    main()

