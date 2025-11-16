"""Команды CLI интерфейса."""

import argparse
import sys

from valutatrade_hub.core.usecases import register_user


def cmd_register(args: argparse.Namespace) -> int:
    """
    Обработка команды register.

    Args:
        args: Аргументы команды

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    try:
        user, user_id = register_user(args.username, args.password)
        print(
            f"Пользователь '{user.username}' зарегистрирован (id={user_id}). "
            f"Войдите: login --username {user.username} --password ****"
        )
        return 0
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Ошибка регистрации: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Создать парсер аргументов командной строки.

    Returns:
        Настроенный ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Валютный кошелек - консольное приложение"
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Команда register
    register_parser = subparsers.add_parser(
        "register", help="Зарегистрировать нового пользователя"
    )
    register_parser.add_argument(
        "--username",
        type=str,
        required=True,
        help="Имя пользователя (обязательно, уникально)",
    )
    register_parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="Пароль (обязательно, минимум 4 символа)",
    )

    return parser


def main() -> int:
    """
    Главная функция CLI.

    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Маршрутизация команд
    if args.command == "register":
        return cmd_register(args)

    print(f"Неизвестная команда: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
