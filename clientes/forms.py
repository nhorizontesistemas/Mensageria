from django import forms

from .models import Cliente, Instancia


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'email_contato', 'telefone_contato', 'ativo']


class InstanciaForm(forms.ModelForm):
    class Meta:
        model = Instancia
        fields = [
            'apelido', 'instance_id', 'token', 'client_token',
            'janela_amostra', 'limite_taxa_erro', 'pausa_pos_failover_minutos',
        ]
