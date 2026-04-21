# EduLatam

**Plataforma de tutoría académica para estudiantes universitarios de Ecuador**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2-darkgreen)](https://www.djangoproject.com/)
[![Railway Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E)](https://railway.app/)
[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-green)](LICENSE)

## ¿Qué es EduLatam?

EduLatam es una plataforma web que conecta estudiantes universitarios ecuatorianos con tutores académicos calificados para recibir clases en línea mediante videoconferencia. La plataforma automatiza todo el proceso: desde la búsqueda y solicitud de clases, hasta la confirmación y realización de sesiones.

El flujo de uso es simple: el estudiante busca un tutor por nombre, materia o área de conocimiento; solicita una clase adjuntando material de estudio si lo desea; el tutor acepta o rechaza la solicitud; una vez aceptada, el tutor comparte el enlace de videoconferencia; y finalmente se realiza la sesión en línea.

Toda la plataforma está geográficamente restringida a Ecuador. El sistema detecta automáticamente la ubicación del usuario mediante su dirección IP y solo permite acceso a usuarios ubicados en el país.

## Funcionalidades principales

**Para Tutores:**
- Gestión de materias agrupadas por área de conocimiento (máximo 5)
- Configuración de tarifa por hora en dólares
- Foto de perfil mediante URL
- Aceptar o rechazar solicitudes de clase desde su dashboard
- Compartir enlace de videoconferencia (Google Meet, Zoom u otro)
- Historial completo de sesiones y su estado

**Para Estudiantes:**
- Búsqueda de tutores por nombre, materia o área de conocimiento
- Filtro de tutores por país (configurable desde administración)
- Solicitar clase especificando fecha, hora, duración y material adjunto (URL)
- Ver tarifa del tutor antes de confirmar solicitud
- Historial de sesiones reservadas y completadas

**Del Sistema:**
- Restricción geográfica por detección de IP (Ecuador activo, otros países configurables)
- Detección automática de ciudad en el momento del registro
- Interfaz responsiva con Bootstrap 5 para móviles y escritorio
- Notificación automática cuando una sesión es cancelada

## Roles y usuarios

**TUTOR**
Se registra en `/tutores/` completando nombre, email, materias, tarifa y biografía. Recibe solicitudes de clase en su dashboard, puede aceptar o rechazar según disponibilidad, comparte el enlace de videoconferencia, y puede cancelar sesiones pendientes. Acceso a: Dashboard, Mi Perfil, Mis Materias.

**ESTUDIANTE**
Se registra en `/estudiantes/` con nombre, email y contraseña. Accede al buscador de tutores, solicita clases con material adjunto, recibe confirmación con el enlace de reunión, y puede cancelar sesiones. Acceso a: Dashboard, Mi Perfil, Buscar Tutores.

**ADMINISTRADOR**
Accede al panel administrativo con credenciales especiales. Gestiona usuarios, materias, áreas de conocimiento y países. Puede activar o desactivar países desde el panel de control.

## Stack tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|----------|
| Backend | Django 5.2 + Python 3.12 | Lógica de negocio y vistas |
| Base de datos | PostgreSQL + PostGIS (Supabase) | Almacenamiento y consultas espaciales |
| Deploy | Railway + Nixpacks | Hosting y CI/CD automático |
| Frontend | Bootstrap 5 + Django Templates | Interfaz responsiva |
| Geolocalización | ipgeolocation.io | Detección de país por IP |
| Reuniones | Google Meet / Zoom | Videoconferencias (enlace externo) |

## Estructura del proyecto

```
apps/accounts/           Modelos y lógica de usuarios, tutores y estudiantes
apps/academicTutoring/   Modelos de sesiones, países y configuración
geoconfig/               Middleware y lógica de geo-restricción
templates/               Templates HTML base y landing pages
static/                  CSS y recursos estáticos
subjectSupport/          Configuración principal de Django
```

## Configuración local — paso a paso

1. **Clonar el repositorio**
   ```bash
   git clone <URL-del-repo>
   cd subjectsSuport
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv env
   ```

3. **Activar entorno e instalar dependencias**
   ```bash
   # Windows
   env\Scripts\activate
   # macOS/Linux
   source env/bin/activate
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus valores
   ```

5. **Aplicar migraciones**
   ```bash
   python manage.py migrate
   ```

6. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   ```

7. **Iniciar servidor de desarrollo**
   ```bash
   python manage.py runserver
   ```

**Nota:** GDAL no es necesario en desarrollo local. PostGIS funciona solo en producción con Railway + Supabase.

## Variables de entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DEBUG` | Modo desarrollo | `True` |
| `SECRET_KEY` | Clave secreta Django (50+ caracteres) | `cambiar-por-clave-segura` |
| `ALLOWED_HOSTS` | Hosts permitidos separados por coma | `localhost,127.0.0.1` |
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:pass@host/db` |
| `CSRF_TRUSTED_ORIGINS` | Orígenes de confianza CSRF | `https://tuapp.railway.app` |
| `SKIP_GEO_CHECK` | Omitir verificación geo (solo desarrollo) | `True` |
| `IPGEOLOCATION_API_KEY` | Clave API para geolocalización | `tu-clave-aqui` |

## Deploy en Railway

1. Conectar el repositorio de GitHub en Railway
2. Configurar variables de entorno en el dashboard de Railway
3. Railway detecta automáticamente la configuración con Nixpacks
4. Las migraciones se ejecutan automáticamente en cada deploy
5. El servidor inicia con Gunicorn en el puerto 8080

**Nota:** Los archivos `nixpacks.toml` y `build.sh` están en la raíz del proyecto.

## Flujo de desarrollo recomendado

Rama principal de desarrollo: `latam-mvp`. Los cambios se hacen en `latam-mvp` y se mergean a `main` al estabilizar. Cada cambio debe ser quirúrgico: un archivo, un problema. Verificar estado con `git status` antes de modificar. Después de cada sesión: `git diff` para confirmar que solo se modificaron los archivos esperados. Mensajes de commit en formato: `tipo: descripción corta` (ejemplo: `fix: error en búsqueda de tutores`, `feat: campo material_url en solicitud`).

## Decisiones arquitecturales clave

- **Capa de servicios:** Toda la lógica de negocio vive en `services.py`, las vistas solo coordinan y delegan.
- **Managers personalizados:** Todas las consultas a la base de datos se hacen a través de managers (`TutorProfileManager`, `ClientProfileManager`) — nunca ORM directo en vistas.
- **Geo-restriction:** Un middleware intercepta todas las solicitudes y verifica el país del visitante antes de permitir acceso.
- **subjects_taught:** El campo de materias del tutor apunta al modelo `Subject` — no a `SubjectLevel`.

## Licencia

MIT License — ver archivo [LICENSE](LICENSE)
