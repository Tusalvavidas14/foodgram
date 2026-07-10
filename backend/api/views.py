from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram_backend.utils import hashids
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
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeReadSerializer,
    ShoppingCartSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Только чтение списка тегов и отдельного тега."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
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
        methods=['put'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Устанавливает свой аватар."""
        user = request.user
        serializer = AvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def avatar_delete(self, request):
        """Удаляет свой аватар."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=204)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id):
        """Подписывается на автора."""
        author = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id):
        """Отписывается от автора."""
        author = get_object_or_404(User, id=id)
        deleted, _ = Follow.objects.filter(
            user=request.user, author=author
        ).delete()
        if not deleted:
            return Response({'errors': 'Вы не были подписаны'}, status=400)
        return Response(status=204)

    def get_queryset(self):
        """Для subscriptions — только авторы с подпиской.

        Иначе — стандартный queryset.
        """
        if self.action == 'subscriptions':
            return User.objects.filter(
                followers__user=self.request.user
            ).annotate(recipes_count=Count('recipes'))
        return super().get_queryset()

    def get_serializer_class(self):
        """Для subscriptions — сериализатор с рецептами.

        Иначе — стандартный.
        """
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Возвращает постраничный список авторов, на которых подписан."""
        return self.list(request)


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

    def _add_to(self, request, id, serializer_class):
        """Принимает нужный класс и сериализует его как параметр."""
        recipe = get_object_or_404(Recipe, id=id)
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    def _remove_from(self, request, id, model, error_message):
        recipe = get_object_or_404(Recipe, id=id)
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted:
            return Response({'errors': error_message}, status=400)
        return Response(status=204)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, id):
        """Добавляет в избранное."""
        return self._add_to(request, id, FavoriteSerializer)

    @favorite.mapping.delete
    def favorite_delete(self, request, id):
        """Удаляем из избранного."""
        return self._remove_from(
            request, id, Favorite, 'Рецепта нет в избранном'
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, id):
        """Добавляет рецепт из списка покупок."""
        return self._add_to(request, id, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, id):
        """Убираем рецепт из списка покупок."""
        return self._remove_from(
            request, id, ShoppingCart, 'Рецепта нет в корзине'
        )

    def _get_shopping_cart_content(self, user):
        """Формирует текст со сводным списком покупок для пользователя."""
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
        return content

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Отдаёт txt-файл со сводным списком покупок."""
        content = self._get_shopping_cart_content(request.user)
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
        link = request.build_absolute_uri(
            f'/s/{hashids.encode(recipe.id)}/'
        )
        return Response({'short-link': link})
