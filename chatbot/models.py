from django.core.exceptions import ValidationError
from django.db import models


class Greeting(models.Model):
    """Приветственное сообщение, показываемое в начале диалога."""

    text = models.TextField(
        "Текст приветствия",
        help_text="Может содержать HTML, эмодзи и ссылки.",
    )
    image_url = models.URLField("URL изображения", blank=True)
    is_active = models.BooleanField("Активно", default=True)

    class Meta:
        verbose_name = "Приветствие"
        verbose_name_plural = "Приветствия"
        ordering = ["id"]

    def __str__(self):
        return self.text[:60]


class DialogStep(models.Model):
    """Один шаг (реплика) диалога."""

    code = models.SlugField("Код шага", max_length=64, unique=True)
    bot_text = models.TextField(
        "Текст бота",
        help_text="Может содержать HTML, эмодзи, ссылки и <img>.",
    )
    image_url = models.URLField("URL изображения", blank=True)
    delay_ms = models.PositiveIntegerField("Задержка ответа, мс", default=0)
    is_final = models.BooleanField("Финальный шаг", default=False)
    google_form_url = models.URLField("Ссылка на Google-форму", blank=True)
    fallback_step = models.ForeignKey(
        "self",
        verbose_name="Шаг при неверном выборе",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fallback_targets",
    )
    is_start = models.BooleanField("Начальный шаг", default=False)

    class Meta:
        verbose_name = "Шаг диалога"
        verbose_name_plural = "Шаги диалога"
        ordering = ["id"]

    def __str__(self):
        return self.code


class DialogOption(models.Model):
    """Кнопка (вариант ответа) на шаге диалога."""

    ACTION_GOTO = "goto"
    ACTION_BACK = "back"
    ACTION_RESTART = "restart"
    ACTION_END = "end"

    ACTION_CHOICES = [
        (ACTION_GOTO, "Перейти к шагу"),
        (ACTION_BACK, "Назад"),
        (ACTION_RESTART, "Начать заново"),
        (ACTION_END, "Завершить"),
    ]

    step = models.ForeignKey(
        DialogStep,
        verbose_name="Шаг",
        on_delete=models.CASCADE,
        related_name="options",
    )
    label = models.CharField("Подпись кнопки", max_length=200)
    order = models.PositiveIntegerField("Порядок", default=0)
    action = models.CharField("Действие", max_length=10, choices=ACTION_CHOICES)
    target_step = models.ForeignKey(
        DialogStep,
        verbose_name="Целевой шаг",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="targeted_by",
    )

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответа"
        ordering = ["order", "id"]

    def clean(self):
        super().clean()
        if self.action == self.ACTION_GOTO and not self.target_step_id:
            raise ValidationError(
                {"target_step": "Для действия «Перейти к шагу» нужно указать целевой шаг."}
            )
        if self.action != self.ACTION_GOTO and self.target_step_id:
            raise ValidationError(
                {"target_step": "Целевой шаг указывается только для действия «Перейти к шагу»."}
            )

    def __str__(self):
        return f"{self.step.code}: {self.label} [{self.action}]"
