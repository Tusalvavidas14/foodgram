from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from foodgram_backend.utils import hashids
from recipes.models import Recipe


def short_link_redirect(request, code):
    decoded = hashids.decode(code)
    if not decoded:
        raise Http404
    recipe = get_object_or_404(Recipe, id=decoded[0])
    return redirect(f'/recipes/{recipe.id}/')
