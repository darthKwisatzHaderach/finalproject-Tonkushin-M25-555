"""Модели данных для валютного кошелька."""

from __future__ import annotations

import hashlib
import secrets
from abc import ABC, abstractmethod
from datetime import datetime

from valutatrade_hub.core.exceptions import InsufficientFundsError


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
        return self._user_id

    @property
    def username(self) -> str:
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
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
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

        self._salt = secrets.token_hex(8)
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
            ValueError: Если сумма не положительная
            InsufficientFundsError: Если недостаточно средств
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом (int или float)")

        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        if amount > self._balance:
            raise InsufficientFundsError(
                self._balance, amount, self._currency_code
            )

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
        return self._user_id

    @property
    def user(self) -> User | None:
        return self._user

    @property
    def wallets(self) -> dict[str, Wallet]:
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
        # TODO: получать курсы из rates.json вместо хардкода
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

            if currency_code == base_currency:
                total_value += balance
            else:
                if currency_code in exchange_rates:
                    value_in_usd = balance * exchange_rates[currency_code]
                    if base_currency == "USD":
                        total_value += value_in_usd
                    else:
                        total_value += value_in_usd / exchange_rates[base_currency]
                else:
                    # Пропускаем валюту без курса
                    continue

        return total_value


class Currency(ABC):
    """Абстрактный базовый класс для валют."""

    def __init__(self, name: str, code: str) -> None:
        """
        Инициализация валюты.

        Args:
            name: Человекочитаемое имя валюты
            code: ISO-код или тикер валюты

        Raises:
            ValueError: Если валидация не прошла
        """
        self.name = name
        self.code = code

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """
        Установить имя валюты.

        Args:
            value: Имя валюты

        Raises:
            ValueError: Если имя пустое
        """
        if not value or not value.strip():
            raise ValueError("Имя валюты не может быть пустым")
        self._name = value.strip()

    @property
    def code(self) -> str:
        return self._code

    @code.setter
    def code(self, value: str) -> None:
        """
        Установить код валюты.

        Args:
            value: Код валюты

        Raises:
            ValueError: Если код не соответствует требованиям
        """
        if not isinstance(value, str):
            raise TypeError("Код валюты должен быть строкой")

        value = value.strip().upper()

        if not value:
            raise ValueError("Код валюты не может быть пустым")

        if len(value) < 2 or len(value) > 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")

        if " " in value:
            raise ValueError("Код валюты не может содержать пробелы")

        self._code = value

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Получить строковое представление для UI/логов.

        Returns:
            Строковое представление валюты
        """
        pass


class FiatCurrency(Currency):
    """Класс фиатной валюты."""

    def __init__(self, name: str, code: str, issuing_country: str) -> None:
        """
        Инициализация фиатной валюты.

        Args:
            name: Человекочитаемое имя валюты
            code: ISO-код валюты
            issuing_country: Страна или зона эмиссии

        Raises:
            ValueError: Если валидация не прошла
        """
        super().__init__(name, code)
        self.issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        """Получить страну/зону эмиссии."""
        return self._issuing_country

    @issuing_country.setter
    def issuing_country(self, value: str) -> None:
        """
        Установить страну/зону эмиссии.

        Args:
            value: Страна или зона эмиссии

        Raises:
            ValueError: Если значение пустое
        """
        if not value or not value.strip():
            raise ValueError("Страна/зона эмиссии не может быть пустой")
        self._issuing_country = value.strip()

    def get_display_info(self) -> str:
        """
        Получить строковое представление фиатной валюты.

        Returns:
            Строковое представление в формате:
            "[FIAT] CODE — Name (Issuing: Country)"
        """
        return (
            f"[FIAT] {self._code} — {self._name} "
            f"(Issuing: {self._issuing_country})"
        )


class CryptoCurrency(Currency):
    """Класс криптовалюты."""

    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ) -> None:
        """
        Инициализация криптовалюты.

        Args:
            name: Человекочитаемое имя валюты
            code: Тикер криптовалюты
            algorithm: Алгоритм консенсуса/майнинга
            market_cap: Рыночная капитализация

        Raises:
            ValueError: Если валидация не прошла
        """
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    @property
    def algorithm(self) -> str:
        """Получить алгоритм."""
        return self._algorithm

    @algorithm.setter
    def algorithm(self, value: str) -> None:
        """
        Установить алгоритм.

        Args:
            value: Алгоритм консенсуса/майнинга

        Raises:
            ValueError: Если значение пустое
        """
        if not value or not value.strip():
            raise ValueError("Алгоритм не может быть пустым")
        self._algorithm = value.strip()

    @property
    def market_cap(self) -> float:
        """Получить рыночную капитализацию."""
        return self._market_cap

    @market_cap.setter
    def market_cap(self, value: float) -> None:
        """
        Установить рыночную капитализацию.

        Args:
            value: Рыночная капитализация

        Raises:
            TypeError: Если значение не является числом
            ValueError: Если значение отрицательное
        """
        if not isinstance(value, (int, float)):
            raise TypeError("Рыночная капитализация должна быть числом")
        if value < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        self._market_cap = float(value)

    def get_display_info(self) -> str:
        """
        Получить строковое представление криптовалюты.

        Returns:
            Строковое представление в формате:
            "[CRYPTO] CODE — Name (Algo: Algorithm, MCAP: MarketCap)"
        """
        # Форматируем капитализацию в научной нотации для больших чисел
        if self._market_cap >= 1e12:
            mcap_str = f"{self._market_cap / 1e12:.2f}e12"
        elif self._market_cap >= 1e9:
            mcap_str = f"{self._market_cap / 1e9:.2f}e9"
        elif self._market_cap >= 1e6:
            mcap_str = f"{self._market_cap / 1e6:.2f}e6"
        else:
            mcap_str = f"{self._market_cap:.2f}"

        return (
            f"[CRYPTO] {self._code} — {self._name} "
            f"(Algo: {self._algorithm}, MCAP: {mcap_str})"
        )
