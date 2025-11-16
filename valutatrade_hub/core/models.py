"""Модели данных для валютного кошелька."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        """
        Инициализация пользователя.

        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            hashed_password: Пароль в зашифрованном виде
            salt: Уникальная соль для пользователя
            registration_date: Дата регистрации пользователя
        """
        self._user_id = user_id
        self.username = username  # Используем сеттер для валидации
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        """Получить идентификатор пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Получить имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        """
        Установить имя пользователя.

        Args:
            value: Новое имя пользователя

        Raises:
            ValueError: Если имя пустое
        """
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        """Получить хешированный пароль."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Получить соль."""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Получить дату регистрации."""
        return self._registration_date

    def get_user_info(self) -> dict:
        """
        Получить информацию о пользователе (без пароля).

        Returns:
            Словарь с информацией о пользователе
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        """
        Изменить пароль пользователя с хешированием.

        Args:
            new_password: Новый пароль

        Raises:
            ValueError: Если пароль короче 4 символов
        """
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        # Генерируем новую соль для нового пароля
        self._salt = secrets.token_hex(8)
        # Хешируем пароль с солью
        password_with_salt = new_password + self._salt
        self._hashed_password = hashlib.sha256(
            password_with_salt.encode("utf-8")
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        """
        Проверить введённый пароль на совпадение.

        Args:
            password: Пароль для проверки

        Returns:
            True если пароль совпадает, иначе False
        """
        password_with_salt = password + self._salt
        hashed_input = hashlib.sha256(
            password_with_salt.encode("utf-8")
        ).hexdigest()
        return hashed_input == self._hashed_password

class Wallet:
    """Класс кошелька пользователя для одной конкретной валюты."""

    def __init__(
        self,
        currency_code: str,
        balance: float = 0.0,
    ) -> None:
        """
        Инициализация кошелька.

        Args:
            currency_code: Код валюты (например, "USD", "BTC")
            balance: Баланс в данной валюте (по умолчанию 0.0)

        Raises:
            ValueError: Если код валюты пустой
        """
        if not currency_code or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")
        self._currency_code = currency_code.strip().upper()
        self.balance = balance  # Используем сеттер для валидации

    @property
    def currency_code(self) -> str:
        """Получить код валюты."""
        return self._currency_code

    @property
    def balance(self) -> float:
        """Получить текущий баланс."""
        return self._balance

    @balance.setter
    def balance(self, new_balance: float) -> None:
        """
        Установить баланс.

        Args:
            new_balance: Новый баланс

        Raises:
            TypeError: Если баланс не является числом
            ValueError: Если баланс отрицательный
        """
        if not isinstance(new_balance, (int, float)):
            raise TypeError("Баланс должен быть числом (int или float)")

        if new_balance < 0:
            raise ValueError("Баланс не может быть меньше 0")

        self._balance = float(new_balance)

    def deposit(self, amount: float) -> None:
        """
        Пополнить баланс.

        Args:
            amount: Сумма для пополнения

        Raises:
            TypeError: Если сумма не является числом
            ValueError: Если сумма не положительная
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом (int или float)")

        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        """
        Снять средства с кошелька.

        Args:
            amount: Сумма для снятия

        Raises:
            TypeError: Если сумма не является числом
            ValueError: Если сумма не положительная или превышает баланс
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом (int или float)")

        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        if amount > self._balance:
            raise ValueError("Сумма снятия не должна превышать баланс")

        self._balance -= float(amount)

    def get_balance_info(self) -> dict:
        """
        Получить информацию о текущем балансе.

        Returns:
            Словарь с информацией о балансе
        """
        return {
            "currency_code": self._currency_code,
            "balance": self._balance,
        }


class Portfolio:
    """Класс управления всеми кошельками одного пользователя."""

    def __init__(
        self,
        user_id: int,
        wallets: dict[str, Wallet] | None = None,
        user: User | None = None,
    ) -> None:
        """
        Инициализация портфеля.

        Args:
            user_id: Уникальный идентификатор пользователя
            wallets: Словарь кошельков (ключ - код валюты, значение - Wallet)
            user: Объект пользователя (опционально)
        """
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = wallets.copy() if wallets else {}
        self._user = user

    @property
    def user_id(self) -> int:
        """Получить идентификатор пользователя."""
        return self._user_id

    @property
    def user(self) -> User | None:
        """
        Получить объект пользователя.

        Returns:
            Объект User или None, если не установлен
        """
        return self._user

    @property
    def wallets(self) -> dict[str, Wallet]:
        """
        Получить копию словаря кошельков.

        Returns:
            Копия словаря кошельков
        """
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавить новый кошелёк в портфель.

        Args:
            currency_code: Код валюты для добавления

        Returns:
            Созданный объект Wallet

        Raises:
            ValueError: Если валюта уже существует в портфеле
        """
        currency_code = currency_code.strip().upper()
        if currency_code in self._wallets:
            raise ValueError(
                f"Валюта {currency_code} уже существует в портфеле"
            )

        wallet = Wallet(currency_code, balance=0.0)
        self._wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """
        Получить кошелёк по коду валюты.

        Args:
            currency_code: Код валюты

        Returns:
            Объект Wallet или None, если кошелёк не найден
        """
        currency_code = currency_code.strip().upper()
        return self._wallets.get(currency_code)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """
        Получить общую стоимость всех валют в базовой валюте.

        Args:
            base_currency: Базовая валюта для конвертации (по умолчанию USD)

        Returns:
            Общая стоимость в базовой валюте

        Raises:
            ValueError: Если базовая валюта не найдена в курсах
        """
        # Фиксированные курсы обмена (для упрощения)
        # Курсы указаны относительно USD (1 USD = 1 USD, 1 EUR = 1.1 USD, и т.д.)
        exchange_rates: dict[str, float] = {
            "USD": 1.0,
            "EUR": 1.1,
            "BTC": 45000.0,
            "ETH": 3000.0,
            "RUB": 0.011,
        }

        base_currency = base_currency.strip().upper()
        if base_currency not in exchange_rates:
            raise ValueError(
                f"Курс для базовой валюты {base_currency} не найден"
            )

        total_value = 0.0

        for currency_code, wallet in self._wallets.items():
            currency_code = currency_code.upper()
            balance = wallet.balance

            # Если валюта кошелька совпадает с базовой, просто добавляем баланс
            if currency_code == base_currency:
                total_value += balance
            else:
                # Конвертируем в USD сначала
                if currency_code in exchange_rates:
                    # Баланс в валюте кошелька * курс к USD
                    value_in_usd = balance * exchange_rates[currency_code]
                    # Конвертируем из USD в базовую валюту
                    if base_currency == "USD":
                        total_value += value_in_usd
                    else:
                        # Конвертируем из USD в базовую валюту
                        total_value += value_in_usd / exchange_rates[
                            base_currency
                        ]
                else:
                    # Если курс не найден, пропускаем эту валюту
                    # (или можно выбросить исключение)
                    continue

        return total_value
