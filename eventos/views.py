from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from django.contrib.auth.models import User

from .models import Evento
from .serializers import EventoSerializer


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
    GET  /api/eventos/  -> lista todos los eventos
    POST /api/eventos/  -> crea un evento junto con sus subtareas logisticas
    """
    serializer_class = EventoSerializer

    def get_queryset(self):
        return Evento.objects.all().order_by('-creado_en')

    def perform_create(self, serializer):
        # Sprint 0-1: aun no hay login (llega en Sprint 2).
        # Mientras tanto, todos los eventos quedan asociados a un usuario demo fijo.
        usuario_demo, _ = User.objects.get_or_create(
            username='usuario_demo',
            defaults={'email': 'demo@organizador-eventos.local'}
        )
        serializer.save(usuario=usuario_demo)