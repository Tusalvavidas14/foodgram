"""Пагинация, используемая в эндпоинтах api."""
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Постраничная пагинация с настраиваемым размером страницы (?limit=)."""

    page_size = 6
    page_size_query_param = 'limit'
