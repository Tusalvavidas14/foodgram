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


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    validate_min = True
    extra = 1


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
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        """Считает, сколько раз рецепт добавили в избранное."""
        return obj.favorites_recipes.count()


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
