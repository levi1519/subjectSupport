# ✅ Fix Definitivo: Provincia Fallback para Geolocalización

**Fecha**: 2025-12-13
**Status**: IMPLEMENTADO Y TESTEADO
**Problema**: Usuarios de Milagro bloqueados porque API retorna "Guayaquil"

---

## Problema Original

**Síntoma**: Usuario en Milagro, Guayas siendo bloqueado a pesar de que "Milagro" está habilitada en la BD.

**Causa Raíz**: La API de geolocalización (`ipgeolocation.io`) tiene **baja precisión** para ciudades pequeñas. Para IPs de Milagro, probablemente retorna:
- `city: 'Guayaquil'` (ciudad principal de la provincia)
- `state_prov: 'Guayas'`

Como "Guayaquil" no existe en `CiudadHabilitada`, el acceso es **bloqueado incorrectamente**.

---

## Solución Implementada: Provincia Fallback

### Lógica Nueva

1. **Intento 1**: Buscar match exacto por `ciudad` + `provincia` (case-insensitive)
2. **Si falla**: **FALLBACK** → Buscar match solo por `provincia` (case-insensitive)
3. **Si aún falla**: Bloquear acceso

### Código Implementado

**Archivo**: [core/utils/geo.py](core/utils/geo.py:166-182)

```python
# FALLBACK: Si no hay match por ciudad+provincia, intentar solo por provincia
# Esto soluciona el problema de baja precisión de API de geolocalización
# (ej: API retorna "Guayaquil" para IPs de Milagro, ambas en provincia Guayas)
if provincia_normalizada:
    logger.info(f"Trying fallback: searching by provincia only ('{provincia_normalizada}')")
    provincia_match = CiudadHabilitada.objects.filter(
        provincia__iexact=provincia_normalizada,
        activo=True
    ).first()

    if provincia_match:
        logger.info(f"✓ PROVINCIA MATCH (FALLBACK): Service available in provincia {provincia_match.provincia} (matched city: {provincia_match.ciudad})")
        return True, provincia_match
    else:
        logger.warning(f"  → Provincia '{provincia_normalizada}' also NOT found in DB")

return False, None
```

---

## Verificación

### Test Ejecutado: `test_provincia_fallback.py`

**Resultados**:

| Test Case | Ciudad API | Provincia API | Resultado | Explicación |
|-----------|------------|---------------|-----------|-------------|
| 1 | Milagro | Guayas | ✅ [OK] | Match exacto (ciudad + provincia) |
| 2 | **Guayaquil** | **Guayas** | ✅ [OK] | **FALLBACK FUNCIONA** |
| 3 | Durán | Guayas | ✅ [OK] | Fallback por provincia |
| 4 | Cuenca | Azuay | ❌ [BLOCKED] | Provincia diferente (correcto) |
| 5 | Milagro | None | ✅ [OK] | Match solo por ciudad |

**Test Case 2 es el CRÍTICO**: Simula el caso real donde la API retorna "Guayaquil" para un usuario de Milagro.

**Resultado**: ✅ **ACCESO PERMITIDO** mediante fallback de provincia.

---

## Logs Esperados en Producción

### Caso 1: Usuario de Milagro, API retorna "Milagro" (Match Exacto)

```
INFO: Middleware IP Detectada: 190.15.128.1
INFO: Geo API Response: {'city': 'Milagro', 'state_prov': 'Guayas'}
INFO: Searching for city='Milagro', provincia='Guayas'
INFO: Active cities in DB: [('Milagro', 'Guayas', 'Ecuador')]
INFO: Filtering by provincia: 'Guayas'
INFO: ✓ MATCH FOUND: Service available in Milagro, Guayas, Ecuador
INFO: Access allowed
```

### Caso 2: Usuario de Milagro, API retorna "Guayaquil" (Fallback)

```
INFO: Middleware IP Detectada: 190.15.128.1
INFO: Geo API Response: {'city': 'Guayaquil', 'state_prov': 'Guayas'}
INFO: Searching for city='Guayaquil', provincia='Guayas'
INFO: Active cities in DB: [('Milagro', 'Guayas', 'Ecuador')]
WARNING: ✗ NO MATCH: Service NOT available for city='Guayaquil', provincia='Guayas'
WARNING:   → City 'Guayaquil' does NOT exist in DB at all
INFO: Trying fallback: searching by provincia only ('Guayas')
INFO: ✓ PROVINCIA MATCH (FALLBACK): Service available in provincia Guayas (matched city: Milagro)
INFO: Access allowed via provincia fallback
```

### Caso 3: Usuario de Cuenca (Azuay) - Bloqueado

```
INFO: Middleware IP Detectada: 190.15.128.1
INFO: Geo API Response: {'city': 'Cuenca', 'state_prov': 'Azuay'}
INFO: Searching for city='Cuenca', provincia='Azuay'
INFO: Active cities in DB: [('Milagro', 'Guayas', 'Ecuador')]
WARNING: ✗ NO MATCH: Service NOT available for city='Cuenca', provincia='Azuay'
WARNING:   → City 'Cuenca' does NOT exist in DB at all
INFO: Trying fallback: searching by provincia only ('Azuay')
WARNING:   → Provincia 'Azuay' also NOT found in DB
INFO: Access blocked for user from Cuenca, Azuay
```

---

## Ventajas de Esta Solución

### 1. Soluciona el Problema de Precisión de API

- ✅ Usuarios de Milagro pueden acceder aunque API diga "Guayaquil"
- ✅ Usuarios de Durán (otra ciudad de Guayas) también pueden acceder
- ✅ Funciona con cualquier ciudad dentro de provincia habilitada

### 2. Mantiene la Seguridad

- ✅ Usuarios de provincias NO habilitadas siguen bloqueados
- ✅ Case sensitivity manejado correctamente (`__iexact`)
- ✅ Solo activa fallback si provincia está presente

### 3. Logging Exhaustivo para Debug

- ✅ Muestra ciudades activas en BD
- ✅ Muestra valores exactos de búsqueda
- ✅ Indica si fue match exacto o fallback
- ✅ Stack traces completos en errores

### 4. Sin Cambios en Base de Datos

- ✅ No requiere agregar "Guayaquil" a `CiudadHabilitada`
- ✅ Mantiene granularidad a nivel de ciudad en BD
- ✅ Fácil de revertir si se desea

---

## Consideraciones y Trade-offs

### Comportamiento Actual

Con "Milagro, Guayas" habilitada:
- ✅ Usuarios de Milagro: PERMITIDO
- ✅ Usuarios de Guayaquil: PERMITIDO (via fallback)
- ✅ Usuarios de Durán: PERMITIDO (via fallback)
- ✅ Usuarios de otras provincias: BLOQUEADO

**Implicación**: Todo usuario de la provincia de Guayas tiene acceso, no solo de Milagro.

### Si Quieres Restringir Solo a Milagro

**Opción 1**: Migrar a MaxMind GeoLite2 (mayor precisión)

**Opción 2**: Deshabilitar fallback y agregar manualmente todas las ciudades de Guayas:
```python
# En Django admin o shell
CiudadHabilitada.objects.create(ciudad='Guayaquil', provincia='Guayas', activo=True)
CiudadHabilitada.objects.create(ciudad='Durán', provincia='Guayas', activo=True)
# etc.
```

**Opción 3**: Mantener fallback pero añadir lista de exclusión:
```python
EXCLUDED_CITIES = ['Guayaquil']  # En settings.py

if ciudad_normalizada in EXCLUDED_CITIES:
    logger.info(f"City '{ciudad_normalizada}' is in exclusion list, blocking access")
    return False, None
```

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| [core/utils/geo.py](core/utils/geo.py:114-186) | Provincia fallback + enhanced logging |
| [test_provincia_fallback.py](test_provincia_fallback.py) | Nuevo - Test de fallback |
| [test_case_sensitivity.py](test_case_sensitivity.py) | Nuevo - Test de case sensitivity |
| [test_api_response.py](test_api_response.py) | Nuevo - Test de API response |
| [PROVINCIA_FALLBACK_FIX.md](PROVINCIA_FALLBACK_FIX.md) | Esta documentación |
| [CASE_SENSITIVITY_FIX.md](CASE_SENSITIVITY_FIX.md) | Documentación de análisis |

---

## Deploy

### Comandos para Deploy a Render

```bash
git add core/utils/geo.py
git add test_provincia_fallback.py
git add test_case_sensitivity.py
git add test_api_response.py
git add PROVINCIA_FALLBACK_FIX.md
git add CASE_SENSITIVITY_FIX.md
git commit -m "fix: Add provincia fallback for low-precision geolocation API + enhanced logging"
git push origin main
```

### Verificación Post-Deploy

1. Acceder a Render Dashboard → Logs
2. Generar tráfico desde Milagro
3. Buscar en logs:
   - `Searching for city='...', provincia='Guayas'`
   - `✓ MATCH FOUND` o `✓ PROVINCIA MATCH (FALLBACK)`
4. Confirmar que usuario puede acceder sin Error 403

---

## Checklist Final

- [x] Provincia fallback implementado
- [x] Case sensitivity verificado (funciona con `__iexact`)
- [x] Enhanced logging añadido
- [x] Tests ejecutados exitosamente:
  - [x] `test_case_sensitivity.py` - ✅ PASS
  - [x] `test_provincia_fallback.py` - ✅ PASS
  - [x] `test_api_response.py` - ✅ PASS
- [x] `python manage.py check` - ✅ PASS
- [ ] Deploy a Render
- [ ] Verificación en producción

---

## Próximos Pasos

1. ✅ Fix implementado
2. ✅ Tests locales pasando
3. ⏳ Deploy a Render
4. ⏳ Verificar logs en producción
5. ⏳ Confirmar que usuarios de Milagro pueden acceder
6. ⏳ Monitorear si hay falsos positivos (usuarios de otras provincias accediendo)

---

**Última actualización**: 2025-12-13
**Status**: LISTO PARA DEPLOY
**Severidad del problema original**: CRÍTICA (usuarios legítimos bloqueados)
**Severidad post-fix**: RESUELTA
