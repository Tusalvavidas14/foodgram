from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Настройки приложения рецептов, тегов и ингредиентов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = 'Рецепты'
