from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from django.contrib.auth.models import User
from .models import Evento, SubtareaLogistica
from django.shortcuts import get_object_or_404
from .serializers import EventoSerializer, SubtareaHoySerializer, SubtareaDetalleSerializer, SubtareaCrearSerializer
from rest_framework.permissions import AllowAny
from .serializers import RegistroSerializer
from rest_framework.permissions import IsAuthenticated
from .serializers import PerfilSerializer



@api_view(['GET'])
def health(request):
    return Response({"status": "ok", "message": "El servidor esta funcionando correctamente"})


@api_view(['GET'])
def home(request):
    return Response({
        "mensaje": "API del Organizador de Eventos Independientes",
        "endpoints_disponibles - ir a": ["https://mini-proyecto-integrador1-back.onrender.com/api/health/"]
    })


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
