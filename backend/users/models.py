from django.db import models
from django.contrib.auth.models import AbstractUser

from django.contrib.auth.validators import UnicodeUsernameValidator

from foodgram_backend.constants import MAX_LENGHT_USERNAME, MAX_LENGHT_EMAIL


class User(AbstractUser):
    username = models.CharField(
        max_length=MAX_LENGHT_USERNAME,
        unique=True,
        validators=[UnicodeUsernameValidator()],
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
        null=True)
    email = models.EmailField(unique=True, max_length=MAX_LENGHT_EMAIL)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Follow(models.Model):
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
        unique_together = ["user", "author"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
