# SubjectSupport - Plataforma de Tutorías

## Descripción General

SubjectSupport es una plataforma web completa de tutorías que conecta tutores con estudiantes, permitiendo la reserva de clases, gestión de sesiones y realización de reuniones virtuales. El sistema implementa un flujo completo desde la búsqueda de tutores hasta la ejecución de sesiones en línea con integración de múltiples plataformas de videollamadas.

## Stack Tecnológico

- **Backend**: Django 5.2
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción recomendada)
- **Autenticación**: Django Auth con modelo de usuario personalizado
- **Frontend**: HTML, CSS, JavaScript (Django Templates)
- **Testing**: Django TestCase (76 tests implementados)
- **Python**: 3.x

## Estructura del Proyecto

```
subjectsSuport/
├── accounts/                    # App de autenticación y perfiles
│   ├── models.py               # User, TutorProfile, ClientProfile
│   ├── views.py                # Registro, login, dashboards
│   ├── forms.py                # Formularios de registro y login
│   ├── urls.py                 # URLs de autenticación
│   ├── tests.py                # Tests de autenticación (38 tests)
│   └── test_utils.py           # Factory para crear usuarios de test
├── core/                        # App principal de funcionalidad
│   ├── models.py               # ClassSession, TutorLead
│   ├── views.py                # Vistas de sesiones y tutores
│   ├── forms.py                # Formularios de sesión
│   ├── urls.py                 # URLs principales
│   ├── tests.py                # Tests funcionales (38 tests)
│   └── services/
│       └── meeting_service.py  # Generación de URLs de reuniones
├── subjectSupport/              # Configuración del proyecto
│   ├── settings.py             # Configuración Django
│   ├── urls.py                 # URLs raíz
│   └── meeting_config.py       # Configuración de reuniones
├── templates/                   # Templates Django
├── static/                      # Archivos estáticos
├── env/                         # Entorno virtual (no en git)
├── db.sqlite3                   # Base de datos (no en git)
├── manage.py                    # CLI de Django
└── README.md                    # Este archivo
```

## Modelos de Datos

### App: accounts

#### User (AbstractUser extendido)
```python
- email: EmailField (unique, usado como USERNAME_FIELD)
- name: CharField (nombre completo)
- user_type: CharField (choices: 'tutor', 'client')
- date_joined: DateTimeField (auto)
- is_active: BooleanField
```

**Relaciones:**
- `tutor_profile`: OneToOne → TutorProfile
- `client_profile`: OneToOne → ClientProfile
- `tutor_sessions`: ForeignKey ← ClassSession (como tutor)
- `client_sessions`: ForeignKey ← ClassSession (como cliente)

#### TutorProfile
```python
- user: OneToOneField → User
- subjects: CharField (materias separadas por comas)
- bio: TextField (opcional)
- experience: TextField (opcional)
- city: CharField (default='Quito')
- country: CharField (default='Ecuador')
- created_at: DateTimeField
```

#### ClientProfile
```python
- user: OneToOneField → User
- is_minor: BooleanField (default=False)
- parent_name: CharField (opcional)
- city: CharField (default='Quito')
- country: CharField (default='Ecuador')
- created_at: DateTimeField
```

### App: core

#### ClassSession (Sesión de Clase)
```python
- tutor: ForeignKey → User (limit_choices_to={'user_type': 'tutor'})
- client: ForeignKey → User (limit_choices_to={'user_type': 'client'})
- subject: CharField (materia)
- scheduled_date: DateField
- scheduled_time: TimeField
- duration: IntegerField (choices: 30, 60, 90, 120 minutos)
- status: CharField (choices: 'pending', 'confirmed', 'completed', 'cancelled')
- meeting_platform: CharField (choices: 'google_meet', 'zoom', 'custom')
- meeting_url: URLField (generado automáticamente)
- meeting_id: CharField (generado automáticamente)
- meeting_password: CharField (opcional, según plataforma)
- host_join_url: URLField (para tutores)
- meeting_started: BooleanField (default=False)
- notes: TextField (opcional)
- created_at: DateTimeField
- updated_at: DateTimeField
```

**Meta:**
- `ordering = ['-scheduled_date', '-scheduled_time']`

**Métodos:**
- `is_upcoming()`: Verifica si la sesión es futura
- `is_past()`: Verifica si la sesión ya pasó

#### TutorLead (Lead de Tutor)
```python
- name: CharField (nombre del prospecto)
- email: EmailField
- subject: CharField (materia de interés)
- created_at: DateTimeField
```

**Meta:**
- `ordering = ['-created_at', '-id']` ← Importante: doble ordenamiento para evitar no-determinismo en tests

## Flujo de Usuario

### Cliente (Estudiante)

1. **Registro**: `/accounts/register/client/`
   - Crea User con `user_type='client'`
   - Crea ClientProfile automáticamente
   - Login automático post-registro

2. **Dashboard**: `/accounts/dashboard/` → redirige a `/accounts/client-dashboard/`
   - Vista de sesiones próximas (confirmadas)
   - Vista de solicitudes pendientes
   - Historial de sesiones pasadas

3. **Búsqueda de Tutores**: `/tutors/`
   - **Búsqueda geográfica prioritizada**: tutores de la misma ciudad → mismo país → otros
   - Filtros: búsqueda por nombre/materias, ciudad
   - Vista de perfiles de tutores

4. **Solicitud de Sesión**: `/session/request/<tutor_id>/`
   - Formulario con: subject, scheduled_date, scheduled_time, duration, notes
   - Validación: no permite fechas pasadas
   - Crea ClassSession con `status='pending'`

5. **Acceso a Reunión**: `/session/<session_id>/meeting/`
   - Solo accesible si `status='confirmed'`
   - Muestra meeting_url, meeting_id, meeting_password
   - Cliente NO es host

### Tutor

1. **Registro**: `/accounts/register/tutor/`
   - Crea User con `user_type='tutor'`
   - Crea TutorProfile automáticamente con subjects, bio, experience, ubicación
   - Login automático post-registro

2. **Dashboard**: `/accounts/dashboard/` → redirige a `/accounts/tutor-dashboard/`
   - Solicitudes pendientes (`status='pending'`)
   - Sesiones próximas confirmadas
   - Todas las sesiones activas

3. **Confirmación de Sesión**: `/session/<session_id>/confirm/`
   - Solo tutor puede confirmar sus sesiones
   - Selecciona meeting_platform (google_meet, zoom, custom)
   - Añade notas opcionales
   - Al confirmar:
     - `status` → 'confirmed'
     - Se genera automáticamente meeting_url, meeting_id, meeting_password
     - Servicio: `update_session_with_meeting()`

4. **Acceso a Reunión**: `/session/<session_id>/meeting/`
   - Solo accesible si `status='confirmed'`
   - Tutor ES host
   - Muestra host_join_url especial (para Zoom)
   - Al acceder, marca `meeting_started=True`

### Cancelación (Ambos)

- `/session/<session_id>/cancel/`
- Solo tutor o cliente de la sesión
- No se puede cancelar si `status='completed'`
- Cambia `status` → 'cancelled'

## Servicios

### meeting_service.py

Genera URLs de reunión automáticamente según la plataforma seleccionada:

#### `generate_google_meet_url(session)`
```python
Returns:
{
    'meeting_url': 'https://meet.google.com/[unique_id]',
    'host_join_url': '[same]',
    'meeting_id': 'xxx-xxxx-xxx',  # Formato Google Meet
    'meeting_password': None
}
```

#### `generate_zoom_url(session)`
```python
Returns:
{
    'meeting_url': 'https://zoom.us/j/[id]?pwd=[password]',
    'host_join_url': 'https://zoom.us/s/[id]?zak=host_[token]',
    'meeting_id': 'XXX XXXX XXXX',  # Formato Zoom
    'meeting_password': '[6 caracteres alphanumericos]'
}
```

#### `generate_custom_meeting_url(session)`
```python
Returns:
{
    'meeting_url': 'https://meet.subjectsupport.com/room/[room_id]',
    'host_join_url': '[same]',
    'meeting_id': '[12 caracteres hex]',
    'meeting_password': '[8 caracteres alphanumericos]'
}
```

#### `create_meeting_for_session(session)` y `update_session_with_meeting(session, save=True)`
- Función principal que ejecuta el generador apropiado
- Actualiza la sesión con los datos de reunión
- Usado automáticamente en confirm_session view

## Autenticación y Permisos

### Sistema de Autenticación
- Email como USERNAME_FIELD (no username tradicional)
- Separación estricta de user_types ('tutor' vs 'client')
- Login/logout estándar de Django

### Control de Acceso por Vista

```python
# Decoradores obligatorios
@login_required

# Checks manuales de permisos
if request.user.user_type != 'client':
    messages.error(request, 'Solo los clientes pueden...')
    return redirect('dashboard')
```

**Vistas protegidas:**
- `/tutors/` → solo clients
- `/session/request/<id>/` → solo clients
- `/session/<id>/confirm/` → solo tutors (y solo el tutor asignado)
- `/accounts/tutor-dashboard/` → solo tutors
- `/accounts/client-dashboard/` → solo clients
- `/session/<id>/meeting/` → solo tutor o client de esa sesión
- `/session/<id>/cancel/` → solo tutor o client de esa sesión

## Testing

### Cobertura Total: 76 Tests (100% passing)

#### accounts/tests.py (38 tests)
- `UserModelTest`: Creación de usuarios, perfiles automáticos, validaciones
- `TutorRegistrationTest`: Registro completo de tutores
- `ClientRegistrationTest`: Registro completo de clientes
- `LoginTest`: Login con email, redirección a dashboard apropiado
- `DashboardAccessTest`: Control de acceso separado tutor/client
- `UserFactoryTest`: Validación del factory de testing

#### core/tests.py (38 tests)
- `ClassSessionModelTest`: CRUD de sesiones, estados, métodos is_upcoming/is_past
- `TutorLeadModelTest`: Creación de leads, **ordering determinístico**
- `SessionRequestFormTest`: Validación de formularios, fechas pasadas
- `SessionConfirmationFormTest`: Campos de plataforma de reunión
- `MeetingServiceTest`: Generación correcta de URLs para cada plataforma
- `TutorSelectionViewTest`: Priorización geográfica, búsquedas, acceso
- `SessionRequestViewTest`: Flujo completo de solicitud
- `SessionConfirmViewTest`: Confirmación y generación automática de reunión
- `SessionCancelViewTest`: Cancelación con permisos
- `MeetingRoomViewTest`: Acceso a sala, roles host/participant, validaciones
- `LandingPageTest`: Página landing para anónimos

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests específicos de una app
python manage.py test accounts
python manage.py test core

# Test específico
python manage.py test core.tests.TutorLeadModelTest.test_tutor_lead_ordering
```

## Instalación y Setup

### 1. Clonar y preparar entorno

```bash
git clone <repository>
cd subjectsSuport
```

### 2. Crear entorno virtual

**Windows:**
```bash
python -m venv env
env\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Instalar dependencias

```bash
pip install django
```

### 4. Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 6. Ejecutar servidor

```bash
python manage.py runserver
```

Navegar a: `http://localhost:8000/`

### 7. Ejecutar tests

```bash
python manage.py test
```

## URLs Principales

### Públicas
- `/` → Landing page
- `/accounts/register/tutor/` → Registro tutor
- `/accounts/register/client/` → Registro cliente
- `/accounts/login/` → Login

### Autenticadas
- `/accounts/dashboard/` → Dashboard (redirige según user_type)
- `/accounts/tutor-dashboard/` → Dashboard tutor
- `/accounts/client-dashboard/` → Dashboard cliente
- `/accounts/logout/` → Logout

### Tutores (solo tutors)
- `/session/<id>/confirm/` → Confirmar sesión pendiente

### Clientes (solo clients)
- `/tutors/` → Lista de tutores (priorización geográfica)
- `/session/request/<tutor_id>/` → Solicitar sesión con tutor

### Compartidas (tutor o client de la sesión)
- `/session/<id>/meeting/` → Sala de reunión virtual
- `/session/<id>/cancel/` → Cancelar sesión

### Admin
- `/admin/` → Django Admin (requiere superuser)

## Características Implementadas

### Autenticación Completa
- Registro separado tutor/cliente
- Login con email
- Perfiles automáticos
- Dashboards diferenciados
- Control de acceso por user_type

### Gestión de Sesiones
- Solicitud de sesión (cliente)
- Confirmación de sesión (tutor)
- Estados: pending → confirmed → completed/cancelled
- Cancelación por ambas partes
- Validación de fechas (no permite pasadas)

### Integración de Reuniones
- Generación automática de URLs
- Soporte multi-plataforma: Google Meet, Zoom, Custom
- IDs y passwords únicos
- URLs especiales para hosts (Zoom)
- Flag meeting_started

### Búsqueda Geográfica
- Priorización: misma ciudad → mismo país → otros
- Filtros de búsqueda por nombre/materias
- Filtro por ciudad
- Query flexible con Q objects

### Sistema de Leads
- Formulario de contacto para potenciales tutores
- Almacenamiento de prospectos
- Ordenamiento determinístico

## Convenciones del Código

### Modelos
- Siempre incluir `verbose_name` y `verbose_name_plural` en Meta
- Usar `auto_now_add=True` para created_at
- Usar `auto_now=True` para updated_at
- Definir `__str__()` descriptivo
- **Importante**: Si ordering usa timestamp, añadir `-id` como secundario para evitar no-determinismo

### Vistas
- Decorador `@login_required` para todas las vistas autenticadas
- Checks manuales de `user_type` al inicio de la vista
- Mensajes con `messages.success/error/warning/info`
- Redirección apropiada en caso de error de permisos
- Usar `get_object_or_404` para lookups

### Forms
- Validación custom en `clean_<field>()`
- Labels en español
- Help texts descriptivos
- Widgets personalizados (DateInput con type='date', TimeInput con type='time')

### Tests
- Usar `UserFactory.create_tutor()` y `UserFactory.create_client()` de test_utils
- Cleanup automático (Django TestCase)
- Nombres descriptivos: `test_<acción>_<resultado_esperado>`
- Arrange-Act-Assert pattern
- Un assert principal por test (ideal)

### Templates
- Herencia: todas las páginas extienden `base.html`
- Mensajes de Django en layout
- CSRF token en todos los forms POST
- Login required checks en templates también

## Estado Actual del Proyecto

### Completado
- Sistema de autenticación completo
- Gestión de sesiones de clase
- Integración de reuniones virtuales
- Búsqueda y selección de tutores con priorización geográfica
- Sistema de permisos y control de acceso
- Suite completa de tests (76 tests, 100% passing)
- Formularios con validaciones
- Dashboards diferenciados

### Posibles Mejoras Futuras

1. **Integración API Real**
   - Conectar con Google Meet API oficial
   - Conectar con Zoom API oficial
   - OAuth para autenticación de plataformas

2. **Sistema de Pagos**
   - Integración con Stripe/PayPal
   - Gestión de tarifas por tutor
   - Historial de transacciones

3. **Notificaciones**
   - Email notifications (confirmaciones, recordatorios)
   - SMS/WhatsApp notifications
   - Push notifications

4. **Calendario**
   - Vista de calendario para disponibilidad
   - Sistema de slots disponibles
   - Prevención de conflictos de horario

5. **Valoraciones y Reviews**
   - Sistema de calificación post-sesión
   - Reviews y comentarios
   - Reputación de tutores

6. **Chat en Tiempo Real**
   - Mensajería tutor-cliente
   - Django Channels + WebSockets
   - Historial de conversaciones

7. **Sistema de Reportes**
   - Estadísticas para tutores
   - Estadísticas para administradores
   - Exportación de datos

8. **Internacionalización**
   - Multi-idioma (i18n)
   - Múltiples zonas horarias
   - Localización de contenido

9. **Frontend Moderno**
   - Migración a React/Vue
   - API REST con Django REST Framework
   - UI/UX mejorado

10. **Funcionalidades Admin**
    - Panel de control administrativo
    - Moderación de usuarios
    - Resolución de disputas

## Notas Importantes para Desarrollo Continuo

### Orden de Migraciones
1. Siempre hacer backup de db antes de migraciones en producción
2. Ejecutar `makemigrations` después de cambios en models
3. Revisar archivos de migración generados antes de aplicar

### Testing
- **SIEMPRE** ejecutar tests antes de commit
- Si cambias un modelo, actualiza sus tests
- Tests determinísticos: evitar dependencias de tiempo/orden
- Caso específico: TutorLead usa `ordering = ['-created_at', '-id']` para evitar race conditions en tests

### Seguridad
- NEVER commit `SECRET_KEY` real a git
- NEVER commit db.sqlite3 con datos reales
- Usar variables de entorno para configuración sensible
- CSRF protection habilitado (default Django)
- XSS protection con Django template escaping

### Performance
- Usar `select_related()` para ForeignKeys
- Usar `prefetch_related()` para ManyToMany
- Índices en campos frecuentemente filtrados
- Considerar caché para queries pesadas

### Git
```
# .gitignore debe incluir:
env/
*.pyc
__pycache__/
db.sqlite3
.env
*.log
```

## Contacto y Soporte

Para preguntas o contribuciones al proyecto, consultar con el equipo de desarrollo.

## Licencia

[Especificar licencia del proyecto]

---

**Última actualización**: 2025-11-09
**Versión**: 1.0.0
**Tests passing**: 76/76 ✓
