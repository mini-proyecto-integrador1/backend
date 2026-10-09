from datetime import date, timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Evento, PerfilOrganizador, SubtareaLogistica


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
class BaseSprint3(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.ana = self.crear_usuario('ana@correo.com')
        self.beto = self.crear_usuario('beto@correo.com')
        self.evento = Evento.objects.create(
            usuario=self.ana, nombre='Boda', tipo='Social', fecha=self.hoy + timedelta(days=10))
        self.entrar(self.ana)

    def crear_usuario(self, correo):
        usuario = User.objects.create_user(correo, correo, 'Clave12345!')
        PerfilOrganizador.objects.create(usuario=usuario, fecha_nacimiento=date(2000, 1, 1))
        return usuario

    def entrar(self, usuario):
        token, _ = Token.objects.get_or_create(user=usuario)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def dia(self, n):
        return self.hoy + timedelta(days=n)

    def gestion(self, dias, horas, estado='pendiente', evento=None):
        return SubtareaLogistica.objects.create(
            evento=evento or self.evento, nombre='G', fecha_limite=self.dia(dias),
            horas_estimadas=horas, estado=estado)


class LimiteDiarioTests(BaseSprint3):
    URL = '/api/perfil/limite/'
    MENSAJE = 'El límite debe estar entre 1 y 16 horas.'

    def test_limite_por_defecto_es_6(self):
        r = self.client.get(self.URL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, {'limite_horas_diarias': 6})

    def test_actualiza_y_persiste(self):
        r = self.client.put(self.URL, {'limite_horas_diarias': 8}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, {'limite_horas_diarias': 8})
        self.assertEqual(self.client.get(self.URL).data['limite_horas_diarias'], 8)

    def test_fuera_de_rango_responde_400(self):
        for valor in (0, 17, 6.5, -1, 'abc'):
            r = self.client.put(self.URL, {'limite_horas_diarias': valor}, format='json')
            self.assertEqual(r.status_code, 400, valor)
            self.assertEqual(r.data['limite_horas_diarias'], [self.MENSAJE], valor)
        self.assertEqual(self.client.get(self.URL).data['limite_horas_diarias'], 6)

    def test_cada_usuario_solo_ve_y_cambia_el_suyo(self):
        self.client.put(self.URL, {'limite_horas_diarias': 10}, format='json')
        self.entrar(self.beto)
        self.assertEqual(self.client.get(self.URL).data['limite_horas_diarias'], 6)
        self.client.put(self.URL, {'limite_horas_diarias': 3}, format='json')
        self.entrar(self.ana)
        self.assertEqual(self.client.get(self.URL).data['limite_horas_diarias'], 10)

    def test_sin_token_responde_401(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.URL).status_code, 401)


class SobrecargaTests(BaseSprint3):
    def url(self, gestion):
        return f'/api/subtareas/{gestion.id}/'

    def test_patch_con_conflicto_da_409_con_cifras(self):
        self.gestion(3, 5)
        b = self.gestion(5, 2)
        r = self.client.patch(self.url(b), {'fecha_limite': str(self.dia(3))}, format='json')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data, {
            'codigo': 'sobrecarga', 'fecha': str(self.dia(3)), 'limite': 6,
            'planificadas': 7, 'horas_gestion': 2, 'exceso': 1,
            'horas_disponibles': 1, 'dia_sugerido': str(self.hoy),
        })
        b.refresh_from_db()
        self.assertEqual(b.fecha_limite, self.dia(5))  # no se movió

    def test_patch_sin_conflicto_actualiza(self):
        self.gestion(3, 5)
        b = self.gestion(5, 2)
        r = self.client.patch(self.url(b), {'fecha_limite': str(self.dia(4))}, format='json')
        self.assertEqual(r.status_code, 200)
        b.refresh_from_db()
        self.assertEqual(b.fecha_limite, self.dia(4))

    def test_resolver_reduciendo_horas(self):
        self.gestion(3, 5)
        b = self.gestion(5, 2)
        cuerpo = {'fecha_limite': str(self.dia(3)), 'horas_estimadas': 2}
        self.assertEqual(self.client.patch(self.url(b), cuerpo, format='json').status_code, 409)
        cuerpo['horas_estimadas'] = 1
        self.assertEqual(self.client.patch(self.url(b), cuerpo, format='json').status_code, 200)

    def test_las_hechas_no_cuentan(self):
        self.gestion(3, 5, estado='hecho')
        b = self.gestion(5, 2)
        r = self.client.patch(self.url(b), {'fecha_limite': str(self.dia(3))}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_cambiar_solo_el_estado_nunca_da_409(self):
        self.gestion(3, 5)
        b = self.gestion(3, 3)  # el día ya está pasado de 6 h
        r = self.client.patch(self.url(b), {'estado': 'hecho'}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_suma_todos_los_eventos_del_organizador_y_solo_los_suyos(self):
        otro = Evento.objects.create(usuario=self.ana, nombre='Fiesta', tipo='Social', fecha=self.dia(10))
        ajeno = Evento.objects.create(usuario=self.beto, nombre='Ajeno', tipo='Social', fecha=self.dia(10))
        self.gestion(3, 5, evento=ajeno)  # de otro organizador: no cuenta
        b = self.gestion(5, 2)
        r = self.client.patch(self.url(b), {'fecha_limite': str(self.dia(3))}, format='json')
        self.assertEqual(r.status_code, 200)
        self.gestion(4, 5, evento=otro)  # de otro evento del mismo organizador: sí cuenta
        c = self.gestion(6, 2)
        r = self.client.patch(self.url(c), {'fecha_limite': str(self.dia(4))}, format='json')
        self.assertEqual(r.status_code, 409)

    def test_fecha_despues_del_evento_o_en_el_pasado_da_400(self):
        b = self.gestion(5, 2)
        for fecha in (self.evento.fecha + timedelta(days=1), self.hoy - timedelta(days=1)):
            r = self.client.patch(self.url(b), {'fecha_limite': str(fecha)}, format='json')
            self.assertEqual(r.status_code, 400)
            self.assertIn('fecha_limite', r.data)

    def test_post_gestion_con_conflicto_da_409_y_no_guarda(self):
        self.gestion(3, 5)
        r = self.client.post(f'/api/eventos/{self.evento.id}/subtareas/', {
            'nombre': 'Comprar torta', 'fecha_limite': str(self.dia(3)), 'horas_estimadas': 2,
        }, format='json')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data['codigo'], 'sobrecarga')
        self.assertEqual(SubtareaLogistica.objects.count(), 1)

    def test_post_evento_con_varios_dias_en_conflicto(self):
        self.gestion(3, 5)
        r = self.client.post('/api/eventos/', {
            'nombre': 'Cumple', 'tipo': 'Social', 'fecha': str(self.dia(10)),
            'subtareas': [
                {'nombre': 'x', 'fecha_limite': str(self.dia(3)), 'horas_estimadas': 2},
                {'nombre': 'y', 'fecha_limite': str(self.dia(4)), 'horas_estimadas': 4},
                {'nombre': 'z', 'fecha_limite': str(self.dia(4)), 'horas_estimadas': 3},
            ],
        }, format='json')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data['codigo'], 'sobrecarga')
        conflictos = r.data['conflictos']
        self.assertEqual([c['fecha'] for c in conflictos], [str(self.dia(3)), str(self.dia(4))])
        self.assertEqual(conflictos[0]['planificadas'], 7)
        self.assertEqual(conflictos[1]['horas_gestion'], 7)
        self.assertIsNone(conflictos[1]['dia_sugerido'])  # 7 h no caben en ningún día
        self.assertEqual(Evento.objects.count(), 1)  # no se creó el evento

    def test_post_evento_sin_conflicto_crea(self):
        r = self.client.post('/api/eventos/', {
            'nombre': 'Cumple', 'tipo': 'Social', 'fecha': str(self.dia(10)),
            'subtareas': [{'nombre': 'x', 'fecha_limite': str(self.dia(3)), 'horas_estimadas': 2}],
        }, format='json')
        self.assertEqual(r.status_code, 201)
