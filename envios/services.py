import random
import time

from django.db.models import Q
from django.utils import timezone

from campanhas.models import Campanha
from clientes.models import Instancia

from . import zapi
from .models import EventoFailover, Envio

BACKOFF_MINUTOS = [5, 15, 30]


def campanha_dentro_da_janela(campanha):
    agora = timezone.localtime()

    if campanha.data_inicio and agora < campanha.data_inicio:
        return False
    if campanha.dias_semana_permitidos and agora.weekday() not in campanha.dias_semana_permitidos:
        return False
    if campanha.horario_inicio and agora.time() < campanha.horario_inicio:
        return False
    if campanha.horario_fim and agora.time() > campanha.horario_fim:
        return False
    return True


def envios_hoje(campanha):
    inicio_do_dia = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    return Envio.objects.filter(
        campanha=campanha, status=Envio.Status.ENVIADO, enviado_em__gte=inicio_do_dia,
    ).count()


def _proxima_instancia(campanha, ultimo_id):
    disponiveis = [i for i in campanha.instancias.all() if i.disponivel()]
    if not disponiveis:
        return None
    if not campanha.round_robin or ultimo_id is None:
        return disponiveis[0]
    ids = [i.id for i in disponiveis]
    try:
        pos = ids.index(ultimo_id)
        return disponiveis[(pos + 1) % len(disponiveis)]
    except ValueError:
        return disponiveis[0]


def verificar_failover(instancia):
    recentes = Envio.objects.filter(
        instancia=instancia, status__in=[Envio.Status.ENVIADO, Envio.Status.FALHA_DEFINITIVA, Envio.Status.FALHOU],
    ).order_by('-criado_em')[:instancia.janela_amostra]

    if len(recentes) < instancia.janela_amostra:
        return

    falhas = sum(1 for e in recentes if e.status != Envio.Status.ENVIADO)
    taxa = falhas / len(recentes)

    if taxa >= instancia.limite_taxa_erro:
        instancia.status = Instancia.Status.PAUSADA
        instancia.pausada_ate = timezone.now() + timezone.timedelta(minutes=instancia.pausa_pos_failover_minutos)
        instancia.save(update_fields=['status', 'pausada_ate'])
        EventoFailover.objects.create(
            instancia=instancia, motivo='Taxa de erro acima do limite configurado.', taxa_erro=taxa,
        )


def _enviar_sequencia(envio, instancia):
    mensagens = list(envio.campanha.mensagens.order_by('ordem'))
    for idx, msg in enumerate(mensagens):
        zapi.enviar_mensagem(instancia, envio.contato.telefone, msg)
        if idx < len(mensagens) - 1 and envio.campanha.delay_sequencia_segundos:
            time.sleep(envio.campanha.delay_sequencia_segundos)


def _marcar_falha(envio, mensagem_erro):
    envio.tentativas += 1
    envio.erro = mensagem_erro
    if envio.tentativas >= envio.max_tentativas:
        envio.status = Envio.Status.FALHA_DEFINITIVA
        envio.proxima_tentativa_em = None
    else:
        minutos = BACKOFF_MINUTOS[min(envio.tentativas - 1, len(BACKOFF_MINUTOS) - 1)]
        envio.status = Envio.Status.FALHOU
        envio.proxima_tentativa_em = timezone.now() + timezone.timedelta(minutes=minutos)
    envio.save()


def processar_campanha(campanha):
    if not campanha_dentro_da_janela(campanha):
        return 0

    restante_hoje = campanha.limite_envios_dia - envios_hoje(campanha)
    if restante_hoje <= 0:
        return 0

    tamanho_lote = min(campanha.tamanho_lote, restante_hoje)
    agora = timezone.now()

    pendentes = Envio.objects.filter(
        campanha=campanha,
    ).filter(
        Q(status=Envio.Status.PENDENTE) | Q(status=Envio.Status.FALHOU, proxima_tentativa_em__lte=agora),
    ).order_by('criado_em')[:tamanho_lote]

    ultimo_instancia_id = None
    processados = 0

    for envio in pendentes:
        instancia = _proxima_instancia(campanha, ultimo_instancia_id)
        if instancia is None:
            break
        ultimo_instancia_id = instancia.id

        envio.status = Envio.Status.PROCESSANDO
        envio.instancia = instancia
        envio.save(update_fields=['status', 'instancia'])

        try:
            _enviar_sequencia(envio, instancia)
        except zapi.ZApiError as exc:
            _marcar_falha(envio, str(exc))
        else:
            envio.status = Envio.Status.ENVIADO
            envio.enviado_em = timezone.now()
            envio.erro = ''
            envio.save(update_fields=['status', 'enviado_em', 'erro'])

        verificar_failover(instancia)
        processados += 1

        if processados < len(pendentes):
            time.sleep(random.uniform(campanha.delay_min_segundos, campanha.delay_max_segundos))

    return processados


def processar_fila():
    total = 0
    for campanha in Campanha.objects.filter(status=Campanha.Status.ATIVA):
        total += processar_campanha(campanha)
    return total
