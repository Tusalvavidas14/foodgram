from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Настройки приложения с эндпоинтами, сериализаторами и вьюсетами."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
