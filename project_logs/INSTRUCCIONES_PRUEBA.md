# 🧪 INSTRUCCIONES PARA PROBAR LOS FIXES

## 📋 Pre-requisitos

Asegúrate de estar en el directorio del proyecto y tener el entorno virtual activado.

### En Windows:
```bash
cd D:\Downloads\Projects\subjectsSuport
env\Scripts\activate
```

### En Linux/Mac:
```bash
cd /path/to/subjectsSuport
source env/bin/activate
```

---

## ✅ PASO 1: Verificar Configuración

### Opción A: Script Automatizado (Recomendado)
```bash
python test_fixes.py
```

Este script verifica:
- ✓ Variables de entorno (DEBUG, ALLOWED_HOSTS, SECRET_KEY)
- ✓ Campos city/country son opcionales en TutorRegistrationForm
- ✓ Campos city/country son opcionales en ClientRegistrationForm
- ✓ Formularios validan correctamente sin city/country

### Opción B: Verificación Manual
```bash
# Verificar que Django funciona
python manage.py check

# Verificar variables de entorno
python manage.py shell
>>> from django.conf import settings
>>> print(f"DEBUG: {settings.DEBUG}")  # Debe ser True en local
>>> print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")  # Debe incluir localhost
>>> exit()
```

---

## ✅ PASO 2: Probar el Servidor

```bash
python manage.py runserver
```

Deberías ver:
```
System check identified no issues (0 silenced).
Django version 5.2.8, using settings 'subjectSupport.settings'
Starting development server at http://127.0.0.1:8000/
```

✅ **Si el servidor arranca sin error "Bad Request"** → El problema de ALLOWED_HOSTS está RESUELTO

---

## ✅ PASO 3: Probar Registro de Tutor

1. Abre el navegador en: `http://localhost:8000/accounts/register/tutor/`

2. Llena SOLO estos campos:
   - **Nombre Completo**: Juan Pérez
   - **Email**: juan@example.com
   - **Materias**: Matemáticas, Física
   - **Biografía**: (Opcional - puedes dejarlo vacío)
   - **Experiencia**: (Opcional - puedes dejarlo vacío)
   - **Contraseña**: TestPass123!
   - **Confirmar Contraseña**: TestPass123!

3. Clic en "Crear Cuenta"

✅ **Si te registra exitosamente** → El problema de campos requeridos está RESUELTO

---

## ✅ PASO 4: Probar Registro de Estudiante

1. Primero, cierra sesión o abre una ventana de incógnito

2. Abre: `http://localhost:8000/accounts/register/client/`

3. Llena SOLO estos campos:
   - **Nombre Completo**: María García
   - **Email**: maria@example.com
   - **Contraseña**: TestPass123!
   - **Confirmar Contraseña**: TestPass123!
   - (Opcional) Marca "Soy menor de edad" para probar ese flujo

4. Clic en "Crear Cuenta"

✅ **Si te registra exitosamente** → El problema está RESUELTO

---

## ✅ PASO 5: Verificar en Admin

1. Crear superusuario (si no existe):
```bash
python manage.py createsuperuser
```

2. Ir a: `http://localhost:8000/admin/`

3. Login y verificar:
   - **Usuarios** → Deben aparecer los usuarios recién creados
   - **Perfiles de Tutores** → El tutor debe tener:
     - city: "Quito" (valor por defecto)
     - country: "Ecuador" (valor por defecto)
   - **Perfiles de Clientes** → El cliente debe tener:
     - city: "Quito" (valor por defecto)
     - country: "Ecuador" (valor por defecto)

✅ **Si los perfiles tienen valores por defecto** → Los valores iniciales funcionan correctamente

---

## ✅ PASO 6: Ejecutar Tests Unitarios

```bash
# Todos los tests
python manage.py test

# Solo tests de accounts
python manage.py test accounts

# Solo tests de core
python manage.py test core
```

✅ **Si todos los tests pasan** → El proyecto está completamente funcional

---

## 🔍 Troubleshooting

### Error: "Bad Request (400)"
**Solución**: Verifica el archivo `.env`:
```bash
cat .env
# Debe contener:
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Error: "Module not found: dotenv"
**Solución**: Instalar python-dotenv:
```bash
pip install python-dotenv
```

### Error: Campos city/country todavía son requeridos
**Solución**: Verificar que los cambios en `accounts/forms.py` se guardaron:
```bash
grep "required=False" accounts/forms.py | grep -E "(city|country)"
# Deberías ver 4 líneas (2 en TutorForm, 2 en ClientForm)
```

---

## 📊 Checklist de Verificación

- [ ] El servidor arranca sin "Bad Request"
- [ ] Puedo acceder a http://localhost:8000
- [ ] Puedo registrar un tutor sin llenar city/country
- [ ] Puedo registrar un estudiante sin llenar city/country
- [ ] Los perfiles tienen valores por defecto (Quito, Ecuador)
- [ ] Los tests unitarios pasan
- [ ] Script test_fixes.py ejecuta sin errores

---

## 🚀 Siguiente Paso: Deployment a Render

Una vez que todo funciona en local, sigue las instrucciones en `RENDER_DEPLOYMENT.md` para configurar las variables de entorno en Render.
