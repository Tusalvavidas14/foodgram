from django.shortcuts import render
from django.http import HttpResponse

from django.contrib.auth import get_user_model
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404


from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import mixins, viewsets
from .serializers import (TagSerializer, 
                          IngredientSerializer, 
                          UserSerializer, 
                          AvatarSerializer, 
                          UserWithRecipesSerializer, 
                          RecipeListSerializer,
                          RecipeCreateSerializer,
                          RecipeMinifiedSerializer)
from recipes.models import (Tag, 
                     ShoppingCart,
                     Favorite,
                     Ingredient, 
                     RecipeIngredient,
                     Recipe,
                    )

from users.models import Follow
from .permissions import IsAuthorOrReadOnly
from .filters import IngredientFilter, RecipeFilter


User = get_user_model()


class TagViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    
    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    
    queryset = Ingredient.objects.all().order_by('id')
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientFilter,)


class UserViewSet(DjoserUserViewSet):
    lookup_field = 'id'
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    
    def get_permissions(self):
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
        author = get_object_or_404(User, id=id)
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
        authors = User.objects.filter(followers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by('id')
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = (RecipeFilter,)
    
    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=400
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={'request': request})
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
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'рецепт уже есть в корзине'},
                    status=400
                )
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={'request': request})
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
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response
    @action(
            detail=True,
            methods=['get'],
            permission_classes=[permissions.AllowAny],
            url_path='get-link'
    )
    def get_link(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        link = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': link})