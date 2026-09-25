
from django.urls import path
from .views import health, EventoListCreateView

urlpatterns = [
    path('health/', health, name='health'),
    path('eventos/', EventoListCreateView.as_view(), name='evento-list-create'),
]