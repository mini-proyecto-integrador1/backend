from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Evento, SubtareaLogistica


class AgregarGestionTests(APITestCase):
    """POST /api/eventos/<id>/subtareas/ — agregar una gestión a un evento ya guardado."""

    def setUp(self):
        self.hoy = timezone.localdate()
        self.ana = User.objects.create_user('ana@correo.com', 'ana@correo.com', 'Clave12345!')
        self.beto = User.objects.create_user('beto@correo.com', 'beto@correo.com', 'Clave12345!')
        self.evento = Evento.objects.create(
            usuario=self.ana, nombre='Boda', tipo='Social', fecha=self.hoy + timedelta(days=20)
        )
        self.url = f'/api/eventos/{self.evento.id}/subtareas/'
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.ana).key)

    def datos(self, **cambios):
        base = {'nombre': 'Comprar torta', 'fecha_limite': str(self.hoy + timedelta(days=5)), 'horas_estimadas': 1.5}
        base.update(cambios)
        return base

    def test_agrega_la_gestion_al_evento(self):
        r = self.client.post(self.url, self.datos(), format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['estado'], 'pendiente')
        self.assertEqual(self.evento.subtareas.count(), 1)

    def test_la_nueva_gestion_aparece_en_hoy(self):
        self.client.post(self.url, self.datos(), format='json')
        r = self.client.get('/api/hoy/')
        self.assertEqual([g['nombre'] for g in r.data], ['Comprar torta'])

    def test_sin_token_responde_401(self):
        self.client.credentials()
        self.assertEqual(self.client.post(self.url, self.datos(), format='json').status_code, 401)

    def test_evento_de_otro_organizador_responde_404(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.create(user=self.beto).key)
        r = self.client.post(self.url, self.datos(), format='json')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(SubtareaLogistica.objects.count(), 0)

    def test_valida_nombre_horas_y_fechas(self):
        casos = {
            'nombre': self.datos(nombre='   '),
            'horas_estimadas': self.datos(horas_estimadas=0),
        }
        casos_fecha = [
            self.datos(fecha_limite=str(self.hoy - timedelta(days=1))),   # en el pasado
            self.datos(fecha_limite=str(self.evento.fecha + timedelta(days=1))),  # después del evento
        ]
        for campo, cuerpo in casos.items():
            r = self.client.post(self.url, cuerpo, format='json')
            self.assertEqual(r.status_code, 400, campo)
            self.assertIn(campo, r.data)
        for cuerpo in casos_fecha:
            r = self.client.post(self.url, cuerpo, format='json')
            self.assertEqual(r.status_code, 400)
            self.assertIn('fecha_limite', r.data)
        self.assertEqual(SubtareaLogistica.objects.count(), 0)
