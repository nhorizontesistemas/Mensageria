from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('publico/', include('clientes.urls')),
    path('cron/', include('envios.urls')),
    path('cron/', include('contatos.urls')),
    path('painel/', include('painel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'painel.views.handler_404'
