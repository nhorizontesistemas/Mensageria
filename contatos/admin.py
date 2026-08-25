from django.contrib import admin

from .models import Contato, ImportJob, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente')
    list_filter = ('cliente',)
    search_fields = ('nome',)


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'cliente', 'ativo', 'criado_em')
    list_filter = ('cliente', 'ativo', 'tags')
    search_fields = ('nome', 'telefone')
    filter_horizontal = ('tags',)
    list_per_page = 50


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'cliente', 'status', 'total_linhas', 'total_processadas',
        'total_validos', 'total_duplicados', 'total_invalidos', 'criado_em',
    )
    list_filter = ('status', 'cliente')
    readonly_fields = (
        'total_linhas', 'total_processadas', 'total_validos', 'total_duplicados',
        'total_invalidos', 'relatorio_validos', 'relatorio_duplicados',
        'relatorio_invalidos', 'relatorio_erros', 'erro_mensagem', 'criado_em', 'concluido_em',
    )
