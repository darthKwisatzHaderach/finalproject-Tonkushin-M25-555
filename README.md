# ValutaTrade Hub

Консольное приложение для управления валютным кошельком с поддержкой криптовалют и фиатных валют.

## Демонстрация

Интерактивная демонстрация работы приложения:

[![asciicast](https://asciinema.org/a/w7OgWNB3UCpTyNPSmbaMGho0g.svg)](https://asciinema.org/a/w7OgWNB3UCpTyNPSmbaMGho0g)

[Смотреть полную демонстрацию на asciinema.org](https://asciinema.org/a/w7OgWNB3UCpTyNPSmbaMGho0g)

## Описание

ValutaTrade Hub позволяет пользователям:
- Регистрироваться и входить в систему
- Управлять портфелем валют (криптовалюты и фиатные валюты)
- Покупать и продавать валюты
- Просматривать актуальные курсы обмена
- Автоматически обновлять курсы из внешних источников (CoinGecko, ExchangeRate-API)

## Структура проекта

```
finalproject_Tonkushin_M25-555/
├── valutatrade_hub/          # Основной пакет
│   ├── core/                 # Бизнес-логика
│   │   ├── models.py         # Модели данных (User, Wallet, Portfolio, Currency)
│   │   ├── usecases.py       # Бизнес-логика (register, login, buy, sell, get_rate)
│   │   ├── utils.py          # Вспомогательные функции
│   │   ├── exceptions.py     # Пользовательские исключения
│   │   └── currencies.py     # Иерархия валют и регистр
│   ├── cli/                  # Командный интерфейс
│   │   └── interface.py      # CLI команды
│   ├── infra/                # Инфраструктура
│   │   ├── settings.py       # Загрузчик конфигурации (Singleton)
│   │   └── database.py       # Менеджер базы данных (Singleton)
│   ├── parser_service/       # Сервис парсинга курсов
│   │   ├── config.py         # Конфигурация API
│   │   ├── api_clients.py    # Клиенты для внешних API
│   │   ├── updater.py        # Обновление курсов
│   │   ├── storage.py        # Хранение курсов
│   │   └── scheduler.py      # Планировщик обновлений
│   ├── decorators.py         # Декораторы (логирование)
│   └── logging_config.py     # Конфигурация логирования
├── data/                     # Данные приложения
│   ├── users.json           # Пользователи
│   ├── portfolios.json      # Портфели пользователей
│   ├── rates.json           # Кэш курсов валют
│   └── exchange_rates.json  # История курсов
├── logs/                     # Логи приложения
│   └── app.log              # Основной лог-файл
├── main.py                   # Точка входа
├── pyproject.toml           # Конфигурация Poetry
├── Makefile                  # Автоматизация задач
└── README.md                # Документация
```

## Установка

### Требования

- Python 3.10 или выше
- Poetry (менеджер зависимостей)

### Шаги установки

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd finalproject_Tonkushin_M25-555
```

2. Установите зависимости:
```bash
make install
```

Или напрямую через Poetry:
```bash
poetry install
```

## Запуск

### Основной способ

```bash
make project
```

Или через Poetry:
```bash
poetry run project
```

### Альтернативный способ

```bash
python main.py
```

## Использование

### Основные команды

#### Регистрация пользователя

```bash
poetry run project register --username alice --password secret123
```

#### Вход в систему

```bash
poetry run project login --username alice --password secret123
```

#### Просмотр портфеля

```bash
poetry run project show-portfolio
poetry run project show-portfolio --base EUR
```

#### Покупка валюты

```bash
poetry run project buy --currency BTC --amount 0.001
poetry run project buy --currency EUR --amount 100
```

#### Продажа валюты

```bash
poetry run project sell --currency BTC --amount 0.0005
poetry run project sell --currency EUR --amount 50
```

#### Получение курса обмена

```bash
poetry run project get-rate --from USD --to BTC
poetry run project get-rate --from EUR --to RUB
```

### Команды Parser Service

#### Обновление курсов

Обновить курсы из всех источников:
```bash
poetry run project update-rates
```

Обновить только из CoinGecko:
```bash
poetry run project update-rates --source coingecko
```

Обновить только из ExchangeRate-API:
```bash
poetry run project update-rates --source exchangerate
```

#### Просмотр курсов из кэша

Показать все курсы:
```bash
poetry run project show-rates
```

Показать курс для конкретной валюты:
```bash
poetry run project show-rates --currency BTC
```

Показать топ-2 самых дорогих криптовалют:
```bash
poetry run project show-rates --top 2
```

Показать все курсы относительно EUR:
```bash
poetry run project show-rates --base EUR
```

## Конфигурация

### Настройки в `pyproject.toml`

Основные настройки находятся в секции `[tool.valutatrade]`:

```toml
[tool.valutatrade]
# Путь к директории с данными (относительно корня проекта)
data_dir = "data"

# Время жизни курсов в секундах (TTL)
rates_ttl_seconds = 300

# Дефолтная базовая валюта
default_base_currency = "USD"

# Путь к файлу логов
log_file = "logs/app.log"

# Уровень логирования
log_level = "INFO"
```

### Переопределение через `config.json`

Создайте файл `config.json` в корне проекта для переопределения настроек:

```json
{
  "data_dir": "custom_data",
  "rates_ttl_seconds": 600,
  "default_base_currency": "EUR",
  "log_file": "logs/custom.log",
  "log_level": "DEBUG"
}
```

## Parser Service

### Настройка API-ключей

Для работы с ExchangeRate-API необходимо установить переменную окружения:

```bash
export EXCHANGERATE_API_KEY="your-api-key-here"
```

Или добавить в `~/.bashrc` / `~/.zshrc`:
```bash
echo 'export EXCHANGERATE_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Важно:** Не храните API-ключи в коде или в репозитории!

### Как работает Parser Service

1. **Обновление курсов** (`update-rates`):
   - Запрашивает курсы из CoinGecko (криптовалюты)
   - Запрашивает курсы из ExchangeRate-API (фиатные валюты)
   - Объединяет данные
   - Сохраняет в `data/rates.json` (кэш)
   - Сохраняет в `data/exchange_rates.json` (история)

2. **Кэш курсов** (`rates.json`):
   - Хранит последние актуальные курсы
   - Формат: `{"pairs": {"BTC_USD": {"rate": 59337.21, "updated_at": "...", "source": "CoinGecko"}}, "last_refresh": "..."}`
   - Используется Core Service для быстрого доступа

3. **История курсов** (`exchange_rates.json`):
   - Хранит все измерения курсов
   - Каждая запись имеет уникальный ID: `BTC_USD_2025-10-10T12:00:00Z`
   - Используется для анализа динамики курсов

### TTL (Time To Live) курсов

Курсы в кэше имеют срок годности (TTL), по умолчанию 300 секунд (5 минут).

Если курс устарел:
- Core Service автоматически пытается обновить его
- Если обновление не удалось, пользователь получает сообщение об устаревших данных
- Рекомендуется выполнить `update-rates` для обновления всех курсов

## Обработка ошибок

Приложение обрабатывает следующие типы ошибок:

- **Недостаточно средств** (`InsufficientFundsError`):
  ```
  Ошибка: Недостаточно средств: доступно 0.1000 BTC, требуется 0.2000 BTC
  ```

- **Неизвестная валюта** (`CurrencyNotFoundError`):
  ```
  Ошибка: Неизвестная валюта 'XYZ'
  ```

- **Ошибка API** (`ApiRequestError`):
  ```
  Ошибка: Ошибка при обращении к внешнему API: CoinGecko API вернул статус 429
  ```

- **Пользователь не залогинен** (`RuntimeError`):
  ```
  Сначала выполните login
  ```

## Логирование

Логи сохраняются в `logs/app.log` с ротацией:
- Максимальный размер файла: 10MB
- Количество резервных файлов: 5
- Формат: `LEVEL YYYY-MM-DDTHH:MM:SS message`

Доменные операции (BUY, SELL, REGISTER, LOGIN) логируются с подробной информацией:
- Время операции
- Пользователь
- Валюта и количество
- Результат (OK/ERROR)
- Ошибки (если есть)

## Сборка и публикация

### Сборка пакета

```bash
make build
```

Создаст файлы в `dist/`:
- `finalproject_tonkushin_m25_555-0.1.0-py3-none-any.whl`
- `finalproject-tonkushin-m25-555-0.1.0.tar.gz`

### Установка собранного пакета

```bash
make package-install
```

### Публикация (dry-run)

```bash
make publish
```

## Проверка кода

### Линтинг

```bash
make lint
```

Используется Ruff для проверки соответствия PEP8.

## Примеры использования

### Полный цикл работы

```bash
# 1. Регистрация
poetry run project register --username alice --password secret123

# 2. Вход
poetry run project login --username alice --password secret123

# 3. Обновление курсов
poetry run project update-rates

# 4. Просмотр курсов
poetry run project show-rates --top 3

# 5. Покупка криптовалюты
poetry run project buy --currency BTC --amount 0.001

# 6. Просмотр портфеля
poetry run project show-portfolio

# 7. Получение курса
poetry run project get-rate --from BTC --to USD

# 8. Продажа валюты
poetry run project sell --currency BTC --amount 0.0005

# 9. Просмотр портфеля после продажи
poetry run project show-portfolio
```

### Демонстрация обработки ошибок

```bash
# Попытка продать больше, чем есть
poetry run project sell --currency BTC --amount 1.0

# Попытка использовать неизвестную валюту
poetry run project buy --currency XYZ --amount 100

# Попытка выполнить операцию без входа
poetry run project show-portfolio
```

## Технические детали

### Архитектура

- **Core Service**: Бизнес-логика, модели данных, usecases
- **Parser Service**: Микросервис для получения курсов из внешних API
- **CLI**: Тонкий слой для взаимодействия с пользователем
- **Infrastructure**: Singleton для конфигурации и базы данных

### Паттерны проектирования

- **Singleton**: `SettingsLoader`, `DatabaseManager`
- **Factory**: `get_currency()` для создания валют
- **Strategy**: `BaseApiClient` с реализациями для разных API
- **Decorator**: `@log_action` для логирования операций

### Безопасность

- Пароли хешируются с использованием SHA-256 и уникальной соли
- API-ключи хранятся в переменных окружения
- Валидация всех входных данных
- Защита от отрицательных балансов

## Лицензия

Проект создан в рамках учебного курса.

## Автор

Tonkushin M25-555
