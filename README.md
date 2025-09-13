### Chatwoot Notification Bot

Асинхронный сервер для приёма вебхуков Chatwoot и отправки уведомлений администраторам в Telegram. Поддерживает локализацию сообщений и рейтлимиты Telegram.

### Возможности
- Отправка уведомлений в Telegram админам (через `aiogram`).
- Рейтлимит на отправку (globally) через `aiolimiter`.
- Конфигурация через `.env`.
- Локализация текстов через YAML (`locales/*.yml`).
- Готовый Dockerfile и docker-compose.

### Быстрый старт (Docker)
```bash
cp .env.example .env
# отредактируйте .env (токен бота, админы, URL Chatwoot)

docker compose build
docker compose up -d
# логи
docker compose logs -f
```
Проверка здоровья:
```bash
curl http://localhost:8000/health
```
Ожидается `ok`.

### Эндпоинты
- `GET /health` — healthcheck.
- `POST /webhooks/chatwoot` — обработчик вебхуков Chatwoot (событие `message_created`).

### Переменные окружения (.env)
- `TELEGRAM_BOT_TOKEN` — токен бота Telegram (BotFather).
- `TELEGRAM_ADMIN_IDS` — список chat_id админов через запятую, например: `123,456`.
- `CHATWOOT_BASE_URL` — базовый URL Chatwoot, например: `https://chatwoot.example.com`.
- `HOST` — хост сервера (по умолчанию `0.0.0.0`).
- `PORT` — порт сервера (по умолчанию `8000`).
- `LOCALE` — текущая локаль (по умолчанию `ru`).
- `RATE_LIMIT_PER_SEC` — лимит сообщений в секунду для Telegram (по умолчанию `25`).

Пример:
```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_ADMIN_IDS=11111111,22222222
CHATWOOT_BASE_URL=https://chatwoot.example.com
HOST=0.0.0.0
PORT=8000
LOCALE=ru
RATE_LIMIT_PER_SEC=25
```

### Настройка Chatwoot Webhook
1) В админке Chatwoot: Settings → Integrations → Webhooks → Add new webhook.
2) URL: `https://YOUR_PUBLIC_HOST/webhooks/chatwoot` (или `http://...` в тестовой среде).
3) События: включите минимум `message_created`.
4) Сохраните.

### Настройка Telegram
- Создайте бота у BotFather, получите токен → `TELEGRAM_BOT_TOKEN`.
- Узнайте `chat_id` администраторов (например, через @getidsbot, или логикой в своём боте) → перечислите через запятую в `TELEGRAM_ADMIN_IDS`.

### Локализации
Файлы в `locales/*.yml`. По умолчанию используется `locales/ru.yml`.

Ключ, используемый для уведомления:
- `notifications.support_new_message`

Пример `locales/ru.yml`:
```yaml
notifications:
  support_new_message: "<b>Новое сообщение в технической поддержке!</b>\nПользователь {user_name} ждёт ответа от агента технической поддержки {assignee_name}\n<a href='{link}'>Перейти в диалог</a>"
```
Доступные плейсхолдеры: `{user_name}`, `{assignee_name}`, `{link}`.

### Запуск локально (без Docker)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# отредактируйте .env
python -m app.main
```
Сервер поднимется на `http://0.0.0.0:8000`.

### Проверка вебхука (dev)
```bash
curl -X POST http://localhost:8000/webhooks/chatwoot \
  -H 'Content-Type: application/json' \
  -d '{
    "event": "message_created",
    "conversation": {
      "id": 42,
      "meta": {
        "sender": {"name": "Иван", "blocked": false},
        "assignee": {"name": "Агент", "id": 1}
      }
    }
  }'
```
Ожидается ответ `success` и отправка уведомления в Telegram админам.

### Как это работает
- Aiohttp-приложение (`app/main.py`) принимает вебхук, извлекает `sender`, `assignee`, `conversation/account id`,
  собирает ссылку вида `{CHATWOOT_BASE_URL}/app/accounts/{account_id}/conversations/{conversation_id}` и отправляет
  локализованный текст всем `TELEGRAM_ADMIN_IDS`.
- Отправка сообщений ограничена с помощью `aiolimiter` (значение `RATE_LIMIT_PER_SEC`).

### Примечания
- Обрабатывается событие `message_created`. Если нужно покрыть другие события/фильтры (например, только публичные сообщения), дайте знать — расширим логику.
- Для продакшена обеспечьте доступность сервиса по HTTPS (через обратный прокси: Nginx/Traefik).
