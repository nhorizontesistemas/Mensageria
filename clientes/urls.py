from django.urls import path

from . import views

urlpatterns = [
    path('<uuid:token>/', views.painel_publico, name='painel_publico'),
]
