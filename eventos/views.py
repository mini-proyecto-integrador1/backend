# Create your views here.

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def health(request):
    return Response({"status": "ok", "message": "El servidor esta funcionando correctamente"})

@api_view(['GET'])
def home(request):
    return Response({
        "mensaje": "API del Organizador de Eventos Independientes",
        "endpoints_disponibles - ir a": ["https://mini-proyecto-integrador1-back.onrender.com/api/health/"]
    })