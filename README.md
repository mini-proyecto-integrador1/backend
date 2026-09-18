# Backend - Organizador de Eventos Independientes

API REST construida con Django REST Framework para el mini-proyecto integrador.

## Tecnologías
- Django + Django REST Framework
- PostgreSQL (Supabase)

## Modelos
- **Evento**: evento organizado por un usuario, con límite de horas diarias configurable.
- **SubtareaLogistica**: gestión logística asociada a un evento (reservar salón, enviar invitaciones, etc.), con fecha límite, horas estimadas y estado.

## Endpoints disponibles
- `GET /api/health/` — verifica que el servidor está activo.

## Cómo correr el proyecto localmente
1. Crear entorno virtual: `python -m venv venv`
2. Activarlo: `.\venv\Scripts\Activate`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Crear archivo `.env` con la variable `DATABASE_URL`
5. Correr migraciones: `python manage.py migrate`
6. Levantar servidor: `python manage.py runserver`