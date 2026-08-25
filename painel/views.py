from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from campanhas.forms import CampanhaForm, MensagemCampanhaFormSet
from campanhas.models import Campanha
from clientes.forms import ClienteForm, InstanciaForm
from clientes.models import Cliente, Instancia
from contatos.forms import ContatoForm, ImportJobForm
from contatos.models import Contato, ImportJob
from contatos.services import processar_import_job
from envios.models import Envio
from envios.zapi import ZApiError, status_instancia


class PainelLoginView(LoginView):
    template_name = 'painel/login.html'
    redirect_authenticated_user = True


# ---------- Dashboard ----------

@login_required
def dashboard(request):
    inicio_do_dia = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)

    clientes = []
    for cliente in Cliente.objects.all():
        campanhas_ativas = cliente.campanhas.filter(status=Campanha.Status.ATIVA).count()
        pendentes = Envio.objects.filter(campanha__cliente=cliente, status=Envio.Status.PENDENTE).count()
        processados_hoje = Envio.objects.filter(
            campanha__cliente=cliente, status=Envio.Status.ENVIADO, enviado_em__gte=inicio_do_dia,
        ).count()
        clientes.append({
            'obj': cliente,
            'campanhas_ativas': campanhas_ativas,
            'pendentes': pendentes,
            'processados_hoje': processados_hoje,
            'instancias_total': cliente.instancias.count(),
        })

    return render(request, 'painel/dashboard.html', {'clientes': clientes})


# ---------- Cliente ----------

@login_required
def cliente_detail(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    inicio_do_dia = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)

    campanhas = []
    for campanha in cliente.campanhas.all():
        pendentes = campanha.envios.filter(status=Envio.Status.PENDENTE).count()
        processados_hoje = campanha.envios.filter(status=Envio.Status.ENVIADO, enviado_em__gte=inicio_do_dia).count()
        falhas_hoje = campanha.envios.filter(
            status__in=[Envio.Status.FALHOU, Envio.Status.FALHA_DEFINITIVA], criado_em__gte=inicio_do_dia,
        ).count()
        campanhas.append({
            'obj': campanha, 'pendentes': pendentes,
            'processados_hoje': processados_hoje, 'falhas_hoje': falhas_hoje,
        })

    return render(request, 'painel/cliente_detail.html', {
        'cliente': cliente, 'campanhas': campanhas, 'instancias': cliente.instancias.all(),
        'total_contatos': cliente.contatos.count(),
    })


@login_required
def cliente_create(request):
    form = ClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cliente = form.save()
        messages.success(request, f'Cliente "{cliente.nome}" criado.')
        return redirect('painel:cliente_detail', cliente_id=cliente.id)
    return render(request, 'painel/cliente_form.html', {'form': form, 'titulo': 'Novo cliente'})


@login_required
def cliente_update(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente atualizado.')
        return redirect('painel:cliente_detail', cliente_id=cliente.id)
    return render(request, 'painel/cliente_form.html', {'form': form, 'titulo': cliente.nome, 'cliente': cliente})


# ---------- Instância ----------

@login_required
def instancia_create(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    form = InstanciaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        instancia = form.save(commit=False)
        instancia.cliente = cliente
        instancia.save()
        messages.success(request, f'Instância "{instancia.apelido}" adicionada.')
        return redirect('painel:cliente_detail', cliente_id=cliente.id)
    return render(request, 'painel/instancia_form.html', {'form': form, 'cliente': cliente, 'titulo': 'Nova instância'})


@login_required
def instancia_update(request, cliente_id, instancia_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    instancia = get_object_or_404(Instancia, id=instancia_id, cliente=cliente)
    form = InstanciaForm(request.POST or None, instance=instancia)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Instância atualizada.')
        return redirect('painel:cliente_detail', cliente_id=cliente.id)
    return render(request, 'painel/instancia_form.html', {
        'form': form, 'cliente': cliente, 'instancia': instancia, 'titulo': instancia.apelido,
    })


@login_required
@require_POST
def instancia_delete(request, cliente_id, instancia_id):
    instancia = get_object_or_404(Instancia, id=instancia_id, cliente_id=cliente_id)
    instancia.delete()
    messages.success(request, 'Instância removida.')
    return redirect('painel:cliente_detail', cliente_id=cliente_id)


@login_required
@require_POST
def instancia_testar_conexao(request, cliente_id, instancia_id):
    instancia = get_object_or_404(Instancia, id=instancia_id, cliente_id=cliente_id)
    try:
        dados = status_instancia(instancia)
        conectada = bool(dados.get('connected'))
        instancia.status = Instancia.Status.CONECTADA if conectada else Instancia.Status.DESCONECTADA
        messages.success(request, f'Teste concluído: {instancia.get_status_display()}.')
    except ZApiError as exc:
        instancia.status = Instancia.Status.BANIDA
        messages.error(request, f'Falha ao testar instância: {exc}')
    instancia.ultima_verificacao_em = timezone.now()
    instancia.save(update_fields=['status', 'ultima_verificacao_em'])
    return redirect('painel:cliente_detail', cliente_id=cliente_id)


# ---------- Campanha ----------

@login_required
@require_POST
def campanha_pausar(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    campanha.status = Campanha.Status.PAUSADA
    campanha.save(update_fields=['status'])
    return redirect('painel:cliente_detail', cliente_id=campanha.cliente_id)


@login_required
@require_POST
def campanha_retomar(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    campanha.status = Campanha.Status.ATIVA
    campanha.save(update_fields=['status'])
    return redirect('painel:cliente_detail', cliente_id=campanha.cliente_id)


@login_required
@require_POST
def campanha_cancelar(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)
    campanha.status = Campanha.Status.CANCELADA
    campanha.save(update_fields=['status'])
    return redirect('painel:cliente_detail', cliente_id=campanha.cliente_id)


@login_required
def campanha_create(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    form = CampanhaForm(request.POST or None, cliente=cliente)
    formset = MensagemCampanhaFormSet(request.POST or None, instance=form.instance)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        campanha = form.save()
        formset.instance = campanha
        formset.save()
        messages.success(request, f'Campanha "{campanha.nome}" criada.')
        return redirect('painel:cliente_detail', cliente_id=cliente.id)

    return render(request, 'painel/campanha_form.html', {
        'form': form, 'formset': formset, 'cliente': cliente, 'titulo': 'Nova campanha',
    })


@login_required
def campanha_update(request, cliente_id, campanha_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    campanha = get_object_or_404(Campanha, id=campanha_id, cliente=cliente)
    form = CampanhaForm(request.POST or None, instance=campanha, cliente=cliente)
    formset = MensagemCampanhaFormSet(request.POST or None, instance=campanha)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Campanha atualizada.')
        return redirect('painel:cliente_detail', cliente_id=cliente.id)

    return render(request, 'painel/campanha_form.html', {
        'form': form, 'formset': formset, 'cliente': cliente, 'campanha': campanha, 'titulo': campanha.nome,
    })


# ---------- Contatos ----------

@login_required
def contato_list(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    qs = cliente.contatos.all().prefetch_related('tags')

    tag_id = request.GET.get('tag')
    if tag_id:
        qs = qs.filter(tags__id=tag_id)

    busca = request.GET.get('q')
    if busca:
        qs = qs.filter(nome__icontains=busca) | qs.filter(telefone__icontains=busca)

    paginator = Paginator(qs, 50)
    pagina = paginator.get_page(request.GET.get('page'))

    return render(request, 'painel/contato_list.html', {
        'cliente': cliente, 'pagina': pagina, 'tags': cliente.tags.all(),
        'tag_selecionada': tag_id, 'busca': busca or '',
    })


@login_required
def contato_create(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    form = ContatoForm(request.POST or None, cliente=cliente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contato adicionado.')
        return redirect('painel:contato_list', cliente_id=cliente.id)
    return render(request, 'painel/contato_form.html', {'form': form, 'cliente': cliente, 'titulo': 'Novo contato'})


@login_required
@require_POST
def contato_delete(request, cliente_id, contato_id):
    contato = get_object_or_404(Contato, id=contato_id, cliente_id=cliente_id)
    contato.delete()
    messages.success(request, 'Contato removido.')
    return redirect('painel:contato_list', cliente_id=cliente_id)


# ---------- Importação ----------

@login_required
def importjob_list(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    jobs = cliente.import_jobs.all()
    return render(request, 'painel/importjob_list.html', {'cliente': cliente, 'jobs': jobs})


@login_required
def importjob_create(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    form = ImportJobForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.cliente = cliente
        job.save()
        messages.success(request, 'Arquivo enviado. Processamento entra na fila automaticamente.')
        return redirect('painel:importjob_list', cliente_id=cliente.id)
    return render(request, 'painel/importjob_form.html', {'form': form, 'cliente': cliente})


@login_required
@require_POST
def importjob_processar_agora(request, cliente_id, job_id):
    job = get_object_or_404(ImportJob, id=job_id, cliente_id=cliente_id)
    if job.status == ImportJob.Status.PENDENTE:
        processar_import_job(job.id)
        messages.success(request, 'Importação processada.')
    return redirect('painel:importjob_list', cliente_id=cliente_id)
