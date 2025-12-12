# 🚀 Guía Completa de Deployment en Render

## 📋 Tabla de Contenidos

1. [Pre-requisitos](#pre-requisitos)
2. [Preparación del Repositorio](#preparación-del-repositorio)
3. [Configuración en Render](#configuración-en-render)
4. [Variables de Entorno](#variables-de-entorno)
5. [Proceso de Deploy](#proceso-de-deploy)
6. [Verificación Post-Deploy](#verificación-post-deploy)
7. [Troubleshooting](#troubleshooting)
8. [Mantenimiento](#mantenimiento)

---

## Pre-requisitos

### 1. Cuenta en Render
- ✅ Crear cuenta gratuita en [render.com](https://render.com)
- ✅ Verificar email

### 2. Repositorio GitHub
- ✅ Código subido a GitHub (público o privado)
- ✅ Archivos de configuración presentes:
  - `requirements.txt`
  - `build.sh`
  - `render.yaml` (opcional, recomendado)
  - `.env.example`

### 3. Archivos Necesarios
Verifica que tu repositorio contenga:

```bash
subjectsSuport/
├── build.sh                    # ✅ Script de build
├── requirements.txt            # ✅ Dependencias
├── render.yaml                 # ✅ Configuración Render (opcional)
├── .env.example                # ✅ Template de variables
├── manage.py                   # ✅ Django CLI
├── subjectSupport/
│   ├── settings.py            # ✅ Con configuración dual
│   └── wsgi.py                # ✅ WSGI application
└── core/fixtures/
    └── ciudades_iniciales.json # ✅ Fixture de ciudades
```

---

## Preparación del Repositorio

### 1. Verificar Archivos Localmente

```bash
# Activar entorno virtual
env\Scripts\activate  # Windows
# o
source env/bin/activate  # Linux/Mac

# Instalar dependencias de producción
pip install -r requirements.txt

# Verificar que build.sh es ejecutable
chmod +x build.sh  # Linux/Mac
# En Windows no es necesario

# Probar collectstatic
python manage.py collectstatic --no-input

# Verificar fixture
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

### 2. Generar SECRET_KEY para Producción

```bash
python -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#%^&*(-_=+)') for i in range(50)))"
```

**⚠️ IMPORTANTE**: Guarda este SECRET_KEY, lo necesitarás en Render.

### 3. Commit y Push al Repositorio

```bash
git add .
git commit -m "feat: Add Render deployment configuration"
git push origin main
```

---

## Configuración en Render

### Opción A: Deploy con render.yaml (Recomendado)

1. **Ir al Dashboard de Render**
   - https://dashboard.render.com

2. **Crear New Blueprint**
   - Click en "New +" → "Blueprint"
   - Seleccionar tu repositorio de GitHub
   - Render detectará automáticamente `render.yaml`
   - Click en "Apply"

3. **Render creará automáticamente**:
   - ✅ Web Service (Django app)
   - ✅ PostgreSQL Database
   - ✅ Conexión entre servicio y base de datos

4. **Configurar Variables Adicionales**
   - Ve a tu Web Service → Environment
   - Editar `CSRF_TRUSTED_ORIGINS`:
     ```
     https://tu-app-nombre.onrender.com
     ```

### Opción B: Deploy Manual

1. **Crear PostgreSQL Database**
   - Dashboard → "New +" → "PostgreSQL"
   - Name: `subjectsupport-db`
   - Database: `subjectsupport`
   - User: `subjectsupport_user`
   - Region: Oregon (o el más cercano)
   - Plan: Free
   - Click "Create Database"
   - **Copiar el Internal Database URL** (lo necesitarás después)

2. **Crear Web Service**
   - Dashboard → "New +" → "Web Service"
   - Connect tu repositorio de GitHub
   - Name: `subjectsupport`
   - Region: Oregon (mismo que la DB)
   - Branch: `main`
   - Runtime: Python 3
   - Build Command:
     ```bash
     chmod +x build.sh && ./build.sh
     ```
   - Start Command:
     ```bash
     gunicorn subjectSupport.wsgi:application
     ```
   - Plan: Free

3. **Configurar Variables de Entorno** (ver sección siguiente)

---

## Variables de Entorno

### Variables Obligatorias en Render

Ve a tu Web Service → Environment → Add Environment Variable

| Variable | Valor | Notas |
|----------|-------|-------|
| `DEBUG` | `False` | SIEMPRE False en producción |
| `SECRET_KEY` | `<tu-secret-key-generado>` | Usar el generado anteriormente |
| `ALLOWED_HOSTS` | `.onrender.com` | Permite subdominios de Render |
| `DATABASE_URL` | `<auto-generado>` | Si usaste Blueprint, ya está configurado |
| `CSRF_TRUSTED_ORIGINS` | `https://tu-app.onrender.com` | Reemplazar con tu URL real |
| `SKIP_GEO_CHECK` | `False` | Activar restricción geográfica |
| `PYTHON_VERSION` | `3.12.0` | Versión de Python |

### Cómo Obtener DATABASE_URL (si hiciste deploy manual)

1. Ve a tu PostgreSQL Database en Render
2. Copia el **Internal Database URL**
3. Pega ese valor en la variable `DATABASE_URL` de tu Web Service

**Formato esperado**:
```
postgresql://user:password@hostname:5432/database
```

### Verificar Variables

En el dashboard de Render, deberías ver algo como:

```
DEBUG = False
SECRET_KEY = qj8k2...  (oculto)
ALLOWED_HOSTS = .onrender.com
DATABASE_URL = postgres://...  (oculto)
CSRF_TRUSTED_ORIGINS = https://subjectsupport.onrender.com
SKIP_GEO_CHECK = False
PYTHON_VERSION = 3.12.0
```

---

## Proceso de Deploy

### 1. Deploy Inicial

Una vez configurado:

1. Render automáticamente ejecutará el build
2. Verás logs en tiempo real
3. El proceso incluye:
   ```
   📦 Installing dependencies...
   📁 Collecting static files...
   🗄️  Running migrations...
   🌍 Loading cities fixture...
   ✅ Build completed!
   ```

### 2. Tiempo Estimado

- Build: 3-5 minutos
- Deploy: 1-2 minutos
- **Total**: ~5-7 minutos para el primer deploy

### 3. Monitorear el Deploy

```
Dashboard → Tu Web Service → Events
```

Verás:
- ✅ Build started
- ✅ Build succeeded
- ✅ Deploy live

---

## Verificación Post-Deploy

### 1. Verificar URL de la Aplicación

Render te asignará una URL:
```
https://subjectsupport.onrender.com
```

### 2. Pruebas Básicas

#### A. Verificar que el sitio carga
```bash
curl https://tu-app.onrender.com
# Debería devolver HTML sin errores
```

#### B. Probar Restricción Geográfica

**Desde fuera de Milagro**:
- Deberías ver la página "Servicio no disponible"
- Formulario de notificación de expansión

**Desde Milagro** (o con VPN):
- Deberías acceder normalmente
- Ver la landing page completa

#### C. Probar Admin de Django

```
https://tu-app.onrender.com/admin/
```

Crear superusuario (si no lo hiciste):

```bash
# En Render Shell (Dashboard → Shell)
python manage.py createsuperuser
```

#### D. Verificar Base de Datos

En el admin:
- ✅ Revisar que existe la ciudad "Milagro" en `CiudadHabilitada`
- ✅ Verificar que `activo=True`

### 3. Revisar Logs

```
Dashboard → Tu Web Service → Logs
```

Buscar:
- ✅ Sin errores 500
- ✅ Static files servidos correctamente
- ✅ Database connections OK
- ✅ Fixture cargado sin errores

---

## Troubleshooting

### Error: "Application failed to respond"

**Causa**: Gunicorn no puede iniciar Django

**Solución**:
```bash
# Verificar en Logs si hay error de import
# Revisar que WSGI_APPLICATION en settings.py es:
WSGI_APPLICATION = 'subjectSupport.wsgi.application'

# Verificar Start Command en Render:
gunicorn subjectSupport.wsgi:application
```

### Error: "SECRET_KEY not found"

**Causa**: Variable de entorno no configurada

**Solución**:
1. Dashboard → Environment
2. Añadir `SECRET_KEY=<tu-valor>`
3. Guardar cambios
4. Render re-deployará automáticamente

### Error: "relation 'core_ciudadhabilitada' does not exist"

**Causa**: Migraciones no se ejecutaron o fixture no se cargó

**Solución**:
```bash
# En Render Shell:
python manage.py migrate
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

### Error: "DisallowedHost at /"

**Causa**: ALLOWED_HOSTS mal configurado

**Solución**:
```bash
# Verificar variable ALLOWED_HOSTS en Render:
ALLOWED_HOSTS=.onrender.com

# O específicamente:
ALLOWED_HOSTS=tu-app.onrender.com
```

### Static Files No Se Cargan (404 en CSS/JS)

**Causa**: WhiteNoise no configurado o collectstatic no ejecutado

**Solución**:
```bash
# 1. Verificar que build.sh contiene:
python manage.py collectstatic --no-input

# 2. Verificar Middleware en settings.py:
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Debe estar aquí
    ...
]

# 3. Manual deploy para forzar rebuild
Dashboard → Manual Deploy → Deploy latest commit
```

### Error: "CSRF verification failed"

**Causa**: CSRF_TRUSTED_ORIGINS mal configurado

**Solución**:
```bash
# Configurar en Render Environment:
CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com

# IMPORTANTE:
# - Usar https:// (no http://)
# - Sin barra al final
# - URL exacta de tu app
```

### Base de Datos Vacía Después de Deploy

**Causa**: Fixture no se cargó correctamente

**Solución**:
```bash
# Conectar a Render Shell
python manage.py shell

# Verificar si existe Milagro
from core.models import CiudadHabilitada
CiudadHabilitada.objects.all()

# Si está vacío, cargar manualmente:
exit()
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

### Logs: "Internal Server Error (500)"

**Pasos de diagnóstico**:

1. **Ver logs detallados**:
   ```bash
   Dashboard → Logs → Filter: "ERROR"
   ```

2. **Conectar a Shell y ejecutar check**:
   ```bash
   python manage.py check --deploy
   ```

3. **Verificar configuración de DB**:
   ```bash
   python manage.py dbshell
   # Si conecta, la DB está OK
   ```

---

## Mantenimiento

### Re-Deploy Después de Cambios

**Deploy Automático** (recomendado):
```bash
# En tu local:
git add .
git commit -m "feat: Nueva funcionalidad"
git push origin main

# Render detecta el push y hace auto-deploy
```

**Deploy Manual**:
```
Dashboard → Manual Deploy → Deploy latest commit
```

### Ver Logs en Tiempo Real

```
Dashboard → Logs → Enable Auto-scroll
```

### Acceder a Shell de Producción

```
Dashboard → Shell
```

Útil para:
- Crear superusuario
- Ejecutar comandos de Django
- Depurar problemas
- Cargar fixtures manualmente

### Backup de Base de Datos

**Método 1: Desde Render Dashboard**
```
PostgreSQL Database → Backups → Create Backup
```

**Método 2: Usando pg_dump (desde Shell)**
```bash
pg_dump $DATABASE_URL > backup.sql
```

### Monitoreo

**Métricas disponibles**:
- Response times
- Memory usage
- CPU usage
- Error rates

```
Dashboard → Metrics
```

### Escalado (Cuando tengas usuarios)

**Free Plan Limitaciones**:
- Se duerme después de 15 min de inactividad
- 750 horas/mes gratis
- 512 MB RAM

**Upgrade a Paid Plan**:
```
Dashboard → Settings → Change Plan
```

Beneficios:
- ✅ No se duerme nunca
- ✅ Más RAM/CPU
- ✅ Deploy más rápido
- ✅ SSL custom domain

---

## Checklist Final

Antes de considerar el deploy exitoso:

- [ ] Aplicación accesible en URL de Render
- [ ] Landing page carga correctamente
- [ ] Static files (CSS/JS) cargan sin 404
- [ ] Restricción geográfica funciona (prueba desde fuera de Milagro)
- [ ] Admin de Django accesible
- [ ] Ciudad "Milagro" existe en base de datos
- [ ] Formularios de registro funcionan
- [ ] Login/logout funciona
- [ ] No hay errores 500 en logs
- [ ] Variables de entorno configuradas correctamente
- [ ] SECRET_KEY es diferente al de desarrollo
- [ ] DEBUG=False en producción
- [ ] HTTPS funciona (SSL automático de Render)

---

## Recursos Adicionales

### Documentación Oficial
- [Render Docs - Django](https://render.com/docs/deploy-django)
- [Render Docs - PostgreSQL](https://render.com/docs/databases)

### Comunidad
- [Render Community Forum](https://community.render.com)

### Soporte
- [Render Support](https://render.com/support)

---

## Próximos Pasos

Una vez deployed exitosamente:

1. **Configurar Dominio Personalizado** (opcional)
   - Dashboard → Settings → Custom Domain
   - Añadir tu dominio
   - Configurar DNS

2. **Configurar Emails Reales**
   - Integrar con SendGrid, Mailgun, etc.
   - Actualizar `EMAIL_BACKEND` en settings.py

3. **Monitoreo con Sentry** (opcional)
   - Instalar `sentry-sdk`
   - Configurar en settings.py
   - Tracking de errores en producción

4. **Analytics** (opcional)
   - Google Analytics
   - Plausible
   - Mixpanel

5. **Compartir con Usuarios Beta**
   - Probar con usuarios reales de Milagro
   - Recolectar feedback
   - Iterar

---

**¡Felicidades! 🎉**

Tu aplicación Django está ahora en producción en Render.

Para preguntas o problemas, revisar la sección de [Troubleshooting](#troubleshooting) o abrir un issue en el repositorio.
