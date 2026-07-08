"""Права доступа, используемые в эндпоинтах api."""
from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS, BasePermission

class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешает изменять и удалять рецепт только его автору."""

    def has_object_permission(self, request, view, obj):
        """Разрешает безопасные методы всем, остальные — только автору."""
        return (
            request.method in SAFE_METHODS
            or request.user == obj.author
        )
