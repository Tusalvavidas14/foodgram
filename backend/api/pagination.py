from rest_framework.pagination import PageNumberPagination

from foodgram_backend.constants import PAGE_SIZE, PAGE_SIZE_QUERY_PARAM


class Paginator(PageNumberPagination):
    """Постраничная пагинация с настраиваемым размером страницы (?limit=)."""

    page_size = PAGE_SIZE
    page_size_query_param = PAGE_SIZE_QUERY_PARAM
