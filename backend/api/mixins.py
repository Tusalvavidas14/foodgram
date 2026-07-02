"""Переиспользуемые миксины для сериализаторов и вьюсетов api."""
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response


class PatchModelMixin:
    """Обеспечивает частичную модификацию объекта (`PATCH`)."""

    def partial_update(self, request, *args, **kwargs):
        """Частично обновляет объект и возвращает его данные в ответе."""
        instance = self.get_object()
        partial = True
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class UsernameValidationMixin:
    """Миксин, добавляющий валидацию поля username."""

    def validate_username(self, value):
        """Запрещает регистрацию с зарезервированным именем "me"."""
        if value.lower() == 'me':
            raise serializers.ValidationError('Использовать "me" запрещено.')
        return value


class BaseCRUDViewSet(
    PatchModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """Базовый вьюсет с созданием, чтением, обновлением и удалением."""
