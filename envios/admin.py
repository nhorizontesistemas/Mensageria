from django.contrib import admin

from .models import EventoFailover, Envio


@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'contato', 'campanha', 'instancia', 'status',
        'tentativas', 'proxima_tentativa_em', 'enviado_em',
    )
    list_filter = ('status', 'campanha', 'instancia')
    search_fields = ('contato__nome', 'contato__telefone')
    readonly_fields = ('criado_em',)
    list_per_page = 50


@admin.register(EventoFailover)
class EventoFailoverAdmin(admin.ModelAdmin):
    list_display = ('instancia', 'taxa_erro', 'criado_em')
    list_filter = ('instancia',)
    readonly_fields = ('criado_em',)
