"""Вьюсеты api: теги, ингредиенты, пользователи и рецепты."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)

User = get_user_model()


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Только чтение списка тегов и отдельного тега."""

    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Только чтение списка ингредиентов с поиском по названию."""

    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(DjoserUserViewSet):
    """Пользователи: профиль, аватар и подписки на других авторов."""

    lookup_field = 'id'
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer

    def get_permissions(self):
        """Список, просмотр и регистрация открыты всем.

        Остальные действия — только для авторизованных пользователей.
        """
        if self.action in ('list', 'retrieve', 'create'):
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Устанавливает (PUT) или удаляет (DELETE) свой аватар."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        user.avatar.delete()
        user.avatar = None
        user.save()
        return Response(status=204)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id):
        """Подписывает (POST) или отписывает (DELETE) от указанного автора."""
        author = get_object_or_404(
            User.objects.annotate(recipes_count=Count('recipes')), id=id
        )
        if request.method == 'POST':
            if request.user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на себя'},
                    status=400
                )
            if Follow.objects.filter(
                user=request.user, author=author
            ).exists():
                return Response(
                    {'errors': 'Уже подписаны'},
                    status=400
                )
            Follow.objects.create(user=request.user, author=author)
            serializer = UserWithRecipesSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=201)

        follow = Follow.objects.filter(user=request.user, author=author)
        if not follow.exists():
            return Response(
                {'errors': 'Вы не были подписаны'},
                status=400
            )
        follow.delete()
        return Response(status=204)

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает постраничный список авторов, на которых подписан юзер."""
        authors = User.objects.filter(
            followers__user=request.user
        ).annotate(recipes_count=Count('recipes'))
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты: CRUD, избранное, список покупок и короткая ссылка."""

    queryset = Recipe.objects.all().order_by('id')
    lookup_field = 'id'
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,
    ]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Для create/partial_update — сериализатор записи, иначе чтения."""
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        """Привязывает создаваемый рецепт к текущему пользователю."""
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, id):
        """Добавляет (POST) или убирает (DELETE) рецепт из избранного."""
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'POST':
            if Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=400
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=201)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'errors': 'Рецепта нет в избранном'},
                status=400
            )
        favorite.delete()
        return Response(status=204)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, id):
        """Добавляет (POST) или убирает (DELETE) рецепт из списка покупок."""
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'рецепт уже есть в корзине'},
                    status=400
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=201)
        cart = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
        if not cart.exists():
            return Response(
                {'errors': 'Рецепта нет в корзине'},
                status=400
            )
        cart.delete()
        return Response(status=204)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Формирует и отдаёт txt-файл со сводным списком покупок."""
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__recipe_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )
        content = 'Список покупок:\n\n'
        for item in ingredients:
            content += (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}\n"
            )
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[permissions.AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, id):
        """Возвращает короткую ссылку на страницу рецепта."""
        recipe = get_object_or_404(Recipe, id=id)
        link = request.build_absolute_uri(f'/s/{recipe.id}/')
        return Response({'short-link': link})
