from django.contrib import admin

from .models import Campanha, MensagemCampanha


class MensagemCampanhaInline(admin.TabularInline):
    model = MensagemCampanha
    extra = 1
    fields = ('ordem', 'tipo', 'texto', 'arquivo')


@admin.register(Campanha)
class CampanhaAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'cliente', 'status', 'segmentacao_tipo',
        'limite_envios_dia', 'tamanho_lote', 'data_inicio',
    )
    list_filter = ('status', 'cliente', 'segmentacao_tipo')
    search_fields = ('nome',)
    filter_horizontal = ('instancias', 'segmentacao_tags', 'segmentacao_contatos')
    inlines = [MensagemCampanhaInline]

    fieldsets = (
        ('Geral', {'fields': ('cliente', 'nome', 'status')}),
        ('Instâncias', {'fields': ('instancias', 'round_robin')}),
        ('Público', {'fields': ('segmentacao_tipo', 'segmentacao_tags', 'segmentacao_contatos')}),
        ('Limites e ritmo (anti-bloqueio)', {
            'fields': (
                'limite_envios_dia', 'tamanho_lote',
                'delay_min_segundos', 'delay_max_segundos',
                'pausa_entre_lotes_segundos', 'delay_sequencia_segundos',
            ),
        }),
        ('Agendamento', {
            'fields': ('data_inicio', 'dias_semana_permitidos', 'horario_inicio', 'horario_fim'),
        }),
    )
