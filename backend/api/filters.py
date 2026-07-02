"""Фильтры для эндпоинтов ингредиентов и рецептов."""
from rest_framework.filters import BaseFilterBackend


class IngredientFilter(BaseFilterBackend):
    """Фильтр для ингредиентов по частичному совпадению названия."""

    def filter_queryset(self, request, queryset, view):
        """Оставляет только ингредиенты, чьё название начинается с ?name=."""
        name = request.query_params.get('name')
        if name:
            return queryset.filter(name__istartswith=name)
        return queryset


class RecipeFilter(BaseFilterBackend):
    """Фильтр рецептов по автору, тегам, избранному и списку покупок."""

    def filter_queryset(self, request, queryset, view):
        """Применяет к queryset все переданные в запросе фильтры."""
        author = request.query_params.get('author')
        tags = request.query_params.getlist('tags')
        is_favorited = request.query_params.get('is_favorited')
        is_in_shopping_cart = request.query_params.get('is_in_shopping_cart')

        if author:
            queryset = queryset.filter(author__id=author)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if is_favorited == '1' and request.user.is_authenticated:
            queryset = queryset.filter(favorites_recipes__user=request.user)
        if is_in_shopping_cart == '1' and request.user.is_authenticated:
            queryset = queryset.filter(recipe_cart__user=request.user)

        return queryset
