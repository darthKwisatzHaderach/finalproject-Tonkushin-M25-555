"""Менеджер базы данных (Singleton) - абстракция над JSON-хранилищем."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader

_settings = SettingsLoader()


class DatabaseManager:
    """
    Менеджер базы данных (Singleton).

    Абстракция над JSON-хранилищем для безопасной работы с данными.
    Реализация через __new__ выбрана для простоты и читабельности.
    """

    _instance: DatabaseManager | None = None
    _data_dir: Path | None = None

    def __new__(cls) -> DatabaseManager:
        """
        Создать или вернуть существующий экземпляр Singleton.

        Returns:
            Единственный экземпляр DatabaseManager
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Инициализировать менеджер базы данных."""
        data_dir_str = _settings.get("data_dir", "data")
        self._data_dir = Path(data_dir_str)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def load(self, filename: str) -> Any:
        """
        Загрузить данные из JSON файла.

        Args:
            filename: Имя файла (например, "users.json")

        Returns:
            Данные из файла (dict, list и т.д.)

        Raises:
            FileNotFoundError: Если файл не найден
            json.JSONDecodeError: Если файл содержит некорректный JSON
        """
        if self._data_dir is None:
            self._initialize()

        file_path = self._data_dir / filename

        if not file_path.exists():
            # Создаём файл с пустыми данными
            if "users" in filename or "portfolios" in filename:
                default_data: Any = []
            else:
                default_data = {}
            self.save(filename, default_data)
            return default_data

        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def save(self, filename: str, data: Any) -> None:
        """
        Сохранить данные в JSON файл.

        Args:
            filename: Имя файла (например, "users.json")
            data: Данные для сохранения
        """
        if self._data_dir is None:
            self._initialize()

        file_path = self._data_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_data_dir(self) -> Path:
        """
        Получить путь к директории с данными.

        Returns:
            Путь к директории с данными
        """
        if self._data_dir is None:
            self._initialize()
        return self._data_dir

