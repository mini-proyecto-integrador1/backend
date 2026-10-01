from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from django.contrib.auth.models import User
from .models import Evento
from .serializers import EventoSerializer
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