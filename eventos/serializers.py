import re
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Evento, SubtareaLogistica, PerfilOrganizador

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

    def update(self, validated_data_instance, validated_data):
        # Las subtareas se editan por sus propios endpoints, aqui se ignoran
        validated_data.pop('subtareas', None)
        return super().update(validated_data_instance, validated_data)

class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    fecha_nacimiento = serializers.DateField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'fecha_nacimiento']
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe una cuenta registrada con este email.')
        return value

    def create(self, validated_data):
        fecha_nacimiento = validated_data.pop('fecha_nacimiento')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        PerfilOrganizador.objects.create(usuario=user, fecha_nacimiento=fecha_nacimiento)
        return user


    def validate_first_name(self, value):
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', value):
            raise serializers.ValidationError('El nombre solo puede contener letras.')
        return value

    def validate_last_name(self, value):
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', value):
            raise serializers.ValidationError('El apellido solo puede contener letras.')
        return value

class PerfilSerializer(serializers.ModelSerializer):
    fecha_nacimiento = serializers.DateField(source='perfil.fecha_nacimiento')

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'fecha_nacimiento']


class SubtareaHoySerializer(serializers.ModelSerializer):
    evento_id = serializers.IntegerField(source='evento.id', read_only=True)
    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)

    class Meta:
        model = SubtareaLogistica
        fields = [
            'id', 'nombre', 'fecha_limite', 'horas_estimadas',
            'estado', 'nota', 'evento_id', 'evento_nombre'
        ] 

class SubtareaDetalleSerializer(serializers.ModelSerializer):
    evento_id = serializers.IntegerField(source='evento.id', read_only=True)

    class Meta:
        model = SubtareaLogistica
        fields = ['id', 'nombre', 'fecha_limite', 'horas_estimadas',
                  'estado', 'nota', 'evento_id']
        read_only_fields = ['id']

    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError('El nombre de la subtarea es obligatorio.')
        return value

    def validate_horas_estimadas(self, value):
        if value <= 0:
            raise serializers.ValidationError('Las horas estimadas deben ser mayores a 0.')
        return value