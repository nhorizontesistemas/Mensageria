import requests
from django.conf import settings


class ZApiError(Exception):
    pass


def _url(instancia, endpoint):
    return f'{settings.ZAPI_BASE_URL}/instances/{instancia.instance_id}/token/{instancia.token}/{endpoint}'


def _headers(instancia):
    headers = {'Content-Type': 'application/json'}
    if instancia.client_token:
        headers['Client-Token'] = instancia.client_token
    return headers


def _post(instancia, endpoint, payload):
    resp = requests.post(_url(instancia, endpoint), json=payload, headers=_headers(instancia), timeout=30)
    if resp.status_code >= 400:
        raise ZApiError(f'{resp.status_code}: {resp.text[:300]}')
    return resp.json()


def enviar_texto(instancia, telefone, texto):
    return _post(instancia, 'send-text', {'phone': telefone, 'message': texto})


def enviar_imagem(instancia, telefone, url_arquivo, legenda=''):
    return _post(instancia, 'send-image', {'phone': telefone, 'image': url_arquivo, 'caption': legenda})


def enviar_video(instancia, telefone, url_arquivo, legenda=''):
    return _post(instancia, 'send-video', {'phone': telefone, 'video': url_arquivo, 'caption': legenda})


def enviar_audio(instancia, telefone, url_arquivo):
    return _post(instancia, 'send-audio', {'phone': telefone, 'audio': url_arquivo})


def enviar_mensagem(instancia, telefone, mensagem_campanha):
    tipo = mensagem_campanha.tipo
    url_arquivo = mensagem_campanha.arquivo.url if mensagem_campanha.arquivo else None

    if tipo == mensagem_campanha.Tipo.TEXTO:
        return enviar_texto(instancia, telefone, mensagem_campanha.texto)
    if tipo == mensagem_campanha.Tipo.IMAGEM:
        return enviar_imagem(instancia, telefone, url_arquivo, mensagem_campanha.texto)
    if tipo == mensagem_campanha.Tipo.VIDEO:
        return enviar_video(instancia, telefone, url_arquivo, mensagem_campanha.texto)
    if tipo == mensagem_campanha.Tipo.AUDIO:
        return enviar_audio(instancia, telefone, url_arquivo)
    raise ZApiError(f'Tipo de mensagem desconhecido: {tipo}')


def status_instancia(instancia):
    resp = requests.get(
        f'{settings.ZAPI_BASE_URL}/instances/{instancia.instance_id}/token/{instancia.token}/status',
        headers=_headers(instancia), timeout=15,
    )
    if resp.status_code >= 400:
        raise ZApiError(f'{resp.status_code}: {resp.text[:300]}')
    return resp.json()
