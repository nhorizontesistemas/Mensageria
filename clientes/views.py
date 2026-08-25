from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from envios.models import Envio

from .models import Cliente


def painel_publico(request, token):
    cliente = get_object_or_404(Cliente, token_publico=token, ativo=True)

    inicio_do_dia = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    envios_hoje = Envio.objects.filter(campanha__cliente=cliente, criado_em__gte=inicio_do_dia)

    enviadas_hoje = envios_hoje.filter(status=Envio.Status.ENVIADO).count()
    falhas_hoje = envios_hoje.filter(status__in=[Envio.Status.FALHOU, Envio.Status.FALHA_DEFINITIVA]).count()
    total_hoje = envios_hoje.count()

    por_campanha = (
        envios_hoje.values('campanha__nome')
        .order_by('campanha__nome')
        .distinct()
    )
    resumo_campanhas = []
    for item in por_campanha:
        nome = item['campanha__nome']
        qs = envios_hoje.filter(campanha__nome=nome)
        resumo_campanhas.append({
            'nome': nome,
            'enviadas': qs.filter(status=Envio.Status.ENVIADO).count(),
            'falhas': qs.filter(status__in=[Envio.Status.FALHOU, Envio.Status.FALHA_DEFINITIVA]).count(),
        })

    contexto = {
        'cliente': cliente,
        'enviadas_hoje': enviadas_hoje,
        'falhas_hoje': falhas_hoje,
        'total_hoje': total_hoje,
        'resumo_campanhas': resumo_campanhas,
    }
    return render(request, 'publico/painel.html', contexto)
