"""Модели рецептов: ингредиенты, теги, рецепты, избранное и корзина."""

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from foodgram_backend.constants import (
    MAX_INGREDIENT_NAME,
    MAX_LENGHT_RECIPE_NAME,
    MAX_RECIPE_DESCRIPTION,
    MAX_SLUG_IN_PROJECT,
    MAX_TAG_NAME,
    MAX_UNIT_LENGHT,
    MIN_COOKING_TIME,
)

User = get_user_model()


class Ingredient(models.Model):
    """Ингредиент из справочника с единицей измерения."""

    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME,
        verbose_name="Ингредиент"
    )
    measurement_unit = models.CharField(
        max_length=MAX_UNIT_LENGHT,
        verbose_name="Единица измерения",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            ),
        ]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Tag(models.Model):
    """Тег, которым можно пометить рецепт (например, «завтрак»)."""

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
    """Рецепт: автор, описание, изображение, ингредиенты и теги."""

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
        validators=[MinValueValidator(MIN_COOKING_TIME)]
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeIngredient(models.Model):
    """Связь рецепта с ингредиентом и его количеством в этом рецепте."""

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


class BaseUserRecipeRelation(models.Model):
    "Родительская модель для классов Favorite и ShoppingCart "

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    pub_date = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(app_label)s_%(class)s_unique_user_recipe'
            ),
        ]


class Favorite(BaseUserRecipeRelation):
    """Отметка «рецепт в избранном» у конкретного пользователя."""
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

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"


class ShoppingCart(BaseUserRecipeRelation):
    """Рецепт в списке покупок конкретного пользователя."""
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

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"
