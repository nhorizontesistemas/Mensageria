from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .models import ImportJob
from .services import processar_import_job


def _autorizado(request):
    enviado = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
    return enviado == settings.CRON_SECRET


@csrf_exempt
@require_GET
def cron_processar_importacoes(request):
    if not _autorizado(request):
        return JsonResponse({'erro': 'não autorizado'}, status=401)

    job = ImportJob.objects.filter(status=ImportJob.Status.PENDENTE).order_by('criado_em').first()
    if not job:
        return JsonResponse({'processado': None})

    processar_import_job(job.id)
    return JsonResponse({'processado': job.id})
