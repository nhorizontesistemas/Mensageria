from django.urls import path

from . import views

urlpatterns = [
    path('processar-importacoes/', views.cron_processar_importacoes, name='cron_processar_importacoes'),
]
