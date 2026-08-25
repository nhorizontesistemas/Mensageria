import csv
import io

import openpyxl
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Contato, ImportJob, Tag

DDI_PADRAO = '55'


def normalizar_telefone(bruto):
    digitos = ''.join(ch for ch in str(bruto) if ch.isdigit())

    if not digitos:
        return None, False

    if digitos.startswith('00'):
        digitos = digitos[2:]

    if len(digitos) in (10, 11):
        digitos = DDI_PADRAO + digitos
    elif len(digitos) in (12, 13) and digitos.startswith(DDI_PADRAO):
        pass
    else:
        return digitos, False

    if not (12 <= len(digitos) <= 13):
        return digitos, False

    return digitos, True


def _ler_csv(arquivo):
    conteudo = arquivo.read()
    for encoding in ('utf-8-sig', 'latin-1'):
        try:
            texto = conteudo.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        texto = conteudo.decode('utf-8', errors='replace')

    leitor = csv.DictReader(io.StringIO(texto))
    for linha in leitor:
        yield {(k or '').strip().lower(): v for k, v in linha.items()}


def _ler_xlsx(arquivo):
    wb = openpyxl.load_workbook(arquivo, read_only=True, data_only=True)
    ws = wb.active
    linhas = ws.iter_rows(values_only=True)
    cabecalho = [str(c or '').strip().lower() for c in next(linhas)]
    for linha in linhas:
        if not any(linha):
            continue
        yield dict(zip(cabecalho, linha))


def ler_linhas(import_job):
    nome_arquivo = import_job.arquivo.name.lower()
    import_job.arquivo.open('rb')
    try:
        if nome_arquivo.endswith('.csv'):
            yield from _ler_csv(import_job.arquivo)
        else:
            yield from _ler_xlsx(import_job.arquivo)
    finally:
        import_job.arquivo.close()


def _salvar_csv(job, campo, cabecalho, linhas):
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    getattr(job, campo).save(
        f'{campo}_{job.id}.csv', ContentFile(buffer.getvalue().encode('utf-8-sig')), save=False,
    )


def processar_import_job(job_id):
    job = ImportJob.objects.get(id=job_id)
    job.status = ImportJob.Status.PROCESSANDO
    job.save(update_fields=['status'])

    validos, duplicados, invalidos, erros = [], [], [], []
    vistos = set()

    try:
        linhas = list(ler_linhas(job))
    except Exception as exc:
        job.status = ImportJob.Status.ERRO
        job.erro_mensagem = str(exc)
        job.save(update_fields=['status', 'erro_mensagem'])
        return

    job.total_linhas = len(linhas)
    job.save(update_fields=['total_linhas'])

    for i, linha in enumerate(linhas):
        try:
            nome = str(linha.get('nome') or '').strip()
            telefone_bruto = linha.get('telefone') or linha.get('telefone/whatsapp') or ''
            tags_bruto = str(linha.get('tags') or linha.get('tag') or '').strip()

            numero, valido = normalizar_telefone(telefone_bruto)
            if not valido:
                invalidos.append([nome, telefone_bruto, 'número inválido'])
                continue

            if numero in vistos or Contato.objects.filter(cliente=job.cliente, telefone=numero).exists():
                duplicados.append([nome, numero])
                continue

            vistos.add(numero)
            contato = Contato.objects.create(cliente=job.cliente, nome=nome, telefone=numero)

            if tags_bruto:
                for tag_nome in [t.strip() for t in tags_bruto.split(',') if t.strip()]:
                    tag, _ = Tag.objects.get_or_create(cliente=job.cliente, nome=tag_nome)
                    contato.tags.add(tag)

            validos.append([nome, numero])
        except Exception as exc:
            erros.append([i + 2, str(linha), str(exc)])

        job.total_processadas = i + 1
        if job.total_processadas % 500 == 0:
            job.save(update_fields=['total_processadas'])

    job.total_validos = len(validos)
    job.total_duplicados = len(duplicados)
    job.total_invalidos = len(invalidos)

    _salvar_csv(job, 'relatorio_validos', ['nome', 'telefone'], validos)
    _salvar_csv(job, 'relatorio_duplicados', ['nome', 'telefone'], duplicados)
    _salvar_csv(job, 'relatorio_invalidos', ['nome', 'telefone', 'motivo'], invalidos)
    _salvar_csv(job, 'relatorio_erros', ['linha', 'conteudo', 'erro'], erros)

    job.status = ImportJob.Status.CONCLUIDO
    job.concluido_em = timezone.now()
    job.save()
