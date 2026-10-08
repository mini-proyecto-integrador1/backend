from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers


class ConflictoSobrecargaSerializer(serializers.Serializer):
    codigo = serializers.CharField(help_text='Siempre "sobrecarga".')
    fecha = serializers.DateField(help_text='Día que se pasaría del límite.')
    limite = serializers.IntegerField(help_text='Límite diario del organizador (horas).')
    planificadas = serializers.FloatField(help_text='Total de horas que quedarían ese día.')
    horas_gestion = serializers.FloatField(help_text='Horas de la gestión que se intenta guardar.')
    exceso = serializers.FloatField(help_text='Horas que se pasan del límite.')
    horas_disponibles = serializers.FloatField(help_text='Límite menos lo que ya había ese día (mínimo 0).')
    dia_sugerido = serializers.DateField(
        allow_null=True,
        help_text='Primer día, desde hoy hasta la fecha del evento, donde la gestión cabe. null si no hay.')


class ConflictosSobrecargaSerializer(serializers.Serializer):
    codigo = serializers.CharField(help_text='Siempre "sobrecarga".')
    conflictos = ConflictoSobrecargaSerializer(many=True)


_EJEMPLO_UN_DIA = {
    'codigo': 'sobrecarga', 'fecha': '2026-10-08', 'limite': 6, 'planificadas': 7,
    'horas_gestion': 2, 'exceso': 1, 'horas_disponibles': 1, 'dia_sugerido': '2026-10-07',
}

RESPUESTA_409 = OpenApiResponse(
    response=ConflictoSobrecargaSerializer,
    description='Sobrecarga: ese día quedaría por encima del límite diario. '
                'No se guarda nada; el cliente reintenta con otra fecha o menos horas.',
    examples=[OpenApiExample('Un día sobrecargado', value=_EJEMPLO_UN_DIA)],
)

RESPUESTA_409_MULTIPLE = OpenApiResponse(
    response=ConflictosSobrecargaSerializer,
    description='Sobrecarga en uno o más días de las gestiones nuevas. No se crea el evento.',
    examples=[OpenApiExample('Varios días sobrecargados',
                             value={'codigo': 'sobrecarga', 'conflictos': [_EJEMPLO_UN_DIA]})],
)