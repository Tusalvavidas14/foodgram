"""Корневые URL-маршруты проекта foodgram_backend."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from recipes.views import short_link_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<int:id>/', short_link_redirect, name='short_link')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
