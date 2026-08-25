from django.db import models

from clientes.models import Cliente


class Tag(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='tags')
    nome = models.CharField(max_length=60)

    class Meta:
        unique_together = ('cliente', 'nome')
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Contato(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contatos')
    nome = models.CharField(max_length=200, blank=True)
    telefone = models.CharField(max_length=20, help_text='Formato normalizado: DDI+DDD+número, só dígitos.')
    tags = models.ManyToManyField(Tag, blank=True, related_name='contatos')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'telefone')
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.nome or "sem nome"} ({self.telefone})'


class ImportJob(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        PROCESSANDO = 'processando', 'Processando'
        CONCLUIDO = 'concluido', 'Concluído'
        ERRO = 'erro', 'Erro'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='import_jobs')
    arquivo = models.FileField(upload_to='importacoes/origem/')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)

    total_linhas = models.PositiveIntegerField(default=0)
    total_processadas = models.PositiveIntegerField(default=0)
    total_validos = models.PositiveIntegerField(default=0)
    total_duplicados = models.PositiveIntegerField(default=0)
    total_invalidos = models.PositiveIntegerField(default=0)

    relatorio_validos = models.FileField(upload_to='importacoes/relatorios/', blank=True, null=True)
    relatorio_duplicados = models.FileField(upload_to='importacoes/relatorios/', blank=True, null=True)
    relatorio_invalidos = models.FileField(upload_to='importacoes/relatorios/', blank=True, null=True)
    relatorio_erros = models.FileField(upload_to='importacoes/relatorios/', blank=True, null=True)

    erro_mensagem = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    concluido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'Importação {self.id} — {self.cliente.nome} ({self.status})'
