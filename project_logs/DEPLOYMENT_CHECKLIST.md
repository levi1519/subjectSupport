# ✅ Checklist de Deployment en Render

## Pre-Deploy

### Repositorio y Código
- [ ] Código subido a GitHub en rama `main`
- [ ] Archivo `requirements.txt` actualizado y completo
- [ ] Archivo `build.sh` presente y con permisos ejecutables
- [ ] Archivo `render.yaml` configurado correctamente
- [ ] Archivo `.env.example` documentado
- [ ] Fixture `core/fixtures/ciudades_iniciales.json` existe y contiene Milagro

### Configuración Local
- [ ] `settings.py` configurado para dual mode (local/producción)
- [ ] WhiteNoise añadido a MIDDLEWARE
- [ ] Database configurada con dj-database-url
- [ ] Static files configurados (STATIC_ROOT, STATICFILES_STORAGE)
- [ ] Security settings para producción (SECURE_SSL_REDIRECT, etc.)

### Variables de Entorno Local
- [ ] Archivo `.env` creado desde `.env.example`
- [ ] `SECRET_KEY` generado y único (no usar el del ejemplo)
- [ ] `DEBUG=True` en local
- [ ] `ALLOWED_HOSTS` configurado para localhost
- [ ] Servidor local funciona correctamente

### Pruebas Locales
- [ ] `python manage.py check` sin errores
- [ ] `python manage.py migrate` exitoso
- [ ] `python manage.py collectstatic --no-input` exitoso
- [ ] `python manage.py loaddata core/fixtures/ciudades_iniciales.json` exitoso
- [ ] Tests pasan: `python manage.py test`
- [ ] Registro de tutores funciona
- [ ] Registro de estudiantes funciona

---

## Configuración en Render

### Crear Cuenta y Conectar GitHub
- [ ] Cuenta creada en [render.com](https://render.com)
- [ ] Email verificado
- [ ] Repositorio de GitHub conectado a Render
- [ ] Render tiene permisos para acceder al repositorio

### Opción A: Blueprint (Recomendado)
- [ ] Crear "New Blueprint" desde dashboard
- [ ] Seleccionar repositorio
- [ ] `render.yaml` detectado automáticamente
- [ ] Click en "Apply"
- [ ] Web Service creado automáticamente
- [ ] PostgreSQL Database creado automáticamente

### Opción B: Manual
- [ ] PostgreSQL Database creado
  - [ ] Name: `subjectsupport-db`
  - [ ] Region: Oregon (u otra cercana)
  - [ ] Plan: Free
  - [ ] Internal Database URL copiado
- [ ] Web Service creado
  - [ ] Name: `subjectsupport`
  - [ ] Runtime: Python 3
  - [ ] Build Command: `chmod +x build.sh && ./build.sh`
  - [ ] Start Command: `gunicorn subjectSupport.wsgi:application`
  - [ ] Plan: Free

---

## Variables de Entorno en Render

### Ir a: Dashboard → Web Service → Environment

- [ ] `DEBUG` = `False`
- [ ] `SECRET_KEY` = `<nuevo-secret-key-generado>` (diferente al local)
- [ ] `ALLOWED_HOSTS` = `.onrender.com`
- [ ] `DATABASE_URL` = `<auto-generado-o-copiado>` (debe comenzar con `postgresql://`)
- [ ] `CSRF_TRUSTED_ORIGINS` = `https://tu-app.onrender.com`
- [ ] `SKIP_GEO_CHECK` = `False`
- [ ] `PYTHON_VERSION` = `3.12.0`

### Validación de Variables
- [ ] Todas las variables guardadas correctamente
- [ ] SECRET_KEY es diferente al de desarrollo
- [ ] CSRF_TRUSTED_ORIGINS usa `https://` (no `http://`)
- [ ] DATABASE_URL conecta a la base de datos correcta

---

## Proceso de Deploy

### Iniciar Deploy
- [ ] Click en "Manual Deploy" → "Deploy latest commit" (si no es automático)
- [ ] O hacer `git push` para trigger auto-deploy

### Monitorear Build
- [ ] Ver logs en tiempo real (Dashboard → Logs)
- [ ] Build inicia correctamente
- [ ] Dependencias se instalan sin errores
- [ ] `collectstatic` exitoso
- [ ] Migraciones se ejecutan sin errores
- [ ] Fixture de ciudades se carga (o mensaje de "ya cargado")
- [ ] Build completa con "✅ Build completed successfully!"

### Deploy Live
- [ ] Deploy completa sin errores
- [ ] Estado: "Deploy live" (verde)
- [ ] URL asignada por Render visible

---

## Verificación Post-Deploy

### Acceso Básico
- [ ] URL de Render abre (https://tu-app.onrender.com)
- [ ] No hay error 500
- [ ] Landing page carga correctamente
- [ ] CSS/JS cargan sin errores 404

### Funcionalidad Core
- [ ] Restricción geográfica activa (desde fuera de Milagro → "Servicio no disponible")
- [ ] Formulario de notificación de expansión funciona
- [ ] Registro de tutores accesible y funciona
- [ ] Registro de estudiantes accesible y funciona
- [ ] Login funciona
- [ ] Logout funciona
- [ ] Dashboard de tutor accesible
- [ ] Dashboard de estudiante accesible

### Admin Django
- [ ] `/admin/` accesible
- [ ] Crear superusuario (si es necesario):
  ```bash
  # Dashboard → Shell
  python manage.py createsuperuser
  ```
- [ ] Login al admin exitoso
- [ ] Modelo `CiudadHabilitada` visible
- [ ] Ciudad "Milagro" existe en la base de datos
- [ ] `Milagro.activo = True`

### Base de Datos
- [ ] Migraciones aplicadas correctamente
- [ ] Tablas creadas
- [ ] Fixture cargado
- [ ] No hay errores de conexión en logs

### Logs
- [ ] No hay errores 500 en logs
- [ ] No hay errores de CSRF
- [ ] No hay errores de DisallowedHost
- [ ] Database connections OK
- [ ] Static files servidos correctamente

---

## Pruebas de Usuario

### Desde Milagro (o VPN)
- [ ] Acceso completo a la plataforma
- [ ] Registro de tutor completo
- [ ] Registro de estudiante completo
- [ ] Login exitoso
- [ ] Crear sesión de clase
- [ ] Confirmar sesión
- [ ] Acceder a sala de reunión

### Desde Fuera de Milagro
- [ ] Página "Servicio no disponible" se muestra
- [ ] Formulario de notificación funciona
- [ ] Email/datos se guardan en `ExpansionRequest` (verificar en admin)

---

## Seguridad

### Configuración HTTPS
- [ ] Render proporciona SSL automático
- [ ] URL usa `https://` (no `http://`)
- [ ] Redirección automática de HTTP a HTTPS funciona
- [ ] `SECURE_SSL_REDIRECT = True` en producción

### Headers de Seguridad
- [ ] `X-Content-Type-Options: nosniff` presente
- [ ] `X-Frame-Options: DENY` presente
- [ ] HSTS activado (verificar en headers)

### Secrets
- [ ] SECRET_KEY único y seguro (50+ caracteres)
- [ ] SECRET_KEY diferente al de desarrollo
- [ ] SECRET_KEY no está en código (solo en variables de entorno)
- [ ] `.env` en `.gitignore` (no subido a git)

---

## Rendimiento

### Carga Inicial
- [ ] Página carga en < 3 segundos (primera carga)
- [ ] Página carga en < 1 segundo (subsecuentes)
- [ ] Static files cargan rápido (comprimidos con WhiteNoise)

### Free Plan (Render)
- [ ] App se duerme después de 15 min inactividad (esperado en free plan)
- [ ] Primera request después de dormir toma ~30 seg (esperado)
- [ ] Requests subsecuentes son rápidas

---

## Monitoreo

### Métricas
- [ ] Response times < 500ms (promedio)
- [ ] No hay picos de error rate
- [ ] Memory usage estable
- [ ] CPU usage normal

### Alertas
- [ ] Configurar notificaciones de Render (opcional)
- [ ] Recibir alertas de deploy fallido
- [ ] Recibir alertas de downtime

---

## Documentación

### Interna
- [ ] `DEPLOYMENT_GUIDE.md` actualizado
- [ ] `README.md` con instrucciones de setup
- [ ] `.env.example` documentado
- [ ] Comentarios en código donde sea necesario

### Externa (Para Usuarios)
- [ ] URL de producción compartida con testers
- [ ] Instrucciones de acceso proporcionadas
- [ ] Restricción geográfica explicada

---

## Rollback Plan

### En Caso de Problemas
- [ ] Conocer cómo hacer rollback a deploy anterior
  - Dashboard → Deploys → Click en deploy anterior → "Redeploy"
- [ ] Tener backup de base de datos reciente
- [ ] Saber cómo acceder a Shell de Render para debugging

---

## Checklist Final de Go-Live

### Antes de Anunciar a Usuarios
- [ ] Todos los items anteriores completados ✅
- [ ] Aplicación estable por al menos 24 horas
- [ ] Sin errores críticos en logs
- [ ] Pruebas end-to-end exitosas
- [ ] Restricción geográfica verificada
- [ ] Fixture de Milagro confirmado
- [ ] Email de confirmación funciona (si aplica)
- [ ] Plan de contingencia preparado

### Marketing/Comunicación
- [ ] URL de producción lista para compartir
- [ ] Instrucciones de uso preparadas
- [ ] Canal de soporte definido (email, WhatsApp, etc.)
- [ ] Plan de onboarding para usuarios beta

---

## Mantenimiento Post-Deploy

### Diario (Primera Semana)
- [ ] Revisar logs para errores
- [ ] Monitorear métricas de uso
- [ ] Responder feedback de usuarios

### Semanal
- [ ] Revisar logs para patrones de error
- [ ] Verificar uso de recursos (RAM/CPU)
- [ ] Backup de base de datos

### Mensual
- [ ] Revisar y actualizar dependencias
- [ ] Analizar métricas de usuarios
- [ ] Planear nuevas features basadas en feedback

---

## Recursos de Ayuda

Si encuentras problemas, consultar:

1. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Sección Troubleshooting
2. [Render Docs](https://render.com/docs)
3. Logs de Render en tiempo real
4. Shell de Render para debugging en vivo

---

**Fecha de Deploy**: _______________

**Deployed por**: _______________

**URL de Producción**: _______________

**Notas adicionales**:
_________________________________
_________________________________
_________________________________
