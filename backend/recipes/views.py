from django.shortcuts import redirect

from foodgram_backend.utils import hashids
from recipes.models import Recipe


def short_link_redirect(request, code):
    decoded = hashids.decode(code)
    if not decoded or not Recipe.objects.filter(id=decoded[0]).exists():
        return redirect('/not_found/')
    return redirect(f'/recipes/{decoded[0]}/')
