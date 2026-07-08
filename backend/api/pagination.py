"""Пагинация, используемая в эндпоинтах api."""
from rest_framework.pagination import PageNumberPagination

from foodgram_backend.constants import PAGE_SIZE


class Paginator(PageNumberPagination):
    """Постраничная пагинация с настраиваемым размером страницы (?limit=)."""

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
