from django.db.models import prefetch_related_objects
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response


class PatchModelMixin:
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        queryset = self.filter_queryset(self.get_queryset())
        if queryset._prefetch_related_lookups:
            instance._prefetched_objects_cache = {}
            prefetch_related_objects(
                [instance], *queryset._prefetch_related_lookups
            )
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


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
