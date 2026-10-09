from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (health, EventoListCreateView, RegistroView, PerfilView,
                    VistaHoyView, EventoDetailView, SubtareaDetailView,
                    SubtareaCreateView, LimiteDiarioView,)
urlpatterns = [
    path('health/', health, name='health'),
    path('eventos/', EventoListCreateView.as_view(), name='evento-list-create'),
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', obtain_auth_token, name='login'),
    path('perfil/', PerfilView.as_view(), name='perfil'),
    path('hoy/', VistaHoyView.as_view(), name='vista-hoy'),
    path('eventos/<int:pk>/', EventoDetailView.as_view(), name='evento-detail'),
    path('subtareas/<int:pk>/', SubtareaDetailView.as_view(), name='subtarea-detail'),
    path('eventos/<int:pk>/subtareas/', SubtareaCreateView.as_view(), name='evento-subtarea-create'),
    path('perfil/limite/', LimiteDiarioView.as_view(), name='perfil-limite'),
]