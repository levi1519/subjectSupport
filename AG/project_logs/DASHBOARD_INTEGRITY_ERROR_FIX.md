# 🔧 Fix: IntegrityError en Dashboards - Prevención con Try/Except

**Fecha:** 16 de Diciembre, 2025  
**Rama:** `feature/subject-refactor`  
**Prioridad:** 🔴🔴 **P2 - ALTA** (Causa errores 500 en dashboards)  
**Estado:** ✅ COMPLETADO

---

## 📋 Problema Identificado

### ❌ Error Crítico: `IntegrityError: null value in column`

**Síntoma:**
```python
IntegrityError: null value in column "country" violates not-null constraint
DETAIL: Failing row contains (id, user_id, null, null, null, null, null, ...)
```

**Ubicación:**
- `tutor_dashboard()` - línea con `get_or_create()`
- `client_dashboard()` - línea con `get_or_create()`

**Causa Raíz:**
```python
# ❌ CÓDIGO PROBLEMÁTICO (ANTES)
profile, created = TutorProfile.objects.get_or_create(
    user=request.user
)
# PROBLEMA: get_or_create() intenta crear un perfil VACÍO
# Si TutorProfile/ClientProfile tiene campos NOT NULL (country, city)
# → IntegrityError porque no se proporcionan valores
```

---

## ✅ Solución Implementada

### 🔧 Cambios en `tutor_dashboard()`

**ANTES:**
```python
# ❌ get_or_create falla con IntegrityError
profile, created = TutorProfile.objects.get_or_create(user=request.user)
```

**DESPUÉS:**
```python
# ✅ Try/except con redirección
try:
    profile = TutorProfile.objects.get(user=request.user)
except TutorProfile.DoesNotExist:
    messages.warning(
        request, 
        'Por favor completa tu perfil antes de acceder al dashboard. '
        'Necesitamos información básica para activar tu cuenta de tutor.'
    )
    return redirect('edit_tutor_profile')
```

---

### 🔧 Cambios en `client_dashboard()`

**ANTES:**
```python
# ❌ get_or_create falla con IntegrityError
profile, created = ClientProfile.objects.get_or_create(user=request.user)
```

**DESPUÉS:**
```python
# ✅ Try/except con redirección
try:
    profile = ClientProfile.objects.get(user=request.user)
except ClientProfile.DoesNotExist:
    messages.warning(
        request, 
        'Por favor completa tu perfil antes de acceder al dashboard. '
        'Necesitamos información básica para activar tu cuenta.'
    )
    return redirect('edit_client_profile')
```

---

## 🎯 Flujo Corregido

### Usuario SIN Perfil (NUEVO FLUJO)
```
Login exitoso
    ↓
Redirigido a dashboard
    ↓
TRY: Profile.objects.get(user)
    ↓
❌ DoesNotExist exception
    ↓
✅ Mensaje warning claro
    ↓
✅ Redirect a edit_profile
    ↓
Usuario completa formulario
    ↓
Perfil guardado
    ↓
Dashboard accesible ✅
```

### Usuario CON Perfil (SIN CAMBIOS)
```
Login exitoso
    ↓
Redirigido a dashboard
    ↓
TRY: Profile.objects.get(user)
    ↓
✅ Perfil encontrado
    ↓
Dashboard renderizado ✅
```

---

## 📝 Commit

```bash
commit [hash]

fix(dashboard): Evitar IntegrityError en get_or_create y redirigir a edición de perfil si el perfil no existe

- Reemplazado get_or_create() con try/except
- Redirección a edit_tutor_profile / edit_client_profile
- Mensajes warnings informativos
- Sin IntegrityError en dashboards
```

---

## 🧪 Testing Sugerido

### Test 1: Tutor SIN Perfil
```
1. Crear usuario tipo tutor sin TutorProfile
2. Login
3. VERIFICAR: Redirigido a /profile/tutor/edit/
4. VERIFICAR: Mensaje warning visible
5. VERIFICAR: Sin error 500
```

### Test 2: Cliente SIN Perfil
```
1. Crear usuario tipo client sin ClientProfile
2. Login
3. VERIFICAR: Redirigido a /profile/client/edit/
4. VERIFICAR: Mensaje warning visible
5. VERIFICAR: Sin error 500
```

### Test 3: Usuarios CON Perfil
```
1. Login con perfil completo
2. VERIFICAR: Dashboard funciona normal
3. VERIFICAR: Sin redirecciones extras
```

---

## ✅ Beneficios

- ✅ **Sin IntegrityError:** No más errores 500
- ✅ **UX Clara:** Usuarios guiados a completar perfil
- ✅ **Datos Consistentes:** Sin perfiles vacíos en DB
- ✅ **Código Robusto:** Excepciones manejadas

---

**Documentado por:** GitHub Copilot  
**Fecha:** 16 de Diciembre, 2025  
**Estado:** ✅ COMPLETADO - Pendiente de testing manual
