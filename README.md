# 🏦 Лекция-чатбот: «Компоненты подключения к БД. Визуализация и управление»

Небольшое production-готовое Django-приложение: интерактивная лекция по подключению
к MySQL/MariaDB и инструментам визуализации, оформленная как чат с консультантом
«дата-банка».

* **Без внешних LLM и API-ключей** — все реплики бота заранее подготовлены и хранятся в БД.
* **Без auth для посетителей** — сценарий редактируется через Django admin.
* **Без сборки фронтенда** — Django-шаблоны, Bootstrap 5 (CDN) и чистый JavaScript (Fetch API).
* **SQLite** + **Gunicorn** + **WhiteNoise** — готовый к деплою на Render.com.

---

## Возможности

| Функция | Где реализована |
|---|---|
| Несколько вариантов приветствия (выбирается случайный активный) | `Greeting`, `views.api_start` |
| Ветвление (3+ варианта ответа на первом шаге) | `DialogOption` |
| Кнопки «Назад» (стек навигации в сессии) и «Начать заново» | `request.session['history']` |
| «Else»-ветка: неверный выбор → `fallback_step` или общее сообщение | `DialogStep.fallback_step`, `views.api_choose` |
| Искусственная задержка ответа (анимация «печатает…») | `DialogStep.delay_ms` + фронтенд |
| Картинки внутри сообщений | `DialogStep.image_url` |
| Эмодзи и внешние ссылки на документацию | текст шагов (HTML) |
| Финальный шаг с кнопкой Google-формы | `is_final`, `google_form_url` |
| CSRF-защита всех POST-запросов | `X-CSRFToken` + `{% csrf_token %}` |

---

## Локальный запуск (UV)

```bash
uv sync                                   # установка зависимостей в .venv
uv run python manage.py migrate           # миграции (SQLite создаётся автоматически)
uv run python manage.py load_scenario     # загрузка демо-сценария (идемпотентно)
uv run python manage.py create_admin      # суперпользователь admin / admin
uv run python manage.py runserver         # http://127.0.0.1:8000/
```

Команда `load_scenario` безопасна для повторного запуска: записи обновляются, дубликаты
не создаются. Секрет сценария лежит в `chatbot/management/commands/load_scenario.py`
(тексты, кнопки, задержки, ссылки).

* Чат: <http://127.0.0.1:8000/>
* Админка: <http://127.0.0.1:8000/admin/> (логин/пароль из `create_admin`, по умолчанию `admin`/`admin`)

В админке доступны модели `Greeting`, `DialogStep` (с inline-вариантами ответов
`DialogOption`) и `DialogOption`. Чтобы сценарий сразу попал в базу на Render —
команда `load_scenario` включена в build-команду.

---

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `SECRET_KEY` | dev-ключ | Секретный ключ Django (**обязателен в проде**) |
| `DEBUG` | `1` | `1`/`0`. На Render выставляйте `0` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1],testserver` | Список хостов через запятую |
| `CSRF_TRUSTED_ORIGINS` | пусто | Дополнительные доверенные origin'ы (через запятую) |
| `DB_PATH` | `db.sqlite3` в корне | Путь к файлу SQLite |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | `admin` / `admin` / `admin@example.com` | Данные суперпользователя для `create_admin` |

Пример локального запуска с прод-настройками:

```bash
DEBUG=0 SECRET_KEY="change-me" ALLOWED_HOSTS="example.onrender.com" \
  uv run python manage.py runserver
```

---

## Деплой на Render.com

В репозитории есть готовый `render.yaml`, но шаги те же:

1. **New → Web Service**, подключить репозиторий, выбрать план *Free*.
2. **Build Command:**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   export PATH="$HOME/.local/bin:$PATH"
   uv sync --frozen
   uv run python manage.py migrate
   uv run python manage.py collectstatic --noinput
   uv run python manage.py load_scenario
   ```

3. **Start Command:**

   ```bash
   uv run gunicorn config.wsgi:application --chdir .
   ```

4. **Environment Variables:**

   ```
   SECRET_KEY=<случайная строка>
   DEBUG=0
   ALLOWED_HOSTS=*
   ```

   (опционально `CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com`)

5. После деплоя выполните в Render Shell:

   ```bash
   uv run python manage.py create_admin   # создать админа
   ```

### ⚠️ SQLite на Render

Файл SQLite **эпизодический**: при каждом редеплое (и при перезапуске free-инстанса)
база может быть пересоздана, поэтому изменения, сделанные через админку, пропадут.
Сценарий восстанавливается командой `load_scenario` в build-процессе — этого достаточно
для демонстрации. Если нужна постоянная база, добавьте Render Disk и переменную
`DB_PATH=/var/data/db.sqlite3` (уже прописано в `render.yaml`) либо переходите на
PostgreSQL.

---

## Структура проекта

```
PycharmProjects/chat_bot/
├── .gitignore
├── README.md
├── pyproject.toml                 # управляется uv (requirements.txt НЕ используется)
├── uv.lock
├── render.yaml                    # конфигурация деплоя на Render
├── manage.py
├── config/                        # проект Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                # настройки через переменные окружения
│   ├── urls.py                    # /admin/ + подключение chatbot
│   └── wsgi.py                    # точка входа для gunicorn
└── chatbot/                       # приложение
    ├── __init__.py
    ├── admin.py                   # Greeting, DialogStep (+inline DialogOption), DialogOption
    ├── apps.py
    ├── models.py                  # Greeting, DialogStep, DialogOption
    ├── urls.py                    # /, /api/start/, /api/choose/
    ├── views.py                   # index, api_start, api_choose (goto/back/restart/end/fallback)
    ├── management/
    │   └── commands/
    │       ├── __init__.py
    │       ├── create_admin.py    # идемпотентное создание суперпользователя
    │       └── load_scenario.py   # идемпотентная загрузка демо-сценария (~10 шагов)
    ├── migrations/
    │   ├── __init__.py
    │   └── 0001_initial.py
    ├── static/chatbot/chat.js     # фронтенд: fetch, «печатает…», кнопки, автоскролл
    └── templates/chatbot/
        ├── base.html              # Bootstrap 5 (CDN), стили чата
        └── chat.html              # страница чата
```

---

## API

### `POST /api/start/`

Сбрасывает состояние диалога в сессии, возвращает случайное приветствие и первый шаг.

```json
{
  "ok": true,
  "result": "step",
  "greeting": {"text": "🏦 ...", "image_url": ""},
  "step": {
    "step_code": "intro",
    "text": "🧾 ...",
    "image_url": "",
    "delay_ms": 400,
    "is_final": false,
    "google_form_url": "",
    "options": [{"id": 1, "label": "➡️ Далее: как подключиться", "action": "goto"}]
  }
}
```

### `POST /api/choose/`

Тело: `{"step_code": "intro", "option_id": 2}`.

* `result: "step"` — переход (`goto` / `back` / `fallback_step`);
* `result: "restart"` — диалог сброшен, приветствие и первый шаг отдаются заново;
* `result: "end"` — диалог завершён;
* `result: "fallback"` — неверный выбор и у шага нет `fallback_step`, показано общее сообщение.

Оба запроса защищены CSRF-токеном (заголовок `X-CSRFToken`).
