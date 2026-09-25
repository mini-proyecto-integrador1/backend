from rest_framework import serializers
from .models import Evento, SubtareaLogistica


class SubtareaLogisticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubtareaLogistica
        fields = ['id', 'nombre', 'fecha_limite', 'horas_estimadas', 'estado', 'nota']
        read_only_fields = ['id', 'estado']


class EventoSerializer(serializers.ModelSerializer):
    # Permite mandar la lista de subtareas dentro del mismo POST del evento
    subtareas = SubtareaLogisticaSerializer(many=True, required=False)

    nombre = serializers.CharField(
        error_messages={'blank': 'El nombre del evento es obligatorio.'}
    )
    tipo = serializers.CharField(
        error_messages={'blank': 'El tipo de evento es obligatorio.'}
    )
    
    class Meta:
        model = Evento
        fields = ['id', 'nombre', 'tipo', 'fecha', 'limite_horas_diarias', 'creado_en', 'subtareas']
        read_only_fields = ['id', 'creado_en']

    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError('El nombre del evento es obligatorio.')
        return value

    def validate_tipo(self, value):
        if not value.strip():
            raise serializers.ValidationError('El tipo de evento es obligatorio.')
        return value

    def create(self, validated_data):
        subtareas_data = validated_data.pop('subtareas', [])
        evento = Evento.objects.create(**validated_data)
        for subtarea_data in subtareas_data:
            SubtareaLogistica.objects.create(evento=evento, **subtarea_data)
        return evento