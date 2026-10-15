from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Count, Q
from rest_framework import serializers
from .models import Evento, SubtareaLogistica


class ProgresoSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    hechas = serializers.IntegerField()
    porcentaje = serializers.FloatField()


class EventoProgresoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    fecha = serializers.DateField()
    progreso = ProgresoSerializer()


class ProgresoGeneralSerializer(serializers.Serializer):
    general = ProgresoSerializer()
    eventos = EventoProgresoSerializer(many=True)


def calcular_progreso(subtareas):
    """hechas / total con un decimal (1 de 3 = 33.3). Las pospuestas cuentan en el total.
    Con 0 subtareas devuelve 0.0, sin dividir por cero."""
    datos = subtareas.aggregate(
        total=Count('id'),
        hechas=Count('id', filter=Q(estado='hecho')),
    )
    total, hechas = datos['total'], datos['hechas']
    if total == 0:
        porcentaje = 0.0
    else:
        exacto = Decimal(hechas) * 100 / Decimal(total)
        porcentaje = float(exacto.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
    return {'total': total, 'hechas': hechas, 'porcentaje': porcentaje}


def progreso_de_usuario(usuario):
    """Resumen de todos los eventos del usuario, con las mismas cifras del detalle."""
    eventos = Evento.objects.filter(usuario=usuario).order_by('fecha')
    return {
        'general': calcular_progreso(SubtareaLogistica.objects.filter(evento__usuario=usuario)),
        'eventos': [
            {'id': e.id, 'nombre': e.nombre, 'fecha': e.fecha,
             'progreso': calcular_progreso(e.subtareas.all())}
            for e in eventos
        ],
    }