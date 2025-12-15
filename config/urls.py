from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('', redirect_to_login),
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')),
]

# En local uniquement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
