from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .documentacion import RESPUESTA_409, RESPUESTA_409_MULTIPLE
from .models import Evento, SubtareaLogistica, PerfilOrganizador
from .serializers import (
    EventoSerializer, SubtareaHoySerializer, SubtareaDetalleSerializer,
    SubtareaCrearSerializer, RegistroSerializer, PerfilSerializer,
    LimiteDiarioSerializer,
)
from .sobrecarga import (
    ESTADOS_QUE_CUENTAN, SobrecargaError, calcular_conflicto,
    conflictos_de_gestiones_nuevas, limite_de,
)


@api_view(['GET'])
def health(request):
    return Response({"status": "ok", "message": "El servidor esta funcionando correctamente"})


@api_view(['GET'])
def home(request):
    return Response({
        "mensaje": "API del Organizador de Eventos Independientes",
        "endpoints_disponibles - ir a": ["https://mini-proyecto-integrador1-back.onrender.com/api/health/"]
    })

@extend_schema_view(post=extend_schema(responses={
    201: EventoSerializer,
    400: OpenApiResponse(description='Datos inválidos.'),
    409: RESPUESTA_409_MULTIPLE,
}))


class EventoListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/eventos/  -> lista SOLO los eventos del usuario autenticado
    POST /api/eventos/  -> crea un evento asociado al usuario autenticado
    """
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Evento.objects.filter(usuario=self.request.user).order_by('-creado_en')

    def perform_create(self, serializer):
        gestiones = serializer.validated_data.get('subtareas', [])
        if gestiones:
            conflictos = conflictos_de_gestiones_nuevas(
                self.request.user, gestiones, serializer.validated_data['fecha'])
            if conflictos:
                raise SobrecargaError({'codigo': 'sobrecarga', 'conflictos': conflictos})
        serializer.save(usuario=self.request.user)

class RegistroView(generics.CreateAPIView):
    """
    POST /api/registro/ -> crea un nuevo usuario (organizador)
    """
    queryset = User.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]

class PerfilView(generics.RetrieveAPIView):
    """
    GET /api/perfil/ -> devuelve los datos del usuario autenticado
    """
    serializer_class = PerfilSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class VistaHoyView(generics.ListAPIView):
    """
    GET /api/hoy/ -> lista las subtareas del usuario autenticado,
    ordenadas por fecha limite (ascendente) y luego por horas
    estimadas (ascendente = menor esfuerzo primero en caso de empate).

    Filtros opcionales por query params:
    - ?evento=<id>      filtra por un evento especifico
    - ?estado=<estado>  filtra por estado (pendiente, hecho, pospuesto)
    """
    serializer_class = SubtareaHoySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = SubtareaLogistica.objects.filter(
            evento__usuario=self.request.user
        ).order_by('fecha_limite', 'horas_estimadas')

        evento_id = self.request.query_params.get('evento')
        if evento_id:
            queryset = queryset.filter(evento__id=evento_id)

        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

class EventoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/eventos/<id>/ -> detalle del evento (con sus subtareas)
    PUT    /api/eventos/<id>/ -> edicion completa
    PATCH  /api/eventos/<id>/ -> edicion parcial
    DELETE /api/eventos/<id>/ -> elimina el evento y sus subtareas
    Solo el dueño del evento puede acceder; los demas reciben 404.
    """
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Evento.objects.filter(usuario=self.request.user)

_RESPUESTAS_EDICION = {
200: SubtareaDetalleSerializer,
400: OpenApiResponse(description='Datos inválidos (por ejemplo, fecha_limite en el pasado o después del evento).'),
409: RESPUESTA_409,
}

@extend_schema_view(
    patch=extend_schema(responses=_RESPUESTAS_EDICION),
    put=extend_schema(responses=_RESPUESTAS_EDICION),
)


class SubtareaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/subtareas/<id>/ -> detalle de la subtarea
    PUT    /api/subtareas/<id>/ -> edicion completa
    PATCH  /api/subtareas/<id>/ -> edicion parcial (ej. cambiar estado)
    DELETE /api/subtareas/<id>/ -> elimina la subtarea
    Solo el dueño del evento al que pertenece puede acceder.
    """
    serializer_class = SubtareaDetalleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SubtareaLogistica.objects.filter(evento__usuario=self.request.user)

    def perform_update(self, serializer):
        gestion = serializer.instance
        datos = serializer.validated_data
        toca_la_carga = 'fecha_limite' in datos or 'horas_estimadas' in datos
        estado_final = datos.get('estado', gestion.estado)
        # cambiar SOLO el estado nunca da 409; una gestión 'hecho' no suma horas
        if toca_la_carga and estado_final in ESTADOS_QUE_CUENTAN:
            conflicto = calcular_conflicto(
                self.request.user,
                datos.get('fecha_limite', gestion.fecha_limite),
                datos.get('horas_estimadas', gestion.horas_estimadas),
                gestion.evento.fecha,
                excluir_id=gestion.pk,
            )
            if conflicto:
                raise SobrecargaError(conflicto)
        serializer.save()


@extend_schema_view(post=extend_schema(responses={
    201: SubtareaCrearSerializer,
    400: OpenApiResponse(description='Datos inválidos.'),
    404: OpenApiResponse(description='El evento no existe o es de otro organizador.'),
    409: RESPUESTA_409,
}))

class SubtareaCreateView(generics.CreateAPIView):
    """
    POST /api/eventos/<id>/subtareas/ -> agrega una gestión logística a un evento ya guardado.
    Body: { "nombre", "fecha_limite", "horas_estimadas" }  ->  201 con la gestión creada.
    Si el evento no existe o es de otro organizador responde 404 (aislamiento).
    """
    serializer_class = SubtareaCrearSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        contexto['evento'] = get_object_or_404(Evento, pk=self.kwargs['pk'], usuario=self.request.user)
        return contexto

    def perform_create(self, serializer):
        evento = serializer.context['evento']
        datos = serializer.validated_data
        conflicto = calcular_conflicto(
            self.request.user, datos['fecha_limite'], datos['horas_estimadas'], evento.fecha)
        if conflicto:
            raise SobrecargaError(conflicto)
        serializer.save()

class LimiteDiarioView(APIView):
    """
    GET /api/perfil/limite/ -> límite de horas diarias del organizador (6 por defecto)
    PUT /api/perfil/limite/ -> cambia el límite (entero de 1 a 16)
    Cada organizador solo ve y cambia el suyo.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Consultar el límite diario', responses=LimiteDiarioSerializer)
    def get(self, request):
        return Response({'limite_horas_diarias': limite_de(request.user)})

    @extend_schema(
        summary='Cambiar el límite diario',
        request=LimiteDiarioSerializer,
        responses={
            200: LimiteDiarioSerializer,
            400: OpenApiResponse(description='Debe ser un entero entre 1 y 16: "El límite debe estar entre 1 y 16 horas."'),
            404: OpenApiResponse(description='El usuario no tiene perfil de organizador.'),
        },
    )
    def put(self, request):
        serializer = LimiteDiarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        perfil = PerfilOrganizador.objects.filter(usuario=request.user).first()
        if perfil is None:
            return Response({'detail': 'El usuario no tiene perfil de organizador.'}, status=404)
        perfil.limite_horas_diarias = serializer.validated_data['limite_horas_diarias']
        perfil.save(update_fields=['limite_horas_diarias'])
        return Response({'limite_horas_diarias': perfil.limite_horas_diarias})
