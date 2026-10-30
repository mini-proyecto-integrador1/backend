# En Punto — Backend

API REST de **En Punto**, la aplicación para organizadores de eventos independientes: guarda los eventos con sus gestiones logísticas, calcula qué es urgente hoy, avisa cuando un día se sobrecarga y entrega el avance de cada evento.

Proyecto Integrador I (750018C) — Universidad del Valle, 2026-II.

## Aplicación desplegada

| Servicio | URL |
|---|---|
| Backend (Render) | https://mini-proyecto-integrador1-back.onrender.com |
| Documentación de la API (Swagger) | https://mini-proyecto-integrador1-back.onrender.com/api/docs/ |
| Esquema OpenAPI | https://mini-proyecto-integrador1-back.onrender.com/api/schema/ |
| Estado del servicio | https://mini-proyecto-integrador1-back.onrender.com/api/health/ |
| Frontend (Vercel) | https://frontend-sepia-eight-44.vercel.app |

> El backend está en un plan gratuito de Render y se duerme cuando no se usa. La primera petición puede tardar hasta un minuto; si falla, espera un momento y vuelve a intentar.

## Cuenta de demostración

- **Correo:** `demo@enpunto.com`
- **Contraseña:** `D040608#`

### Probar la API desde Swagger

1. Abre `/api/docs/`.
2. En `POST /api/login/` pulsa **Try it out**, escribe `{"username": "demo@enpunto.com", "password": "D040608#"}` y ejecuta. Copia el valor de `token`.
3. Pulsa **Authorize** (arriba a la derecha) y escribe `Token <tu token>` (la palabra `Token`, un espacio y el valor).
4. Ya puedes probar `GET /api/hoy/`, `GET /api/eventos/` o `GET /api/progreso/`.

## Tecnologías

- Python 3.13 (probado) y Django 6.1
- Django REST Framework 3.18 (autenticación por token)
- drf-spectacular (Swagger / OpenAPI)
- PostgreSQL en Supabase (producción); cualquier base compatible con `DATABASE_URL` en local
- django-cors-headers, dj-database-url, psycopg
- gunicorn (servidor en Render)

## Endpoints

Todos van bajo `/api/`. Los marcados con 🔒 requieren la cabecera `Authorization: Token <token>`.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health/` | Comprueba que el servicio responde |
| POST | `/api/registro/` | Crea una cuenta (correo, contraseña, nombre, apellido y fecha de nacimiento) |
| POST | `/api/login/` | Devuelve el token (`username` es el correo) |
| GET | `/api/perfil/` 🔒 | Datos del usuario |
| PUT/PATCH | `/api/perfil/limite/` 🔒 | Cambia el límite de horas diarias |
| GET, POST | `/api/eventos/` 🔒 | Lista los eventos del usuario / crea uno |
| GET, PUT, PATCH, DELETE | `/api/eventos/<id>/` 🔒 | Detalle, edición y eliminación de un evento |
| POST | `/api/eventos/<id>/subtareas/` 🔒 | Agrega una gestión a un evento |
| GET, PUT, PATCH, DELETE | `/api/subtareas/<id>/` 🔒 | Detalle, edición (estado, nota, fecha) y eliminación de una gestión |
| GET | `/api/hoy/` 🔒 | Gestiones ordenadas por urgencia (vencidas, para hoy, próximas) y avisos de sobrecarga |
| GET | `/api/progreso/` 🔒 | Avance de cada evento y avance general |

Cada usuario solo ve y modifica sus propios eventos.

## Modelo de datos

| Modelo | Campos principales |
|---|---|
| `Evento` | usuario, nombre, tipo, fecha, límite de horas diarias (6 por defecto) |
| `SubtareaLogistica` (gestión) | evento, nombre, fecha límite, horas estimadas, estado (`pendiente`, `hecho`, `pospuesto`), nota, fecha de completado |
| `PerfilOrganizador` | usuario, fecha de nacimiento, límite de horas diarias |

Al borrar un evento se borran sus gestiones.

## Ejecutar en local

### Requisitos

- [Python](https://www.python.org/downloads/) 3.12 o superior (probado con 3.13). Para comprobarlo: `python --version`
- Git
- Una base de datos PostgreSQL (por ejemplo la de un proyecto gratuito de [Supabase](https://supabase.com)) **o** usar SQLite solo para pruebas locales (ver más abajo)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/mini-proyecto-integrador1/backend.git
cd backend

# 2. Crear y activar un entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows (CMD o PowerShell)
source venv/bin/activate       # macOS / Linux

# 3. Instalar dependencias
pip install -r requirements.txt
```

**4. Crear el archivo `.env`** en la raíz del backend (mismo nivel que `manage.py`):

```
DATABASE_URL=postgresql://usuario:contraseña@host:5432/basedatos
SECRET_KEY=una-clave-larga-y-secreta
DEBUG=True
```

> Para probar rápido sin PostgreSQL puedes usar `DATABASE_URL=sqlite:///db.sqlite3`.

```bash
# 5. Crear las tablas
python manage.py migrate

# 6. Iniciar el servidor
python manage.py runserver
```

**Qué deberías ver en cada paso:**

1. `pip install` termina sin errores.
2. `migrate` lista las migraciones aplicadas (`Applying eventos.0001_initial... OK`).
3. `runserver` muestra `Starting development server at http://127.0.0.1:8000/`. Déjalo abierto.
4. Abre http://127.0.0.1:8000/api/health/ (debe responder) y http://127.0.0.1:8000/api/docs/ (debe mostrar Swagger).

Para detener el servidor presiona `Ctrl + C`.

### Crear un usuario de prueba

Desde Swagger, usa `POST /api/registro/` con un cuerpo como:

```json
{
  "email": "prueba@correo.com",
  "password": "UnaClave123",
  "first_name": "Ana",
  "last_name": "Pérez",
  "fecha_nacimiento": "1995-05-20"
}
```

Luego inicia sesión con `POST /api/login/` (el `username` es el correo).

### Usar el backend local con el frontend

En el repositorio del frontend crea un archivo `.env.local` con:

```
VITE_API_URL=http://localhost:8000
```

y ejecuta `npm run dev`. El backend ya permite el origen `http://localhost:5173` (CORS).

### Variables de entorno

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | Cadena de conexión a la base de datos |
| `SECRET_KEY` | En producción | Clave secreta de Django (si falta, se usa una de desarrollo) |
| `DEBUG` | No | `True` por defecto. En producción debe ser `False` |

## Pruebas automáticas

```bash
python manage.py test
```

Ejecuta las 28 pruebas (registro, login, eventos, gestiones, vista Hoy, progreso y límite diario). Deben terminar con `OK`. Se necesita `DATABASE_URL` definida; para no tocar tu base real puedes usar SQLite:

```bash
# Windows (CMD)
set DATABASE_URL=sqlite:///db.sqlite3 && python manage.py test

# macOS / Linux
DATABASE_URL=sqlite:///db.sqlite3 python manage.py test
```

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Please supply the ENGINE value` o error de base de datos | Falta `DATABASE_URL` | Crea el archivo `.env` (o define la variable) como se indica arriba. |
| `ModuleNotFoundError` | El entorno virtual no está activo o faltan dependencias | Activa el entorno y ejecuta `pip install -r requirements.txt`. |
| `401 Unauthorized` o "Las credenciales de autenticación no se proporcionaron" | Falta el token | Envía `Authorization: Token <token>` (en Swagger, botón **Authorize**). |
| El navegador bloquea las peticiones del frontend (CORS) | Origen no permitido | Solo se permiten `http://localhost:5173` y el dominio de Vercel; agrega otros en `CORS_ALLOWED_ORIGINS` de `config/settings.py`. |
| En producción la primera petición tarda o falla | El servicio de Render está dormido | Espera 30 a 60 segundos y repite. |
| `pip install` falla leyendo `requirements.txt` | Archivo guardado en una codificación distinta a UTF-8 | Vuelve a guardarlo como UTF-8. |

## Despliegue

- **API:** Render, a partir de la rama `main`, con `gunicorn config.wsgi`. Las variables `DATABASE_URL`, `SECRET_KEY` y `DEBUG=False` se configuran en el panel de Render, nunca en el repositorio.
- **Base de datos:** PostgreSQL en Supabase.
- Después de cada cambio en los modelos hay que ejecutar `python manage.py migrate` contra la base de producción.

## Estructura del proyecto

```
config/       Configuración de Django (settings, urls, wsgi)
eventos/
├── models.py       Evento, SubtareaLogistica, PerfilOrganizador
├── serializers.py  Validación y formato de los datos
├── views.py        Vistas de la API
├── urls.py         Rutas bajo /api/
├── migrations/     Migraciones de la base de datos
└── tests.py        Pruebas automáticas
manage.py
requirements.txt
```

## Equipo

- Jairo Hernán González Barreto — backend
- Luis Yair Valencia Rivas — UX, frontend y QA
- Martín Stivensson Álvarez Quintero — UX y frontend

Profesor: Fabián Stiven Valencia Córdoba
