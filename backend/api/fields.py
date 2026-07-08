import base64

from django.core.files.base import ContentFile

from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Поле изображения, принимающее файл в виде base64-строки."""

    def to_internal_value(self, data):
        """Декодирует data:image/...;base64,... в файл перед валидацией."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'image.{ext}'
            )
        return super().to_internal_value(data)