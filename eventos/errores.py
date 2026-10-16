from rest_framework.views import exception_handler as manejador_drf
from .sobrecarga import SobrecargaError

MENSAJE_401 = 'Tu sesión no es válida o expiró. Inicia sesión de nuevo.'
MENSAJE_404 = 'No encontramos lo que buscas.'
MENSAJE_400 = 'Revisa los datos enviados.'


def _primer_mensaje(data):
    """Devuelve el primer texto legible dentro de un error de DRF."""
    if isinstance(data, dict):
        for clave, valor in data.items():
            if clave in ('status', 'message'):
                continue
            mensaje = _primer_mensaje(valor)
            if mensaje:
                return mensaje
    elif isinstance(data, (list, tuple)):
        for valor in data:
            mensaje = _primer_mensaje(valor)
            if mensaje:
                return mensaje
    elif data is not None:
        return str(data)
    return None


def manejador_de_errores(exc, context):
    """
    Llama al manejador de DRF y, en los 400, 401 y 404, conserva las claves
    originales y agrega "status": "error" y "message".
    El 409 de sobrecarga y cualquier otro código se devuelven sin cambios.
    """
    response = manejador_drf(exc, context)
    if response is None:
        return None
    if isinstance(exc, SobrecargaError) or response.status_code not in (400, 401, 404):
        return response

    data = response.data
    cuerpo = dict(data) if isinstance(data, dict) else {'errors': data}

    if response.status_code == 401:
        mensaje = MENSAJE_401
    elif response.status_code == 404:
        mensaje = MENSAJE_404
    else:
        mensaje = _primer_mensaje(data) or MENSAJE_400

    cuerpo['status'] = 'error'
    cuerpo['message'] = mensaje
    response.data = cuerpo
    return response