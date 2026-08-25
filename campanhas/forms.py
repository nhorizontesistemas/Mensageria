from django import forms
from django.forms import inlineformset_factory

from .models import Campanha, MensagemCampanha


class DiasSemanaField(forms.TypedMultipleChoiceField):
    def __init__(self, **kwargs):
        super().__init__(
            choices=Campanha.DiaSemana.choices,
            widget=forms.CheckboxSelectMultiple,
            coerce=int,
            required=False,
            **kwargs,
        )


class CampanhaForm(forms.ModelForm):
    dias_semana_permitidos = DiasSemanaField(
        label='Dias da semana permitidos', help_text='Nenhum marcado = todos os dias.',
    )

    class Meta:
        model = Campanha
        fields = [
            'nome', 'status', 'instancias', 'round_robin',
            'segmentacao_tipo', 'segmentacao_tags', 'segmentacao_contatos',
            'limite_envios_dia', 'tamanho_lote', 'delay_min_segundos', 'delay_max_segundos',
            'pausa_entre_lotes_segundos', 'delay_sequencia_segundos',
            'data_inicio', 'dias_semana_permitidos', 'horario_inicio', 'horario_fim',
        ]
        widgets = {
            'instancias': forms.CheckboxSelectMultiple,
            'segmentacao_tags': forms.CheckboxSelectMultiple,
            'segmentacao_contatos': forms.SelectMultiple(attrs={'size': 8}),
            'data_inicio': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, cliente=None, **kwargs):
        self.cliente = cliente
        super().__init__(*args, **kwargs)
        self.fields['instancias'].required = False
        if cliente is not None:
            self.fields['instancias'].queryset = cliente.instancias.all()
            self.fields['segmentacao_tags'].queryset = cliente.tags.all()
            self.fields['segmentacao_contatos'].queryset = cliente.contatos.all()

    def save(self, commit=True):
        campanha = super().save(commit=False)
        campanha.cliente = self.cliente
        if commit:
            campanha.save()
            self.save_m2m()
        return campanha


MensagemCampanhaFormSet = inlineformset_factory(
    Campanha, MensagemCampanha,
    fields=['ordem', 'tipo', 'texto', 'arquivo'],
    extra=1, can_delete=True,
)
