from django.db import models

from clientes.models import Cliente, Instancia
from contatos.models import Contato, Tag


class Campanha(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = 'rascunho', 'Rascunho'
        AGENDADA = 'agendada', 'Agendada'
        ATIVA = 'ativa', 'Ativa'
        PAUSADA = 'pausada', 'Pausada'
        CONCLUIDA = 'concluida', 'Concluída'
        CANCELADA = 'cancelada', 'Cancelada'

    class Segmentacao(models.TextChoices):
        TODOS = 'todos', 'Todos os contatos'
        TAG = 'tag', 'Por tag'
        LISTA = 'lista', 'Lista específica'

    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 0, 'Segunda'
        TERCA = 1, 'Terça'
        QUARTA = 2, 'Quarta'
        QUINTA = 3, 'Quinta'
        SEXTA = 4, 'Sexta'
        SABADO = 5, 'Sábado'
        DOMINGO = 6, 'Domingo'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='campanhas')
    nome = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)

    instancias = models.ManyToManyField(Instancia, related_name='campanhas')
    round_robin = models.BooleanField(default=True, help_text='Intercalar envios entre as instâncias vinculadas.')

    segmentacao_tipo = models.CharField(max_length=10, choices=Segmentacao.choices, default=Segmentacao.TODOS)
    segmentacao_tags = models.ManyToManyField(Tag, blank=True, related_name='campanhas')
    segmentacao_contatos = models.ManyToManyField(Contato, blank=True, related_name='campanhas_lista')

    limite_envios_dia = models.PositiveIntegerField(default=500)
    tamanho_lote = models.PositiveIntegerField(default=5, help_text='Mensagens disparadas seguidas antes de pausar.')
    delay_min_segundos = models.PositiveIntegerField(default=3, help_text='Delay mínimo entre mensagens do mesmo lote.')
    delay_max_segundos = models.PositiveIntegerField(default=8, help_text='Delay máximo entre mensagens do mesmo lote.')
    pausa_entre_lotes_segundos = models.PositiveIntegerField(default=120, help_text='Descanso entre uma rajada e a próxima.')
    delay_sequencia_segundos = models.PositiveIntegerField(
        default=3, help_text='Intervalo entre os itens de uma mesma mensagem (texto → imagem → vídeo) para um contato.',
    )

    data_inicio = models.DateTimeField(null=True, blank=True)
    dias_semana_permitidos = models.JSONField(
        default=list, blank=True,
        help_text='Lista de dias permitidos (0=Segunda .. 6=Domingo). Vazio = todos os dias.',
    )
    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fim = models.TimeField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.nome} ({self.cliente.nome})'


class MensagemCampanha(models.Model):
    class Tipo(models.TextChoices):
        TEXTO = 'texto', 'Texto'
        IMAGEM = 'imagem', 'Imagem'
        VIDEO = 'video', 'Vídeo'
        AUDIO = 'audio', 'Áudio'

    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name='mensagens')
    ordem = models.PositiveIntegerField(default=0)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    texto = models.TextField(blank=True, help_text='Legenda ou corpo do texto (usado em texto/imagem/vídeo).')
    arquivo = models.FileField(upload_to='campanhas/midias/', blank=True, null=True)

    class Meta:
        ordering = ['campanha', 'ordem']

    def __str__(self):
        return f'{self.campanha.nome} — item {self.ordem} ({self.tipo})'
