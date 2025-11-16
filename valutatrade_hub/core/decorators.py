"""Декораторы для логирования и других целей."""

from __future__ import annotations

import functools
from collections.abc import Callable
from datetime import datetime
from typing import Any

from valutatrade_hub.core.logging_config import get_logger

# Логгер для действий
_action_logger = get_logger("actions")


def log_action(action: str, verbose: bool = False) -> Callable:
    """
    Декоратор для логирования доменных операций.

    Args:
        action: Название действия (BUY, SELL, REGISTER, LOGIN и т.д.)
        verbose: Если True, добавляет дополнительный контекст в лог

    Returns:
        Декорированная функция

    Пример:
        @log_action("BUY", verbose=True)
        def buy_currency(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Подготавливаем данные для логирования
            log_data: dict[str, Any] = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
            }

            # Извлекаем информацию из аргументов функции
            # Для buy_currency и sell_currency: currency, amount, base_currency
            # Для register_user и login_user: username, password
            try:
                # Пытаемся извлечь username/user_id из глобального состояния
                # или из аргументов
                from valutatrade_hub.core.usecases import get_current_user

                current_user = get_current_user()
                if current_user:
                    log_data["username"] = current_user.username
                    log_data["user_id"] = current_user.user_id
                else:
                    # Если пользователь не залогинен, пытаемся получить из args
                    if args and len(args) > 0:
                        # Для register_user и login_user первый аргумент - username
                        if action in ("REGISTER", "LOGIN"):
                            log_data["username"] = args[0] if args else "unknown"
            except Exception:
                pass

            # Извлекаем параметры операции
            if action in ("BUY", "SELL"):
                # Ищем currency, amount, base_currency в kwargs или args
                if "currency" in kwargs:
                    log_data["currency_code"] = kwargs["currency"]
                elif len(args) > 0:
                    log_data["currency_code"] = args[0]

                if "amount" in kwargs:
                    log_data["amount"] = kwargs["amount"]
                elif len(args) > 1:
                    log_data["amount"] = args[1]

                if "base_currency" in kwargs:
                    log_data["base"] = kwargs["base_currency"]
                elif len(args) > 2:
                    log_data["base"] = args[2]

            # Выполняем функцию и логируем результат
            result = "OK"
            error_type = None
            error_message = None

            try:
                func_result = func(*args, **kwargs)
                log_data["result"] = result

                # Если verbose и это операция с валютой, добавляем контекст
                if verbose and action in ("BUY", "SELL") and func_result:
                    if isinstance(func_result, dict):
                        # Добавляем информацию о балансе "было→стало"
                        if "old_balance" in func_result:
                            log_data["old_balance"] = func_result["old_balance"]
                        if "new_balance" in func_result:
                            log_data["new_balance"] = func_result["new_balance"]
                        if "rate" in func_result:
                            log_data["rate"] = func_result["rate"]

                return func_result

            except Exception as e:
                result = "ERROR"
                error_type = type(e).__name__
                error_message = str(e)

                log_data["result"] = result
                log_data["error_type"] = error_type
                log_data["error_message"] = error_message

                # Пробрасываем исключение дальше (не глотаем)
                raise

            finally:
                # Формируем строку лога
                log_parts = [
                    log_data["action"],
                    f"user='{log_data.get('username', 'unknown')}'",
                ]

                if "currency_code" in log_data:
                    currency = log_data["currency_code"]
                    amount = log_data.get("amount", 0)
                    # Форматируем amount в зависимости от валюты
                    if currency in ("BTC", "ETH"):
                        amount_str = f"{amount:.4f}"
                    else:
                        amount_str = f"{amount:.2f}"
                    log_parts.append(f"currency='{currency}' amount={amount_str}")

                if "rate" in log_data:
                    rate = log_data["rate"]
                    log_parts.append(f"rate={rate:.2f}")

                if "base" in log_data:
                    log_parts.append(f"base='{log_data['base']}'")

                if verbose and "old_balance" in log_data:
                    old_bal = log_data["old_balance"]
                    new_bal = log_data["new_balance"]
                    currency = log_data.get("currency_code", "")
                    if currency in ("BTC", "ETH"):
                        old_str = f"{old_bal:.4f}"
                        new_str = f"{new_bal:.4f}"
                    else:
                        old_str = f"{old_bal:.2f}"
                        new_str = f"{new_bal:.2f}"
                    log_parts.append(
                        f"balance={old_str}→{new_str} {currency}"
                    )

                log_parts.append(f"result={log_data['result']}")

                if error_type:
                    log_parts.append(f"error_type='{error_type}'")
                if error_message:
                    # Ограничиваем длину сообщения об ошибке
                    error_msg_short = (
                        error_message[:100] + "..."
                        if len(error_message) > 100
                        else error_message
                    )
                    log_parts.append(f"error_message='{error_msg_short}'")

                # Логируем на уровне INFO
                log_message = " ".join(log_parts)
                _action_logger.info(log_message)

        return wrapper

    return decorator

