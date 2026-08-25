import uuid

from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    email_contato = models.EmailField(blank=True)
    telefone_contato = models.CharField(max_length=32, blank=True)
    ativo = models.BooleanField(default=True)
    token_publico = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Instancia(models.Model):
    class Status(models.TextChoices):
        CONECTADA = 'conectada', 'Conectada'
        DESCONECTADA = 'desconectada', 'Desconectada'
        BANIDA = 'banida', 'Banida/erro'
        PAUSADA = 'pausada', 'Pausada (failover)'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='instancias')
    apelido = models.CharField(max_length=100)
    instance_id = models.CharField(max_length=100)
    token = models.CharField(max_length=200)
    client_token = models.CharField(
        max_length=200, blank=True,
        help_text='Token de segurança da conta Z-API (Client-Token), se configurado.',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DESCONECTADA)
    pausada_ate = models.DateTimeField(null=True, blank=True)
    ultima_verificacao_em = models.DateTimeField(null=True, blank=True)

    janela_amostra = models.PositiveIntegerField(
        default=20, help_text='Quantos envios recentes analisar para calcular a taxa de erro.',
    )
    limite_taxa_erro = models.FloatField(
        default=0.3, help_text='Taxa de falha (0-1) na amostra que aciona a pausa automática.',
    )
    pausa_pos_failover_minutos = models.PositiveIntegerField(
        default=30, help_text='Minutos que a instância fica pausada após acionar o failover.',
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['cliente__nome', 'apelido']

    def __str__(self):
        return f'{self.apelido} ({self.cliente.nome})'

    def disponivel(self):
        from django.utils import timezone

        if self.status == self.Status.BANIDA:
            return False
        if self.status == self.Status.PAUSADA:
            if self.pausada_ate and self.pausada_ate <= timezone.now():
                return True
            return False
        return True
