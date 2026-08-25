from django.db import models

from campanhas.models import Campanha
from clientes.models import Instancia
from contatos.models import Contato


class Envio(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        PROCESSANDO = 'processando', 'Processando'
        ENVIADO = 'enviado', 'Enviado'
        FALHOU = 'falhou', 'Falhou (aguardando nova tentativa)'
        FALHA_DEFINITIVA = 'falha_definitiva', 'Falha definitiva'

    campanha = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name='envios')
    contato = models.ForeignKey(Contato, on_delete=models.CASCADE, related_name='envios')
    instancia = models.ForeignKey(Instancia, on_delete=models.SET_NULL, null=True, blank=True, related_name='envios')

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    tentativas = models.PositiveIntegerField(default=0)
    max_tentativas = models.PositiveIntegerField(default=3)
    proxima_tentativa_em = models.DateTimeField(null=True, blank=True)

    enviado_em = models.DateTimeField(null=True, blank=True)
    erro = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['status', 'proxima_tentativa_em']),
        ]

    def __str__(self):
        return f'{self.contato} — {self.campanha.nome} ({self.status})'


class EventoFailover(models.Model):
    instancia = models.ForeignKey(Instancia, on_delete=models.CASCADE, related_name='eventos_failover')
    motivo = models.TextField()
    taxa_erro = models.FloatField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Failover — {self.instancia} em {self.criado_em:%d/%m/%Y %H:%M}'
