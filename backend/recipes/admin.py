"""Регистрация моделей recipes в админке."""
from django.contrib import admin
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Список ингредиентов с поиском по названию."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Список рецептов с фильтром по тегам и счётчиком в избранном."""

    list_display = ('name', 'author', 'favorites_count')
    search_fields = ('author', 'name')
    list_filter = ('tags',)

    def favorites_count(self, obj):
        """Считает, сколько раз рецепт добавили в избранное."""
        return obj.favorites_recipes.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Список связей рецепт-ингредиент с количеством."""

    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Список избранных рецептов пользователей."""

    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Список рецептов в корзинах покупок пользователей."""

    list_display = ('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Список тегов рецептов."""

    list_display = ('name', 'slug')
