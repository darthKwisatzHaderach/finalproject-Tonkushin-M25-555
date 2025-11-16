"""Загрузчик конфигурации (Singleton)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Для Python < 3.11


class SettingsLoader:
    """Загрузчик конфигурации (Singleton)."""

    _instance: SettingsLoader | None = None
    _config: dict[str, Any] = {}

    def __new__(cls) -> SettingsLoader:
        """
        Создать или вернуть существующий экземпляр Singleton.

        Returns:
            Единственный экземпляр SettingsLoader
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Загрузить конфигурацию из pyproject.toml или config.json."""
        project_root = Path(__file__).parent.parent.parent

        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)
                    self._config = pyproject_data.get("tool", {}).get(
                        "valutatrade", {}
                    )
            except Exception:
                pass

        config_json_path = project_root / "config.json"
        if config_json_path.exists():
            try:
                with open(config_json_path, encoding="utf-8") as f:
                    json_config = json.load(f)
                    self._config.update(json_config)
            except Exception:
                pass

        self._config.setdefault("data_dir", "data")
        self._config.setdefault("rates_ttl_seconds", 300)
        self._config.setdefault("default_base_currency", "USD")
        self._config.setdefault("log_file", "logs/app.log")
        self._config.setdefault("log_level", "INFO")

        if "data_dir" in self._config:
            data_dir = self._config["data_dir"]
            if not Path(data_dir).is_absolute():
                self._config["data_dir"] = str(project_root / data_dir)

        if "log_file" in self._config:
            log_file = self._config["log_file"]
            if not Path(log_file).is_absolute():
                self._config["log_file"] = str(project_root / log_file)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение конфигурации по ключу.

        Args:
            key: Ключ конфигурации
            default: Значение по умолчанию, если ключ не найден

        Returns:
            Значение конфигурации или default
        """
        return self._config.get(key, default)

    def reload(self) -> None:
        """Перезагрузить конфигурацию из файлов."""
        self._config.clear()
        self._load_config()

