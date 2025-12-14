from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# Redirection automatique vers le login
def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('', redirect_to_login),  #racine redirige vers /login/
    path('admin/', admin.site.urls),
    path('', include('gestion.urls')),  # inclut toutes les urls de ton app "gestion"
]

# Gestion des fichiers media (avatars, uploads...)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
