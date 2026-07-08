"""Сериализаторы api: пользователи, теги, ингредиенты и рецепты."""
from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега рецепта."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента из справочника."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя с флагом подписки текущего юзера."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на автора obj."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта для избранного, корзины и подписок."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Ингредиент внутри рецепта вместе с его количеством."""

    name = serializers.SlugRelatedField(
        source='ingredient', slug_field='name', read_only=True
    )
    measurement_unit = serializers.SlugRelatedField(
        source='ingredient', slug_field='measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Полное представление рецепта для чтения (список/детали)."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipes_ingredient'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном у текущего юзера."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, лежит ли рецепт в корзине покупок текущего юзера."""
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )


class IngredientCreateSerializer(serializers.Serializer):
    """Ингредиент и его количество при создании/редактировании рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и редактирования рецепта."""

    ingredients = IngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def _set_ingredients(self, recipe, ingredients):
        """Оптимизирует запросы с помощью Django ORM."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients
        )

    def create(self, validated_data):
        """Создаёт рецепт вместе с его тегами и ингредиентами."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт, полностью пересобирая теги и ингредиенты."""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        recipe = super().update(instance, validated_data)

        if tags is not None:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients is not None:
            recipe.recipes_ingredient.all().delete()
            self._set_ingredients(recipe, ingredients)
        return recipe

    def validate_tags(self, value):
        """Проверяет, что теги указаны и не повторяются."""
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один тег.')
        elif len(value) != len(set(tag.id for tag in value)):
            raise serializers.ValidationError('Тег не может повторяться.')
        return value

    def validate_ingredients(self, value):
        """Проверяет, что ингредиенты указаны и не повторяются."""
        if not value:
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент.'
            )

        ids = []
        for item in value:
            ids.append(item['id'].id)

        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Ингредиенты дублируются.')
        return value

    def validate(self, data):
        """Проверяет, что теги и ингредиенты присутствуют в запросе."""
        if self.instance is None:  # создание рецепта
            if 'ingredients' not in data:
                raise serializers.ValidationError(
                    {'ingredients': 'Обязательное поле'}
                )
            if 'tags' not in data:
                raise serializers.ValidationError(
                    {'tags': 'Обязательное поле'}
                )
        else:  # частичное обновление рецепта
            if 'ingredients' not in data:
                raise serializers.ValidationError(
                    {'ingredients': 'Обязательное поле'}
                )
            if 'tags' not in data:
                raise serializers.ValidationError(
                    {'tags': 'Обязательное поле.'}
                )
        return data

    def to_representation(self, instance):
        """Отдаёт рецепт в формате чтения после создания/обновления."""
        return RecipeReadSerializer(instance, context=self.context).data


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор регистрации нового пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для смены аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserWithRecipesSerializer(UserSerializer):
    """Профиль автора вместе с его рецептами — для страницы подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    def get_recipes(self, obj):
        """Отдаёт рецепты автора, урезанные по ?recipes_limit=, если задан."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:min(int(recipes_limit), 10**9)]
        return RecipeMinifiedSerializer(
            queryset,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов автора."""
        return obj.recipes.count()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
