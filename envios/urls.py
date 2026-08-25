from django.urls import path

from . import views

urlpatterns = [
    path('processar-fila/', views.cron_processar_fila, name='cron_processar_fila'),
]
