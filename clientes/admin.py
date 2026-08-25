from django.contrib import admin

from .models import Cliente, Instancia


class InstanciaInline(admin.TabularInline):
    model = Instancia
    extra = 0
    fields = ('apelido', 'instance_id', 'status', 'pausada_ate')
    readonly_fields = ('ultima_verificacao_em',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'total_instancias', 'link_publico', 'criado_em')
    list_filter = ('ativo',)
    search_fields = ('nome', 'email_contato', 'telefone_contato')
    readonly_fields = ('token_publico', 'criado_em')
    inlines = [InstanciaInline]

    @admin.display(description='Instâncias')
    def total_instancias(self, obj):
        return obj.instancias.count()

    @admin.display(description='Link público')
    def link_publico(self, obj):
        return f'/publico/{obj.token_publico}/'


@admin.register(Instancia)
class InstanciaAdmin(admin.ModelAdmin):
    list_display = ('apelido', 'cliente', 'status', 'pausada_ate', 'ultima_verificacao_em')
    list_filter = ('status', 'cliente')
    search_fields = ('apelido', 'instance_id', 'cliente__nome')
    readonly_fields = ('ultima_verificacao_em', 'criado_em')
