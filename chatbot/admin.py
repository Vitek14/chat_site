from django.contrib import admin

from .models import DialogOption, DialogStep, Greeting


class DialogOptionInline(admin.TabularInline):
    model = DialogOption
    fk_name = "step"
    extra = 1
    fields = ("label", "order", "action", "target_step")


@admin.register(Greeting)
class GreetingAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "is_active", "image_url")
    list_filter = ("is_active",)
    list_editable = ("is_active",)

    @admin.display(description="Текст")
    def short_text(self, obj):
        return obj.text[:60]


@admin.register(DialogStep)
class DialogStepAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "is_start", "is_final", "delay_ms", "fallback_step")
    list_filter = ("is_start", "is_final")
    search_fields = ("code", "bot_text")
    inlines = [DialogOptionInline]


@admin.register(DialogOption)
class DialogOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "step", "label", "order", "action", "target_step")
    list_filter = ("action",)
    search_fields = ("label",)
