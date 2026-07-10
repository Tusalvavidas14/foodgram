from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Follow

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Пользователи с поиском по имени/email и расширенной формой создания."""

    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    fieldsets = BaseUserAdmin.fieldsets
    list_filter = ('is_staff', 'is_superuser')
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Данные пользователя', {
            'fields': (
                'username', 'first_name', 'last_name', 'email', 'password',
            ),
        }),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Список подписок пользователей друг на друга."""

    list_display = ('user', 'author')
