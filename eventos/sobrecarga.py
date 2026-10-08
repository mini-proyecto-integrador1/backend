"""
Lógica de límite diario y sobrecarga (Sprint 3, C2 y C3).
Los tres endpoints que validan sobrecarga usan estas mismas funciones,
para que las cifras sean siempre iguales.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException

from .models import PerfilOrganizador, SubtareaLogistica

LIMITE_POR_DEFECTO = 6
ESTADOS_QUE_CUENTAN = ('pendiente', 'pospuesto')  # las 'hecho' no suman horas
CERO = Decimal('0')


class SobrecargaError(APIException):
    """Responde 409 con el cuerpo exacto que espera el frontend."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Sobrecarga de horas.'
    default_code = 'sobrecarga'

    def __init__(self, cuerpo):
        self.detail = cuerpo


def limite_de(usuario):
    """Límite diario del organizador; 6 si todavía no tiene perfil."""
    perfil = PerfilOrganizador.objects.filter(usuario=usuario).first()
    return perfil.limite_horas_diarias if perfil else LIMITE_POR_DEFECTO


def _num(valor):
    """7.00 -> 7 ; 1.50 -> 1.5 (para que el JSON salga como número)."""
    valor = Decimal(valor)
    return int(valor) if valor == valor.to_integral_value() else float(valor)


def _cargas_por_dia(usuario, desde, hasta, excluir_id=None):
    """{fecha: horas} de las gestiones pendientes/pospuestas de TODOS sus eventos."""
    consulta = SubtareaLogistica.objects.filter(
        evento__usuario=usuario,
        estado__in=ESTADOS_QUE_CUENTAN,
        fecha_limite__range=(desde, hasta),
    )
    if excluir_id is not None:
        consulta = consulta.exclude(pk=excluir_id)
    filas = consulta.values('fecha_limite').annotate(total=Sum('horas_estimadas'))
    return {fila['fecha_limite']: fila['total'] for fila in filas}


def calcular_conflicto(usuario, fecha, horas_gestion, fecha_evento, *,
                       excluir_id=None, carga_extra=None, limite=None):
    """
    Devuelve None si la gestión cabe en `fecha`, o el diccionario del 409.
    - excluir_id: la gestión que se está editando (no se cuenta dos veces).
    - carga_extra: {fecha: horas} de gestiones nuevas aún sin guardar (POST de eventos).
    """
    limite = limite if limite is not None else limite_de(usuario)
    horas_gestion = Decimal(horas_gestion)
    hoy = timezone.localdate()

    cargas = _cargas_por_dia(usuario, min(hoy, fecha), max(fecha_evento, fecha), excluir_id)
    ya_planificado = cargas.get(fecha, CERO)
    planificadas = ya_planificado + horas_gestion
    if planificadas <= limite:
        return None

    # primer día desde hoy hasta la fecha del evento donde cabe (distinto al día en conflicto)
    sugerido = None
    dia = hoy
    while dia <= fecha_evento:
        if dia != fecha:
            ocupado = cargas.get(dia, CERO) + (carga_extra or {}).get(dia, CERO)
            if ocupado + horas_gestion <= limite:
                sugerido = dia
                break
        dia += timedelta(days=1)

    return {
        'codigo': 'sobrecarga',
        'fecha': fecha.isoformat(),
        'limite': limite,
        'planificadas': _num(planificadas),
        'horas_gestion': _num(horas_gestion),
        'exceso': _num(planificadas - limite),
        'horas_disponibles': _num(max(limite - ya_planificado, CERO)),
        'dia_sugerido': sugerido.isoformat() if sugerido else None,
    }


def conflictos_de_gestiones_nuevas(usuario, gestiones, fecha_evento):
    """Para POST /api/eventos/: un conflicto por cada día que se pasa del límite."""
    limite = limite_de(usuario)
    por_dia = {}
    for g in gestiones:
        por_dia[g['fecha_limite']] = por_dia.get(g['fecha_limite'], CERO) + Decimal(g['horas_estimadas'])

    conflictos = []
    for fecha in sorted(por_dia):
        conflicto = calcular_conflicto(usuario, fecha, por_dia[fecha], fecha_evento,
                                       carga_extra=por_dia, limite=limite)
        if conflicto:
            conflictos.append(conflicto)
    return conflictos