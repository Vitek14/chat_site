"""Загружает демонстрационный сценарий лекции в базу.

Команда идемпотентна: повторный запуск обновляет существующие записи,
не создавая дубликатов.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from chatbot.models import DialogOption, DialogStep, Greeting

IMAGE_POOL = "https://placehold.co/640x360.png?text=Connection+Pool"
IMAGE_DASHBOARD = "https://placehold.co/640x360.png?text=Data+Dashboard"
IMAGE_QUERY = "https://placehold.co/640x360.png?text=SQL+Query"

GOOGLE_FORM_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLScKNr7JJg2ZO96yIqRCoIGQikfIyZIDD_2bjwQHUpiRyyB4-A"
    "/viewform?usp=publish-editor"
)

MYSQL_DOCS = "https://dev.mysql.com/doc/refman/8.4/en/connecting.html"
MARIADB_DOCS = "https://mariadb.com/kb/en/connecting-to-mariadb/"
WORKBENCH_DOCS = "https://dev.mysql.com/doc/workbench/en/"
PHPMYADMIN_DOCS = "https://docs.phpmyadmin.net/en/latest/"
DATAGRIP_DOCS = "https://www.jetbrains.com/help/datagrip/"

GREETINGS = [
    {
        "text": (
            "🏦 <b>Добрый день!</b> Я ваш персональный консультант «дата-банка». "
            "Сегодня поговорим о том, как наши клиенты подключаются к базе данных "
            "и как смотрят на свои счета. 💳"
        ),
        "image_url": "",
        "is_active": True,
    },
    {
        "text": (
            "👋 <b>Рады видеть вас в отделении «Дата-банк»!</b> "
            "Вы на верном пути: сегодня разберём подключение к MySQL/MariaDB "
            "и инструменты визуализации. 🏧"
        ),
        "image_url": "",
        "is_active": True,
    },
    {
        "text": (
            "🏛️ <b>Уважаемый клиент!</b> Наш консультант по базам данных к вашим услугам. "
            "Присядьте, возьмите выписку — и начнём нашу лекцию. 📊"
        ),
        "image_url": IMAGE_DASHBOARD,
        "is_active": True,
    },
]

STEPS = [
    {
        "code": "intro",
        "is_start": True,
        "bot_text": (
            "🧾 <b>Открываем наш счёт подключения.</b><br><br>"
            "В «дата-банке» есть четыре ключевые «банковские карты» для работы с базой: "
            "<b>драйвер</b> 🛠, <b>строка подключения</b> 🔗, <b>пул соединений</b> 🏊 "
            "и <b>транзакции</b> 💳.<br><br>"
            "Драйвер — это наш курьер, который несёт запросы к серверу. "
            "Строка подключения — адрес отделения банка. "
            "Пул соединений — очередь на обслуживание. "
            "А транзакция — это одна атомарная «операция по списанию». 💸<br><br>"
            "Куда движемся? 👇"
        ),
        "image_url": "",
        "delay_ms": 400,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "➡️ Далее: как подключиться", "action": "goto", "target": "mysql_specifics"},
            {"label": "🔍 Показать пример кода", "action": "goto", "target": "example"},
            {"label": "🧠 Подробнее, как это работает", "action": "goto", "target": "details_connections"},
        ],
    },
    {
        "code": "mysql_specifics",
        "bot_text": (
            "🐬 <b>MySQL и MariaDB: наши основные хранилища.</b><br><br>"
            "Стандартный порт — <b>3306</b>. Для Python чаще всего используют драйверы "
            "<code>mysqlclient</code> (C-расширение, быстрый) или <code>PyMySQL</code> "
            "(чистый Python, ставится без компилятора).<br><br>"
            "Строка подключения для SQLAlchemy выглядит так:<br>"
            "<code>mysql+pymysql://user:password@127.0.0.1:3306/bank</code><br><br>"
            "А для Django в <code>settings.py</code>:<br>"
            "<code>DATABASES = {&#39;default&#39;: {&#39;ENGINE&#39;: "
            "&#39;django.db.backends.mysql&#39;, &#39;NAME&#39;: &#39;bank&#39;, ...}}</code><br><br>"
            "📚 Документация: "
            f"<a href='{MYSQL_DOCS}' target='_blank' rel='noopener'>MySQL: Connecting to MySQL</a> · "
            f"<a href='{MARIADB_DOCS}' target='_blank' rel='noopener'>MariaDB: Connecting</a>"
        ),
        "image_url": "",
        "delay_ms": 700,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "➡️ Далее: инструменты визуализации", "action": "goto", "target": "visualization"},
            {"label": "🧠 Подробнее про транзакции", "action": "goto", "target": "details_transactions"},
            {"label": "⬅️ Назад", "action": "back"},
        ],
    },
    {
        "code": "example",
        "bot_text": (
            "💻 <b>Пример: как выглядит «операция по списанию» в коде.</b><br><br>"
            "<pre class='bg-light p-2 rounded'>from sqlalchemy import create_engine, text\n\n"
            "engine = create_engine(\n"
            "    &quot;mysql+pymysql://app:secret@127.0.0.1:3306/bank&quot;,\n"
            "    pool_size=5, max_overflow=10,\n)\n\n"
            "with engine.begin() as conn:  # транзакция\n"
            "    rows = conn.execute(\n"
            "        text(&quot;SELECT * FROM accounts WHERE balance &gt; :limit&quot;),\n"
            "        {&quot;limit&quot;: 1000},\n"
            "    ).all()</pre>"
            "<br>Обратите внимание: <code>engine.begin()</code> сам открывает и закрывает "
            "транзакцию — кредит проходит либо целиком, либо никак. ⚖️"
        ),
        "image_url": IMAGE_QUERY,
        "delay_ms": 900,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "➡️ Далее: инструменты визуализации", "action": "goto", "target": "visualization"},
            {"label": "⬅️ Назад", "action": "back"},
            {"label": "🔄 Начать лекцию заново", "action": "restart"},
        ],
    },
    {
        "code": "details_connections",
        "bot_text": (
            "🧠 <b>Подробно: как устроено подключение к базе.</b><br><br>"
            "<b>1. Драйвер.</b> Он знает протокол MySQL и умеет говорить с сервером на его языке. "
            "Без драйвера приложение — это клиент без банковской карты. 💳<br>"
            "<b>2. Строка подключения.</b> Хост, порт, имя базы, логин и пароль. "
            "Пароль лучше держать в переменных окружения, а не в коде. 🔐<br>"
            "<b>3. Пул соединений.</b> Держать соединение открытым дорого, "
            "создавать новое на каждый запрос — тоже. Пул держит N «открытых окон» и выдаёт их по мере надобности. 🏊<br>"
            "<b>4. Транзакции.</b> <code>BEGIN → работа → COMMIT</code> (или <code>ROLLBACK</code>). "
            "Деньги либо приходят, либо нет — «на полпути» быть не может. 💸"
        ),
        "image_url": IMAGE_POOL,
        "delay_ms": 800,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "➡️ Далее: инструменты визуализации", "action": "goto", "target": "visualization"},
            {"label": "⬅️ Назад", "action": "back"},
        ],
    },
    {
        "code": "visualization",
        "bot_text": (
            "📊 <b>Визуализация и управление: наш торговый зал.</b><br><br>"
            "Чтобы посмотреть «выписку по счетам», нужен клиент с графическим интерфейсом:<br>"
            "• <b>MySQL Workbench</b> — официальный инструмент MySQL: схема, ER-диаграммы, slow query log. 🛠<br>"
            "• <b>phpMyAdmin</b> — веб-панель на PHP, работает с MySQL и MariaDB. 🌐<br>"
            "• <b>DataGrip</b> — IDE от JetBrains: автодополнение, рефакторинг, отчёты. 🧠<br>"
            "• <b>Админ-панели приложений</b> — Django Admin, Rails Admin: CRUD «из коробки». ⚙️<br><br>"
            "📚 <a href='{WORKBENCH_DOCS}' target='_blank' rel='noopener'>Документация Workbench</a> · "
            "<a href='{PHPMYADMIN_DOCS}' target='_blank' rel='noopener'>Документация phpMyAdmin</a> · "
            "<a href='{DATAGRIP_DOCS}' target='_blank' rel='noopener'>Документация DataGrip</a>"
        ),
        "image_url": IMAGE_DASHBOARD,
        "delay_ms": 1000,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "⚖️ Сравнить инструменты", "action": "goto", "target": "tools_compare"},
            {"label": "➡️ Далее: транзакции и права", "action": "goto", "target": "transactions"},
            {"label": "⬅️ Назад", "action": "back"},
        ],
    },
    {
        "code": "tools_compare",
        "bot_text": (
            "⚖️ <b>Сравнение клиентов: кому какой «банковский терминал» подходит.</b><br><br>"
            "<table class='table table-sm table-bordered bg-white'>"
            "<thead><tr><th>Инструмент</th><th>Тип</th><th>Сильная сторона</th></tr></thead><tbody>"
            "<tr><td>Workbench</td><td>десктоп</td><td>схема и ER-диаграммы</td></tr>"
            "<tr><td>phpMyAdmin</td><td>веб</td><td>быстрый доступ без установки</td></tr>"
            "<tr><td>DataGrip</td><td>IDE</td><td>умный SQL и рефакторинг</td></tr>"
            "<tr><td>Django Admin</td><td>веб</td><td>управление данными модели</td></tr>"
            "</tbody></table>"
            "<br>Общий знаменатель: все они используют тот же драйвер и ту же строку подключения. 🧩"
        ),
        "image_url": "",
        "delay_ms": 700,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "➡️ Далее: транзакции и права", "action": "goto", "target": "transactions"},
            {"label": "⬅️ Назад", "action": "back"},
            {"label": "🔄 Начать лекцию заново", "action": "restart"},
        ],
    },
    {
        "code": "details_transactions",
        "bot_text": (
            "🧠 <b>Подробно: транзакции и «кредитный лимит».</b><br><br>"
            "<b>Транзакция</b> — это группа операций, которая выполняется целиком. "
            "В MySQL есть уровни изоляции: READ UNCOMMITTED, READ COMMITTED, "
            "REPEATABLE READ (по умолчанию) и SERIALIZABLE. 🧾<br><br>"
            "<b>Кредитный лимит</b> — это права доступа: <code>GRANT</code> и <code>REVOKE</code> "
            "выдают пользователю доступ только к нужным таблицам и операциям. "
            "Чем меньше лимитов, тем меньше риска. 🔐<br><br>"
            "<b>Автоинкремент и индексы</b> — это внутренние «индексы банка»: "
            "поиск по primary key работает в разы быстрее, чем по колонке без индекса. ⚡"
        ),
        "image_url": "",
        "delay_ms": 800,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "➡️ Далее: финальный чек", "action": "goto", "target": "final"},
            {"label": "⬅️ Назад", "action": "back"},
        ],
    },
    {
        "code": "transactions",
        "bot_text": (
            "💳 <b>Транзакции и права доступа — операционный день банка.</b><br><br>"
            "• Каждая операция с деньгами должна быть атомарной: <code>BEGIN</code> → "
            "<code>UPDATE accounts ...</code> → <code>COMMIT</code>. ⚖️<br>"
            "• При ошибке — <code>ROLLBACK</code>, и клиент даже не заметит сбоя. 🔄<br>"
            "• Права: <code>GRANT SELECT, INSERT ON bank.accounts TO 'app'@'localhost';</code> "
            "— кредитный лимит клиента. 🔐<br>"
            "• <code>SELECT ... FOR UPDATE</code> — блокировка строки, чтобы два "
            "менеджера не провели одну и ту же операцию дважды. 🔒"
        ),
        "image_url": "",
        "delay_ms": 700,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": "clarify",
        "options": [
            {"label": "🧠 Ещё подробнее", "action": "goto", "target": "details_transactions"},
            {"label": "➡️ Далее: финальный чек", "action": "goto", "target": "final"},
            {"label": "⬅️ Назад", "action": "back"},
        ],
    },
    {
        "code": "clarify",
        "bot_text": (
            "🧭 <b>Такой операции в моём реестре нет.</b><br><br>"
            "Давайте вернёмся к началу лекции — там мы разбирали драйверы, "
            "строку подключения, пул и транзакции. 🏦"
        ),
        "image_url": "",
        "delay_ms": 400,
        "is_final": False,
        "google_form_url": "",
        "fallback_step": None,
        "options": [
            {"label": "➡️ В начало", "action": "goto", "target": "intro"},
            {"label": "🛠 К подключению", "action": "goto", "target": "mysql_specifics"},
            {"label": "🔄 Начать лекцию заново", "action": "restart"},
        ],
    },
    {
        "code": "final",
        "bot_text": (
            "🏁 <b>Лекция завершена — спасибо за визит!</b><br><br>"
            "Итог: <b>драйвер</b> 🛠 + <b>строка подключения</b> 🔗 + <b>пул</b> 🏊 = "
            "надёжный доступ к данным; <b>транзакции</b> 💳 гарантируют целостность; "
            "<b>Workbench, phpMyAdmin, DataGrip и админ-панели</b> 📊 дают визуализацию и управление.<br><br>"
            "Осталось оставить нам обратную связь — заполните короткую анкету, "
            "и мы начислим баллы на ваш «клиентский счёт». 📝"
        ),
        "image_url": "",
        "delay_ms": 900,
        "is_final": True,
        "google_form_url": GOOGLE_FORM_URL,
        "fallback_step": "clarify",
        "options": [
            {"label": "📝 Пройти анкету", "action": "end"},
            {"label": "🔄 Пройти лекцию заново", "action": "restart"},
            {"label": "⬅️ Назад", "action": "back"},
        ],
    },
]


class Command(BaseCommand):
    help = "Загружает (или обновляет) демонстрационный сценарий лекции."

    @transaction.atomic
    def handle(self, *args, **options):
        greeting_count = 0
        for data in GREETINGS:
            greeting, created = Greeting.objects.update_or_create(
                text=data["text"],
                defaults={
                    "image_url": data["image_url"],
                    "is_active": data["is_active"],
                },
            )
            greeting_count += 1 if created else 0

        steps: dict[str, DialogStep] = {}
        for data in STEPS:
            code = data["code"]
            step, _ = DialogStep.objects.update_or_create(
                code=code,
                defaults={
                    "bot_text": data["bot_text"],
                    "image_url": data["image_url"],
                    "delay_ms": data["delay_ms"],
                    "is_final": data["is_final"],
                    "google_form_url": data["google_form_url"],
                    "is_start": data.get("is_start", False),
                    "fallback_step": None,
                },
            )
            steps[code] = step

        for data in STEPS:
            step = steps[data["code"]]
            fallback_code = data.get("fallback_step")
            step.fallback_step = steps.get(fallback_code) if fallback_code else None
            step.save(update_fields=["fallback_step"])

        option_count = 0
        for data in STEPS:
            step = steps[data["code"]]
            for order, option_data in enumerate(data["options"], start=1):
                target_code = option_data.get("target")
                DialogOption.objects.update_or_create(
                    step=step,
                    label=option_data["label"],
                    defaults={
                        "order": order,
                        "action": option_data["action"],
                        "target_step": steps.get(target_code) if target_code else None,
                    },
                )
                option_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Сценарий загружен: {greeting_count} новых приветствий, "
                f"{len(steps)} шагов, {option_count} вариантов ответа. "
                "Повторный запуск безопасен."
            )
        )
