import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import DialogOption, DialogStep, Greeting

SESSION_HISTORY_KEY = "history"
SESSION_CURRENT_KEY = "current_step"

GENERIC_FALLBACK_TEXT = (
    "🤔 Хмм, кажется, мы вышли за пределы моего реестра операций. "
    "Такой запрос в банковской выписке не значится. "
    "Давайте вернёмся к началу — нажмите «Начать заново». 🔄"
)

END_TEXT = (
    "🏦 Спасибо за визит в наш «дата-банк»! Остаток на счёте знаний только растёт. "
    "До встречи! 👋"
)


def _start_step() -> DialogStep | None:
    step = DialogStep.objects.filter(is_start=True).order_by("id").first()
    if step is None:
        step = DialogStep.objects.order_by("id").first()
    return step


def _options_payload(step: DialogStep) -> list[dict]:
    return [
        {
            "id": option.id,
            "label": option.label,
            "action": option.action,
        }
        for option in step.options.select_related("target_step").order_by("order", "id")
    ]


def _step_payload(step: DialogStep) -> dict:
    return {
        "step_code": step.code,
        "text": step.bot_text,
        "image_url": step.image_url,
        "delay_ms": step.delay_ms,
        "is_final": step.is_final,
        "google_form_url": step.google_form_url,
        "options": _options_payload(step),
    }


def _random_greeting() -> dict | None:
    greeting = Greeting.objects.filter(is_active=True).order_by("?").first()
    if greeting is None:
        return None
    return {"text": greeting.text, "image_url": greeting.image_url}


def _history(request) -> list[str]:
    return list(request.session.get(SESSION_HISTORY_KEY, []))


def _push_history(request, step_code: str) -> None:
    history = _history(request)
    history.append(step_code)
    request.session[SESSION_HISTORY_KEY] = history


def _reset_session(request) -> None:
    request.session[SESSION_HISTORY_KEY] = []
    request.session.pop(SESSION_CURRENT_KEY, None)


@require_GET
def index(request):
    return render(request, "chatbot/chat.html")


@require_POST
def api_start(request):
    """Сбрасывает состояние сессии и отдаёт приветствие и первый шаг."""
    _reset_session(request)
    start = _start_step()
    if start is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "Сценарий не загружен. Выполните: python manage.py load_scenario",
            },
            status=503,
        )
    request.session[SESSION_CURRENT_KEY] = start.code
    return JsonResponse(
        {
            "ok": True,
            "result": "step",
            "greeting": _random_greeting(),
            "step": _step_payload(start),
        }
    )


@require_POST
def api_choose(request):
    """Обрабатывает нажатие кнопки и возвращает следующий шаг."""
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Некорректный JSON"}, status=400)

    step_code = payload.get("step_code") or ""
    option_id = payload.get("option_id")

    current_code = request.session.get(SESSION_CURRENT_KEY)
    current = DialogStep.objects.filter(code=current_code).first() if current_code else None
    if current is None:
        current = _start_step()
    if current is None:
        return JsonResponse(
            {"ok": False, "error": "Сценарий не загружен."},
            status=503,
        )

    option = None
    if option_id is not None:
        option = (
            DialogOption.objects.filter(pk=option_id, step=current)
            .select_related("target_step")
            .first()
        )

    if option is None:
        # Некорректный выбор: уходим в fallback-шаг или в общее сообщение.
        if option_id is None:
            return _restart_response(request)
        if current.fallback_step_id:
            _push_history(request, current.code)
            request.session[SESSION_CURRENT_KEY] = current.fallback_step.code
            return JsonResponse(
                {"ok": True, "result": "step", "step": _step_payload(current.fallback_step)}
            )
        return JsonResponse(
            {
                "ok": True,
                "result": "fallback",
                "step": {
                    "step_code": current.code,
                    "text": GENERIC_FALLBACK_TEXT,
                    "image_url": "",
                    "delay_ms": 400,
                    "is_final": False,
                    "google_form_url": "",
                    "options": [
                        {"id": None, "label": "🔄 Начать заново", "action": "restart"}
                    ],
                },
            }
        )

    if option.action == DialogOption.ACTION_GOTO:
        target = option.target_step
        if target is None:
            target = current.fallback_step or current
        _push_history(request, current.code)
        request.session[SESSION_CURRENT_KEY] = target.code
        return JsonResponse(
            {"ok": True, "result": "step", "step": _step_payload(target)}
        )

    if option.action == DialogOption.ACTION_BACK:
        history = _history(request)
        if history:
            previous_code = history.pop()
            request.session[SESSION_HISTORY_KEY] = history
            previous = DialogStep.objects.filter(code=previous_code).first()
        else:
            previous = _start_step()
        if previous is None:
            previous = current
        request.session[SESSION_CURRENT_KEY] = previous.code
        return JsonResponse(
            {"ok": True, "result": "step", "step": _step_payload(previous)}
        )

    if option.action == DialogOption.ACTION_RESTART:
        return _restart_response(request)

    # ACTION_END
    _reset_session(request)
    return JsonResponse({"ok": True, "result": "end", "text": END_TEXT})


def _restart_response(request) -> JsonResponse:
    _reset_session(request)
    start = _start_step()
    if start is None:
        return JsonResponse({"ok": False, "error": "Сценарий не загружен."}, status=503)
    request.session[SESSION_CURRENT_KEY] = start.code
    return JsonResponse(
        {
            "ok": True,
            "result": "restart",
            "greeting": _random_greeting(),
            "step": _step_payload(start),
        }
    )

