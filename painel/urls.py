from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'painel'

urlpatterns = [
    path('login/', views.PainelLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('senha/', views.PainelPasswordChangeView.as_view(), name='password_change'),
    path('', views.dashboard, name='dashboard'),

    path('cliente/novo/', views.cliente_create, name='cliente_create'),
    path('cliente/<int:cliente_id>/', views.cliente_detail, name='cliente_detail'),
    path('cliente/<int:cliente_id>/editar/', views.cliente_update, name='cliente_update'),

    path('cliente/<int:cliente_id>/instancia/nova/', views.instancia_create, name='instancia_create'),
    path('cliente/<int:cliente_id>/instancia/<int:instancia_id>/editar/', views.instancia_update, name='instancia_update'),
    path('cliente/<int:cliente_id>/instancia/<int:instancia_id>/remover/', views.instancia_delete, name='instancia_delete'),
    path('cliente/<int:cliente_id>/instancia/<int:instancia_id>/testar/', views.instancia_testar_conexao, name='instancia_testar_conexao'),

    path('cliente/<int:cliente_id>/campanha/nova/', views.campanha_create, name='campanha_create'),
    path('cliente/<int:cliente_id>/campanha/<int:campanha_id>/editar/', views.campanha_update, name='campanha_update'),
    path('campanha/<int:campanha_id>/pausar/', views.campanha_pausar, name='campanha_pausar'),
    path('campanha/<int:campanha_id>/retomar/', views.campanha_retomar, name='campanha_retomar'),
    path('campanha/<int:campanha_id>/cancelar/', views.campanha_cancelar, name='campanha_cancelar'),

    path('cliente/<int:cliente_id>/contatos/', views.contato_list, name='contato_list'),
    path('cliente/<int:cliente_id>/contatos/novo/', views.contato_create, name='contato_create'),
    path('cliente/<int:cliente_id>/contatos/<int:contato_id>/remover/', views.contato_delete, name='contato_delete'),

    path('cliente/<int:cliente_id>/importacoes/', views.importjob_list, name='importjob_list'),
    path('cliente/<int:cliente_id>/importacoes/nova/', views.importjob_create, name='importjob_create'),
    path('cliente/<int:cliente_id>/importacoes/<int:job_id>/processar/', views.importjob_processar_agora, name='importjob_processar_agora'),
]
