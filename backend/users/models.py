from django.contrib.auth.models import AbstractUser
from django.db import models

from foodgram_backend.constants import MAX_LENGHT_EMAIL, MAX_LENGHT_USERNAME
from users.validators import validate_username


class User(AbstractUser):
    """Пользователь foodgram, авторизуется по email."""

    username = models.CharField(
        max_length=MAX_LENGHT_USERNAME,
        unique=True,
        validators=[validate_username],
        verbose_name='Имя пользователя'
    )
    first_name = models.CharField(
        max_length=MAX_LENGHT_USERNAME
    )
    last_name = models.CharField(
        max_length=MAX_LENGHT_USERNAME,
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )
    email = models.EmailField(unique=True, max_length=MAX_LENGHT_EMAIL)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        """Возвращает username — удобно для админки и логов."""
        return self.username


class Follow(models.Model):
    """Подписка одного пользователя на другого (автора рецептов)."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Подписка"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="автор",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
