# ESQUEMA DE ARQUITECTURA - SubjectSupport

## ESTRUCTURA DE CARPETAS IMPLEMENTADA

```
subjectsSuport/
├── subjectSupport/                    # Configuración del proyecto (Root Project)
│   ├── __init__.py
│   ├── settings.py                   # Configuración principal
│   ├── urls.py                       # URLs raíz
│   ├── wsgi.py
│   ├── asgi.py
│   ├── initialization.py
│   └── meeting_config.py
│
├── apps/                             # Contenedor de aplicaciones (Apps Container)
│   ├── __init__.py
│   │
│   ├── academicTutoring/             # App: Lógica de tutoría académica
│   │   ├── __init__.py
│   │   ├── apps.py                   # name='apps.academicTutoring'
│   │   ├── admin.py
│   │   ├── models.py                 # Modelos: ClassSession, TutorLead, ServiceArea, etc.
│   │   ├── views.py                  # Vistas de sesiones, geolocalización
│   │   ├── forms.py
│   │   ├── urls.py
│   │   ├── middleware.py             # GeoRestrictionMiddleware
│   │   ├── tests.py
│   │   │
│   │   ├── requirements/             # Pipeline Architect Guard - RFC 2119
│   │   │   ├── requirements_models.json
│   │   │   └── requirements_views.json
│   │   │
│   │   ├── context/                  # Estado de capa
│   │   │   ├── context_models.json
│   │   │   └── context_views.json
│   │   │
│   │   ├── logs/                     # Auditoría y logs
│   │   │   ├── ARCHITECT_GUARD_IMPLEMENTATION.md
│   │   │   ├── ARCHITECT_GUARD_MAINTENANCE.md
│   │   │   ├── AUDIT_REPORT_ARCHITECT_GUARD.md
│   │   │   └── IMPLEMENTATION_COMPLETE.md
│   │   │
│   │   ├── migrations/               # Migraciones corregidas
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_classsession_host_join_url_*.py
│   │   │   ├── 0003_notificacionexpansion_*.py
│   │   │   ├── 0004_add_service_area_gis.py
│   │   │   ├── 0005_remove_ciudadhabilitada.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── services/                 # Servicios especializados
│   │   │   ├── __init__.py
│   │   │   └── meeting_service.py
│   │   │
│   │   ├── utils/                    # Utilidades
│   │   │   ├── __init__.py
│   │   │   └── geo.py                # Geolocalización corregida
│   │   │
│   │   ├── templates/                # Templates específicos
│   │   │   ├── core/
│   │   │   └── landing/
│   │   │
│   │   ├── fixtures/                 # Datos iniciales
│   │   │   └── ciudades_iniciales.json
│   │   │
│   │   ├── management/               # Comandos personalizados
│   │   │   ├── commands/
│   │   │   └── __init__.py
│   │   │
│   │   └── tests/                    # Tests unitarios
│   │       ├── tests_models.py
│   │       └── tests_views.py
│   │
│   └── accounts/                     # App: Autenticación y perfiles
│       ├── __init__.py
│       ├── apps.py                   # name='apps.accounts'
│       ├── admin.py
│       ├── models.py                 # User, TutorProfile, ClientProfile, Subject
│       ├── views.py                  # Vistas de autenticación corregidas
│       ├── forms.py
│       ├── urls.py
│       ├── urls_estudiantes.py
│       ├── urls_tutores.py
│       ├── serializers.py
│       ├── tests.py
│       ├── test_utils.py
│       │
│       ├── requirements/             # Pipeline Architect Guard - RFC 2119
│       │   ├── requirements_models.json    # Corregido
│       │   └── requirements_views.json     # Reescrito
│       │
│       ├── context/                  # Estado de capa
│       │   ├── context_models.json
│       │   └── context_views.json
│       │
│       ├── logs/                     # Auditoría y logs (NUEVO)
│       │   ├── DEBT_LOG.md           # Creado
│       │   └── CRITIC_REPORT.md      # Creado
│       │
│       ├── migrations/               # Migraciones existentes
│       │   ├── 0001_initial.py
│       │   ├── 0002_clientprofile_*.py
│       │   ├── 0003_subject_*.py
│       │   ├── 0004_clientprofile_*.py
│       │   ├── 0005_tutorprofile_*.py
│       │   └── __init__.py
│       │
│       ├── templates/                # Templates de autenticación
│       │   └── accounts/
│       │
│       ├── management/               # Comandos personalizados
│       │   ├── commands/
│       │   └── __init__.py
│       │
│       └── tests/                    # Tests unitarios
│           ├── tests_models.py
│           └── tests_views.py
│
├── templates/                        # Templates globales
│   ├── 404.html
│   ├── 500.html
│   ├── core/
│   ├── emails/
│   └── registration/
│
├── staticfiles/                      # Archivos estáticos
│
├── project_logs/                     # Logs del proyecto
│
├── dev_scripts/                      # Scripts de desarrollo
│
├── manage.py
├── requirements.txt
├── runtime.txt
├── render.yaml
├── build.sh
├── .env
├── .env.example
├── .gitignore
└── db.sqlite3
```

## PATRÓN IMPLEMENTADO: APPS CONTAINER

### 1. **Separación de Responsabilidades**
- **subjectSupport/**: Solo configuración del proyecto
- **apps/**: Contenedor de aplicaciones Django
  - `academicTutoring`: Dominio de tutoría (sesiones, geolocalización)
  - `accounts`: Autenticación y gestión de usuarios

### 2. **Pipeline ARCHITECT GUARD**
Cada app contiene:
- **requirements/**: Especificaciones RFC 2119 (MUST, SHOULD, MAY, MUST_NOT)
- **context/**: Estado de capa (.json)
- **logs/**: Auditoría y reportes técnicos
- **tests/**: Tests unitarios (mantenidos en ubicación original)

### 3. **Correcciones Aplicadas**
1. **Migraciones**: Dependencias de `core` → `academicTutoring`
2. **Imports**: `from core.` → `from apps.academicTutoring.`
3. **Apps.py**: Nombres completos (`apps.academicTutoring`, `apps.accounts`)
4. **Requirements**: Archivos JSON corregidos y específicos por app
5. **Logs**: Carpeta `logs/` creada en `accounts` con documentación

### 4. **Validación Exitosa**
- ✅ `python manage.py check`: 0 issues
- ✅ `python manage.py migrate`: Aplicadas correctamente
- ✅ `python manage.py runserver`: Servidor funcionando
- ✅ Estructura conforme a especificaciones

## FLUJO DE DATOS
```
Cliente → subjectSupport/urls.py → apps/[app]/urls.py → views.py
         ↓
Middleware (GeoRestriction) → models.py → templates/
         ↓
requirements/ (validación) ← context/ (estado) ← logs/ (auditoría)
```

## BENEFICIOS DE LA ARQUITECTURA
1. **Modularidad**: Apps independientes y reutilizables
2. **Auditabilidad**: Pipeline Architect Guard documentado
3. **Mantenibilidad**: Separación clara de responsabilidades
4. **Escalabilidad**: Fácil agregar nuevas apps al contenedor
5. **Consistencia**: Estructura uniforme entre apps

**Estado**: ✅ IMPLEMENTACIÓN COMPLETA Y VALIDADA