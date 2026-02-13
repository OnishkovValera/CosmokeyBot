# Телеграм бот для Cosmokey 
Этот репозиторий содержит код для телеграм бота косметической компании Cosmokey.

## Содержание
 - [Описание](#описание)
 - [Технологии](#технологии)
 - [Даталогическая модель бд](#даталогическая-модель-базы-данных)
 - [Структура проекта](#структура-проекта)
 - [Деплой](#деплой)
## Описание
Телегарам бот для Cosmokey, предназначен для взаимодействия с клиентами компании,
предоставления информации о продуктах, акциях и поддержке клиентов.

Бот имеет несколько функций: 
 - Предоставление помощи
    - Сообщение о браке/повреждении товара
    - Претензия или жалоба на товар
    - Получение обратной связи о товаре
 - Возможность получения денежного вознаграждения за отзыв о товаре
 - Получение полезной информации о продукции компании
 - Получение подарка за подписку на канал компании в телеграме

## Технологии
 - Python 3.10
 - aiogram 3.0
 - asyncpg
 - SQLAlchemy 2.0
 - Alembic
 - PostgreSQL
 - redis
 - pydentic
 - loguru
 - python-dotenv


## Даталогическая модель базы данных:
```postgresql
CREATE TABLE users
(
   id                             SERIAL PRIMARY KEY,
   telegram_id                    BIGINT       NOT NULL UNIQUE,
   username                       VARCHAR(256) NOT NULL,
   chat_id                        BIGINT       NOT NULL,
   is_subscribed                  BOOLEAN      NOT NULL DEFAULT FALSE,
   is_got_reward_for_subscription BOOLEAN      NOT NULL DEFAULT FALSE,
   created_at                     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE assistance_requests
(
   id           SERIAL PRIMARY KEY,
   user_id      INTEGER      NOT NULL REFERENCES users (id),
   request_type VARCHAR(256) NOT NULL,
   message_id   BIGINT       NOT NULL,
   created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
   is_processed BOOLEAN      NOT NULL DEFAULT FALSE,
   processed_at TIMESTAMP

);

CREATE TABLE messages_texts
(
   id          SERIAL PRIMARY KEY,
   message_key VARCHAR(256) NOT NULL UNIQUE,
   text        TEXT         NOT NULL
);

CREATE TABLE rewards
(
   id         SERIAL PRIMARY KEY,
   user_id    INTEGER      NOT NULL REFERENCES users (id),
   link       VARCHAR(512) NOT NULL,
   message_id BIGINT       NOT NULL,
   created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

```

## Структура проекта
 - readme-files - папка с тз
 - bot - папка с кодом бота
   - db - папка с кодом для работы с базой данных
   - fsm - папка с кодом для реализации конечного автомата состояний
   - handlers - папка с кодом для обработки сообщений от пользователей
   - middlewares - папка с кодом для обработки промежуточных действий
   - models - папка с кодом для описания моделей данных
   - services - папка с кодом для реализации бизнес-логики
   - utils - папка с кодом для вспомогательных функций и классов
   - main.py - основной файл для запуска бота
 - alembic - папка с кодом для миграций базы данных
 - docker-compose.yml - файл для настройки и запуска контейнеров с помощью Docker Compose
 - .env - файл для хранения переменных окружения
 - pyproject.toml - файл для управления зависимостями проекта

## Деплой
``` shell
docker compose build
docker compose up
```

## TODO
- [ ] подумать над проектом
- [x] можно ли отправлять несколько отзывов от одного пользователя на разные товары (ДА)
- [x] нужно ли ограничение на количество претензий/браков/обратных связей от одного пользователя (ДА, не более 40 открытых)
- [x] нужно ли добавить проверку на получение подарка за подписку на канал компании в телеграме (ДА)
- [x] нужно ли проверять, что ссылка на отзыв на товар идет с конкретного маркетплейса (НЕТ)
- [x] нужно ли проверять ссылки на идентичность отзыва (ДА)
- [x] стоит ли удалять обработанные запросы о помощи (Переводить в статус "обработано" и удалять из показа, но оставить возможность поиска по id)
- [ ] подумать над тем как это будет работать у администратора
- [ ] использовать сливы loguru 
- [ ] добавить информирование о критических сбоях
- [ ] использовать @dp.errors()
- [ ] добавить AiogramSink() в логгер для логирования критичных сбоев
- [ ] добавить работу с телеграм каналом компании
- [ ] добавить возможность менять тексты сообщений от бота через админку
- [ ] добавить функциональность eager инициализации текстов сообщений от бота из бд
- [ ] добавить возможность поиска запросов о помощи по id для администраторов