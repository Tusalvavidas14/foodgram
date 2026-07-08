from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def short_link_redirect(request, id):
    'Редирект короткой ссылки на страницу рецепта'
    get_object_or_404(Recipe, id=id)
    return redirect(f'/recipes/{id}/')