from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .services import processar_fila


def _autorizado(request):
    enviado = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
    return enviado == settings.CRON_SECRET


@csrf_exempt
@require_GET
def cron_processar_fila(request):
    if not _autorizado(request):
        return JsonResponse({'erro': 'não autorizado'}, status=401)

    total = processar_fila()
    return JsonResponse({'processados': total})
