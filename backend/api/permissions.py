"""Права доступа, используемые в эндпоинтах api."""
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешает изменять и удалять рецепт только его автору."""

    def has_object_permission(self, request, view, obj):
        """Разрешает безопасные методы всем, остальные — только автору."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
