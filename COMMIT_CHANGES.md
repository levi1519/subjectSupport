# 🎯 COMANDOS PARA COMMIT DE LOS CAMBIOS

## 📋 Archivos Modificados y Creados

### Archivos Modificados ✏️
1. `subjectSupport/settings.py` - Configuración dual con variables de entorno
2. `accounts/forms.py` - Campos city/country opcionales

### Archivos Creados 📄
1. `.env` - Variables de entorno locales (NO se sube a git)
2. `.env.example` - Template de configuración
3. `FIXES_APLICADOS.md` - Documentación de fixes
4. `RENDER_DEPLOYMENT.md` - Instrucciones para Render
5. `INSTRUCCIONES_PRUEBA.md` - Guía de pruebas
6. `test_fixes.py` - Script de verificación
7. `COMMIT_CHANGES.md` - Este archivo

---

## 🔍 PASO 1: Verificar Cambios

```bash
# Ver archivos modificados
git status

# Ver diferencias en settings.py
git diff subjectSupport/settings.py

# Ver diferencias en forms.py
git diff accounts/forms.py
```

---

## 💾 PASO 2: Commit de los Cambios

### Opción A: Commit Todo Junto
```bash
# Añadir todos los archivos relevantes
git add subjectSupport/settings.py
git add accounts/forms.py
git add .env.example
git add FIXES_APLICADOS.md
git add RENDER_DEPLOYMENT.md
git add INSTRUCCIONES_PRUEBA.md
git add test_fixes.py
git add COMMIT_CHANGES.md

# Commit con mensaje descriptivo
git commit -m "fix: Resolver problemas de registro y configuración dual

- Fix registro de tutores: campos city/country ahora opcionales
- Fix registro de estudiantes: campos city/country ahora opcionales
- Fix error Bad Request en local: configuración dual con dotenv
- Add soporte para variables de entorno (.env local + Render)
- Add documentación completa de fixes y deployment
- Add script de verificación test_fixes.py

BREAKING CHANGES:
- Ahora se requiere archivo .env para desarrollo local
- Las variables DEBUG, SECRET_KEY, ALLOWED_HOSTS deben configurarse

Fixes: #N/A
Refs: fc9fa21"
```

### Opción B: Commits Separados (Más organizado)
```bash
# Commit 1: Fix de formularios
git add accounts/forms.py
git commit -m "fix: Hacer campos city/country opcionales en forms de registro

- TutorRegistrationForm: city y country ahora tienen required=False
- ClientRegistrationForm: city y country ahora tienen required=False
- Los valores por defecto del modelo (Quito, Ecuador) se aplican automáticamente

Esto resuelve el problema donde el template no mostraba estos campos
pero el formulario los requería, causando errores de validación."

# Commit 2: Fix de configuración
git add subjectSupport/settings.py .env.example
git commit -m "feat: Añadir soporte para configuración dual (local + producción)

- Integración con python-dotenv para variables de entorno
- DEBUG: configurable vía variable de entorno
- SECRET_KEY: configurable vía variable de entorno
- ALLOWED_HOSTS: configurable y soporta múltiples hosts

Esto permite que el proyecto funcione tanto en local (con .env)
como en producción (con variables de entorno del sistema).

Antes: DEBUG=False hardcoded, solo funcionaba en Render
Después: Configuración flexible que soporta desarrollo local"

# Commit 3: Documentación
git add FIXES_APLICADOS.md RENDER_DEPLOYMENT.md INSTRUCCIONES_PRUEBA.md test_fixes.py COMMIT_CHANGES.md
git commit -m "docs: Añadir documentación completa de fixes y deployment

- FIXES_APLICADOS.md: Resumen detallado de todos los cambios
- RENDER_DEPLOYMENT.md: Instrucciones para configurar Render
- INSTRUCCIONES_PRUEBA.md: Guía paso a paso para probar los fixes
- test_fixes.py: Script automatizado de verificación
- COMMIT_CHANGES.md: Guía para hacer commits"
```

---

## 🚀 PASO 3: Push a GitHub (Si aplica)

```bash
# Verificar remote
git remote -v

# Push a main (o tu rama actual)
git push origin main

# Si tienes conflictos, primero pull
git pull --rebase origin main
git push origin main
```

---

## 🔄 PASO 4: Deploy a Render

### Opción A: Auto-deploy (Si está configurado)
- Render detectará el push y hará deploy automáticamente
- Verifica en el dashboard de Render

### Opción B: Deploy Manual
1. Ir a dashboard de Render
2. Seleccionar tu servicio
3. Click en "Manual Deploy" → "Deploy latest commit"

### Opción C: Configurar Variables de Entorno en Render
**IMPORTANTE**: Antes de hacer deploy, configurar en Render → Environment:

```bash
DEBUG=False
SECRET_KEY=<genera_uno_nuevo>
ALLOWED_HOSTS=.onrender.com,tu-app.onrender.com
```

Para generar nuevo SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## ⏮️ PASO 5: Rollback (Si algo falla)

### Revertir último commit (local)
```bash
git reset --soft HEAD~1  # Mantiene cambios en staging
# o
git reset --hard HEAD~1  # Descarta cambios completamente
```

### Revertir commit específico
```bash
git revert <commit-hash>
git push origin main
```

### Volver al estado pre-fixes
```bash
# Ver commits
git log --oneline

# Volver a commit específico (sin borrar historial)
git revert --no-commit HEAD~3..HEAD
git commit -m "revert: Revertir fixes temporalmente"

# O crear una branch de backup
git branch backup-fixes
git reset --hard <commit-hash-anterior>
```

---

## 📊 Checklist Pre-Push

- [ ] He probado todos los fixes en local
- [ ] Script test_fixes.py ejecuta sin errores
- [ ] El servidor local funciona (http://localhost:8000)
- [ ] Puedo registrar tutores exitosamente
- [ ] Puedo registrar estudiantes exitosamente
- [ ] Los tests unitarios pasan
- [ ] He revisado el diff de los cambios
- [ ] El archivo .env NO está en el commit (verificar con `git status`)
- [ ] He actualizado la documentación si es necesario

---

## 🎯 Próximos Pasos Después del Commit

1. ✅ Hacer commit de los cambios
2. ✅ Push a GitHub
3. ⚠️ Configurar variables de entorno en Render (ANTES de deploy)
4. ⚠️ Generar nuevo SECRET_KEY para producción
5. ⚠️ Deploy a Render
6. ⚠️ Probar registro de tutores en producción
7. ⚠️ Probar registro de estudiantes en producción
8. ⚠️ Verificar logs de Render para errores

---

## 📞 Soporte

Si encuentras algún problema:
1. Revisa los logs: `python manage.py runserver` (local) o Render logs (producción)
2. Ejecuta: `python test_fixes.py` para diagnosticar
3. Verifica el archivo `.env` existe y tiene las variables correctas
4. Revisa `INSTRUCCIONES_PRUEBA.md` para troubleshooting
