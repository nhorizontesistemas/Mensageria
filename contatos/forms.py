from django import forms

from .models import Contato, ImportJob, Tag


class ContatoForm(forms.ModelForm):
    tags_texto = forms.CharField(
        required=False, label='Tags',
        help_text='Separe por vírgula (ex: vip, promo-agosto)',
    )

    class Meta:
        model = Contato
        fields = ['nome', 'telefone', 'ativo']

    def __init__(self, *args, cliente=None, **kwargs):
        self.cliente = cliente
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tags_texto'].initial = ', '.join(
                self.instance.tags.values_list('nome', flat=True)
            )

    def save(self, commit=True):
        contato = super().save(commit=False)
        contato.cliente = self.cliente
        if commit:
            contato.save()
            self._salvar_tags(contato)
        return contato

    def _salvar_tags(self, contato):
        nomes = [t.strip() for t in self.cleaned_data.get('tags_texto', '').split(',') if t.strip()]
        tags = []
        for nome in nomes:
            tag, _ = Tag.objects.get_or_create(cliente=self.cliente, nome=nome)
            tags.append(tag)
        contato.tags.set(tags)


class ImportJobForm(forms.ModelForm):
    class Meta:
        model = ImportJob
        fields = ['arquivo']
