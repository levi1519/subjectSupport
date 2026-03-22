# SubjectSupport - Quick Start Guide

## URLs Disponibles

### Páginas Públicas
- `/` - Landing page
- `/accounts/login/` - Iniciar sesión
- `/accounts/register/tutor/` - Registro de tutor
- `/accounts/register/client/` - Registro de estudiante

### Panel de Cliente (Estudiante)
- `/accounts/client/dashboard/` - Dashboard del estudiante
- `/tutors/` - Ver y seleccionar tutores disponibles
- `/sessions/request/<tutor_id>/` - Solicitar sesión con un tutor
- `/sessions/<session_id>/meeting/` - Sala de reunión virtual
- `/sessions/<session_id>/cancel/` - Cancelar sesión

### Panel de Tutor
- `/accounts/tutor/dashboard/` - Dashboard del tutor
- `/sessions/<session_id>/confirm/` - Confirmar sesión pendiente
- `/sessions/<session_id>/meeting/` - Iniciar reunión como host
- `/sessions/<session_id>/cancel/` - Cancelar sesión

### Sistema
- `/admin/` - Panel de administración Django
- `/accounts/logout/` - Cerrar sesión

## Credenciales de Prueba

### Superusuario (Tutor)
- Email: `ruben@subjectsupport.com`
- Password: `ruben123`
- Type: Tutor

## Cómo Probar el Sistema

### 1. Iniciar el Servidor
```bash
env/Scripts/python.exe manage.py runserver
```

### 2. Crear un Estudiante
1. Ir a: http://localhost:8000/accounts/register/client/
2. Completar formulario de registro
3. Iniciar sesión

### 3. Crear un Tutor (Alternativa)
1. Ir a: http://localhost:8000/accounts/register/tutor/
2. Completar formulario con materias
3. Iniciar sesión

### 4. Flujo Completo de Sesión

#### Como Estudiante:
1. Login → `/accounts/login/`
2. Dashboard → `/accounts/client/dashboard/`
3. Buscar Tutores → `/tutors/` (Click "Buscar Tutores")
4. Seleccionar tutor y hacer click en "Solicitar Clase"
5. Completar formulario de solicitud
6. Ver solicitud en "Solicitudes Pendientes"

#### Como Tutor:
1. Login → `/accounts/login/`
2. Dashboard → `/accounts/tutor/dashboard/`
3. Ver "Solicitudes Pendientes"
4. Click "Confirmar" en la solicitud
5. **Seleccionar plataforma de reunión** (Google Meet, Zoom, o Custom)
6. Agregar notas opcionales
7. Confirmar sesión
8. Ver sesión en "Mis Clases Próximas"
9. Click en "Iniciar" para entrar a la sala de reunión

#### Unirse a la Reunión:
1. Ambos usuarios ven la sesión confirmada en sus dashboards
2. Click en botón "Unirse" (estudiante) o "Iniciar" (tutor)
3. Se muestra la página de sala de reunión con:
   - Detalles de la sesión
   - Plataforma seleccionada
   - ID de reunión (si aplica)
   - Contraseña (si aplica - Zoom)
   - Botón para unirse al enlace externo

## Nuevas Características - Meeting Integration

### Plataformas Soportadas
- **Google Meet** - Genera URLs del estilo `https://meet.google.com/xxx-xxxx-xxx`
- **Zoom** - Genera URLs con ID de reunión y contraseña
- **Custom** - URLs personalizadas de SubjectSupport

### Campos Nuevos en Sesión
- `meeting_platform` - Plataforma seleccionada
- `meeting_url` - URL para unirse
- `meeting_id` - ID de reunión
- `meeting_password` - Contraseña (Zoom)
- `host_join_url` - URL especial para host
- `meeting_started` - Indicador si la reunión comenzó

### Flujo de Generación de Enlace
1. Tutor confirma sesión
2. Tutor selecciona plataforma (Google Meet/Zoom/Custom)
3. Sistema genera automáticamente:
   - URL única de reunión
   - ID de reunión (formato real)
   - Contraseña (para Zoom)
4. Enlace disponible inmediatamente en dashboards
5. Página profesional de sala de reunión

### Archivos Clave
- `core/models.py` - Modelo ClassSession con campos de reunión
- `core/services/meeting_service.py` - Lógica de generación de URLs
- `core/views.py` - Vista `meeting_room` para sala de reunión
- `core/templates/core/meeting_room.html` - Página profesional de reunión
- `subjectSupport/meeting_config.py` - Configuración de APIs (futuro)

## Características del Sistema

### Gestión de Usuarios
- ✅ Registro separado para tutores y estudiantes
- ✅ Autenticación basada en email
- ✅ Perfiles personalizados por tipo de usuario
- ✅ Control de acceso basado en roles
- ✅ Ubicación geográfica (ciudad, país)

### Sistema de Sesiones
- ✅ Solicitud de sesiones por estudiantes
- ✅ Confirmación/rechazo por tutores
- ✅ Estados: Pendiente → Confirmada → Completada/Cancelada
- ✅ Selección de fecha, hora y duración
- ✅ Notas adicionales
- ✅ **Selección de plataforma de video conferencia**
- ✅ **Generación automática de enlaces de reunión**

### Búsqueda Geográfica
- ✅ Priorización de tutores por ciudad
- ✅ Categorización: Misma ciudad → Mismo país → Otros
- ✅ Filtros de búsqueda por nombre/materia/ciudad
- ✅ Badges visuales de prioridad

### Dashboards
- ✅ Panel de estudiante con estadísticas
- ✅ Panel de tutor con contador de solicitudes
- ✅ Visualización de sesiones: Pendientes, Próximas, Historial
- ✅ **Mostrar plataforma de reunión**
- ✅ **Botones directos a sala de reunión**
- ✅ Acciones rápidas (Confirmar, Cancelar, Unirse)

### Meeting Integration (NUEVO)
- ✅ Soporte para Google Meet, Zoom, Custom
- ✅ Generación automática de URLs
- ✅ IDs y contraseñas únicos
- ✅ Página profesional de sala de reunión
- ✅ URLs separadas para host y participante
- ✅ Tracking de estado de reunión
- ✅ Diseño responsive y profesional
- ✅ Control de acceso (solo tutor y cliente)

### Interfaz
- ✅ Diseño moderno con Bootstrap 5
- ✅ Gradientes y colores distintivos
- ✅ Responsive (móvil y desktop)
- ✅ Mensajes de feedback con Django messages
- ✅ Iconos con Bootstrap Icons
- ✅ **Página de reunión estilo profesional**
- ✅ **Badges de plataforma**

## Tecnologías

- **Backend**: Django 5.2.8
- **Database**: SQLite
- **Frontend**: Bootstrap 5.3.0, Bootstrap Icons
- **Authentication**: Django Auth con Custom User Model
- **Meeting Service**: Custom service layer para generación de URLs

## Estructura del Proyecto

```
subjectsSuport/
├── accounts/           # App de usuarios y autenticación
│   ├── models.py      # User, TutorProfile, ClientProfile
│   ├── views.py       # Registro, login, dashboards
│   └── templates/     # Templates de autenticación
├── core/              # App principal de sesiones
│   ├── models.py      # ClassSession, TutorLead
│   ├── views.py       # Sesiones, tutores, meeting_room
│   ├── forms.py       # Formularios de sesión
│   ├── services/      # Servicios de negocio
│   │   └── meeting_service.py  # Generación de URLs
│   └── templates/     # Templates de sesiones
├── subjectSupport/    # Configuración del proyecto
│   ├── settings.py    # Configuración Django
│   ├── urls.py        # URLs principales
│   └── meeting_config.py  # Configuración de APIs
├── db.sqlite3         # Base de datos
└── manage.py          # Comando Django
```

## Comandos Útiles

```bash
# Iniciar servidor
env/Scripts/python.exe manage.py runserver

# Crear migraciones
env/Scripts/python.exe manage.py makemigrations

# Aplicar migraciones
env/Scripts/python.exe manage.py migrate

# Crear superusuario
env/Scripts/python.exe manage.py createsuperuser

# Acceder a shell
env/Scripts/python.exe manage.py shell

# Ver todas las sesiones
from core.models import ClassSession
ClassSession.objects.all()

# Ver usuarios
from accounts.models import User
User.objects.all()
```

## Estado Actual

✅ **COMPLETADO** - Integración completa de plataformas de reunión
- Modelo actualizado con campos de reunión
- Servicio de generación de URLs implementado
- Vista de sala de reunión creada
- Dashboards actualizados con información de plataforma
- Formulario de confirmación con selector de plataforma
- Migraciones aplicadas
- Sistema probado y funcional

## Próximos Pasos (Opcional)

Para integración con APIs reales:
1. Configurar Google Cloud Project para Google Meet API
2. Crear Zoom App para Zoom API
3. Instalar dependencias: `google-api-python-client`, `requests`
4. Actualizar `meeting_service.py` con llamadas a API real
5. Configurar variables de entorno en `.env`

Ver `MEETING_INTEGRATION.md` para guía completa de integración con APIs reales.
