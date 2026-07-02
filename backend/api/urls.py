"""URL-маршруты api: роутер DRF для тегов, пользователей и рецептов."""
from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'users', UserViewSet, basename='users')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
]
