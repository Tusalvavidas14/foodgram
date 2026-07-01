from django.db import models
from django.core.validators import MinValueValidator

from foodgram_backend.constants import (
    MAX_LENGHT_RECIPE_NAME,
    MAX_RECIPE_DESCRIPTION,
    MAX_INGREDIENT_NAME,
    MAX_SLUG_IN_PROJECT,
    MAX_UNIT_LENGHT,
    MAX_TAG_NAME,
)
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME,
        verbose_name="Ингредиент"
    )
    measurement_unit = models.CharField(
        max_length=MAX_UNIT_LENGHT,
        verbose_name="Единица измерения",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_TAG_NAME,
        verbose_name="Название тега"
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_IN_PROJECT,
        unique=True,
        verbose_name="слаг"
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="автор",
    )
    name = models.CharField(
        max_length=MAX_LENGHT_RECIPE_NAME,
        verbose_name="Название",
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name="Изображение"
    )
    text = models.TextField(
        max_length=MAX_RECIPE_DESCRIPTION,
        verbose_name="Описание рецепта"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="ингредиенты"
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipes_ingredient"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                1,
                message='Количество ингредиента не может быть меньше 1'
            )
        ],
        verbose_name="Количество ингредиентов",
    )

    class Meta:
        unique_together = ["recipe", "ingredient"]
        verbose_name = "Рецепт к ингредиенту"
        verbose_name_plural = "Рецепты к ингредиентам"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites_recipes"
    )

    pub_date = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ['user', 'recipe']
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"


class ShoppingCart(models.Model):
    """""Модель корзины покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart"
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_cart"
    )

    pub_date = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ['user', 'recipe']
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"
