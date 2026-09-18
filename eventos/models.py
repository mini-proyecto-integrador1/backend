# Create your models here.

from django.db import models
from django.contrib.auth.models import User


class Evento(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eventos')
    nombre = models.CharField(max_length=200)
    fecha = models.DateField()
    limite_horas_diarias = models.PositiveIntegerField(default=6)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class SubtareaLogistica(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('hecho', 'Hecho'),
        ('pospuesto', 'Pospuesto'),
    ]

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='subtareas')
    nombre = models.CharField(max_length=200)
    fecha_limite = models.DateField()
    horas_estimadas = models.DecimalField(max_digits=5, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    nota = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.evento.nombre})"