from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/start/", views.api_start, name="api_start"),
    path("api/choose/", views.api_choose, name="api_choose"),
]
