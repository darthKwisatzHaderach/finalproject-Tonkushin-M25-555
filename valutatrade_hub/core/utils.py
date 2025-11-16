"""Вспомогательные функции."""

import json
from pathlib import Path
from typing import Any

# Пути к файлам данных
DATA_DIR = Path(__file__).parent.parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"


def load_json(file_path: Path) -> Any:
    """
    Загрузить данные из JSON файла.

    Args:
        file_path: Путь к JSON файлу

    Returns:
        Данные из файла (dict, list и т.д.)

    Raises:
        FileNotFoundError: Если файл не найден
        json.JSONDecodeError: Если файл содержит некорректный JSON
    """
    if not file_path.exists():
        # Создаём файл с пустыми данными
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if "users" in str(file_path):
            default_data: Any = []
        else:
            default_data = {}
        save_json(file_path, default_data)
        return default_data

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def save_json(file_path: Path, data: Any) -> None:
    """
    Сохранить данные в JSON файл.

    Args:
        file_path: Путь к JSON файлу
        data: Данные для сохранения
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def validate_amount(amount: Any) -> float:
    """
    Валидировать сумму.

    Args:
        amount: Значение для валидации

    Returns:
        Валидная сумма как float

    Raises:
        TypeError: Если значение не является числом
        ValueError: Если сумма <= 0
    """
    if not isinstance(amount, (int, float)):
        raise TypeError("Сумма должна быть числом")

    amount_float = float(amount)
    if amount_float <= 0:
        raise ValueError("Сумма должна быть положительным числом")

    return amount_float


def validate_currency_code(currency_code: Any) -> str:
    """
    Валидировать код валюты.

    Args:
        currency_code: Значение для валидации

    Returns:
        Валидный код валюты в верхнем регистре

    Raises:
        TypeError: Если значение не является строкой
        ValueError: Если код валюты пустой
    """
    if not isinstance(currency_code, str):
        raise TypeError("Код валюты должен быть строкой")

    currency_code = currency_code.strip().upper()
    if not currency_code:
        raise ValueError("Код валюты не может быть пустым")

    return currency_code


def get_exchange_rate(
    from_currency: str, to_currency: str, rates_data: dict | None = None
) -> float:
    """
    Получить курс обмена между валютами.

    Args:
        from_currency: Исходная валюта
        to_currency: Целевая валюта
        rates_data: Данные курсов (если None, загружаются из файла)

    Returns:
        Курс обмена (сколько единиц to_currency за 1 единицу from_currency)

    Raises:
        ValueError: Если курс не найден
    """
    if rates_data is None:
        rates_data = load_json(RATES_FILE)

    from_currency = validate_currency_code(from_currency)
    to_currency = validate_currency_code(to_currency)

    # Если валюты одинаковые, курс = 1
    if from_currency == to_currency:
        return 1.0

    # Пытаемся найти прямой курс
    rate_key = f"{from_currency}_{to_currency}"
    if rate_key in rates_data and "rate" in rates_data[rate_key]:
        return float(rates_data[rate_key]["rate"])

    # Пытаемся найти обратный курс
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in rates_data and "rate" in rates_data[reverse_key]:
        return 1.0 / float(rates_data[reverse_key]["rate"])

    # Если не нашли, используем фиксированные курсы (заглушка)
    fallback_rates: dict[str, float] = {
        "USD": 1.0,
        "EUR": 1.1,
        "BTC": 45000.0,
        "ETH": 3000.0,
        "RUB": 0.011,
    }

    # Конвертируем через USD
    if from_currency in fallback_rates and to_currency in fallback_rates:
        # Сначала в USD, потом в целевую валюту
        from_to_usd = fallback_rates[from_currency]
        usd_to_to = 1.0 / fallback_rates[to_currency]
        return from_to_usd * usd_to_to

    raise ValueError(
        f"Курс обмена {from_currency} -> {to_currency} не найден"
    )
