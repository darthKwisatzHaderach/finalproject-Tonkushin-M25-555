"""Пользовательские исключения для обработки ошибок."""


class InsufficientFundsError(ValueError):
    """Исключение для случая недостаточности средств."""

    def __init__(self, available: float, required: float, code: str) -> None:
        """
        Инициализация исключения.

        Args:
            available: Доступный баланс
            required: Требуемая сумма
            code: Код валюты
        """
        self.available = available
        self.required = required
        self.code = code

        # Форматируем числа в зависимости от типа валюты
        if code in ("BTC", "ETH"):
            available_str = f"{available:.4f}"
            required_str = f"{required:.4f}"
        else:
            available_str = f"{available:.2f}"
            required_str = f"{required:.2f}"

        message = (
            f"Недостаточно средств: доступно {available_str} {code}, "
            f"требуется {required_str} {code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(ValueError):
    """Исключение для случая, когда валюта не найдена."""

    def __init__(self, code: str) -> None:
        """
        Инициализация исключения.

        Args:
            code: Код валюты, которая не найдена
        """
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(RuntimeError):
    """Исключение для случая сбоя внешнего API."""

    def __init__(self, reason: str) -> None:
        """
        Инициализация исключения.

        Args:
            reason: Причина ошибки
        """
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)

