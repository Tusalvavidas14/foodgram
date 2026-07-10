from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Настройки приложения пользователей и подписок."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'
