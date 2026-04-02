# REPORTE DE TRAZABILIDAD: PROYECCIONES RFC 2119

## RESUMEN DE DESCENTRALIZACIÓN

### ✅ ESTRUCTURA DE HERENCIA IMPLEMENTADA

**Padre (Ground Truth):** `apps/globalRequirements.json`
**Hijos (Proyecciones Técnicas):**
1. `apps/academicTutoring/requirements/requirements_security.json` (Middleware)
2. `apps/academicTutoring/requirements/requirements_forms.json` (Forms)
3. `apps/accounts/requirements/requirements_serializers.json` (Serializers)

### ✅ REGLAS DE HERENCIA CUMPLIDAS

#### 1. **PROYECCIÓN FUNCIONAL**
- Cada archivo hijo es una proyección funcional de los requisitos globales
- Los contratos técnicos implementan los criterios de aceptación del negocio
- No hay contradicciones entre padres e hijos

#### 2. **VALIDACIÓN REDUNDANTE**
- Cada regla se satisface en dos niveles:
  - **Nivel Padre (Negocio):** Criterios de aceptación globales
  - **Nivel Hijo (Técnico):** Implementación específica por capa
- Validación redundante garantiza consistencia

#### 3. **TRAZABILIDAD COMPLETA**
- Cada requisito técnico referencia IDs de requisitos globales
- Mapeo bidireccional mediante atributos `parent_trace`
- Estructura de `traceability` en cada archivo hijo

## MAPEO DETALLADO DE REQUISITOS

### 🔐 **CAPA DE SEGURIDAD (Middleware)**

**Archivo:** `apps/academicTutoring/requirements/requirements_security.json`

#### Mapeo Global → Técnico:
- **GEO-001 a GEO-009** → Verificación geográfica y restricciones
- **SEC-001 a SEC-008** → Políticas de seguridad generales
- **REQ-SEC-001** → GeoRestrictionMiddleware (17 referencias padre)
- **REQ-SEC-002** → Path-Based Access Policies (6 referencias padre)

#### Contratos Técnicos Implementados:
1. **Ejecución de verificaciones Milagro antes del dispatch de vistas**
2. **Contratos de respuesta 403 Forbidden para solicitudes fuera de límites**
3. **Políticas de acceso basadas en rutas URL**
4. **Exclusión de rutas específicas (admin, static, logout)**
5. **Bypass para usuarios autenticados**

### 📝 **CAPA DE VALIDACIÓN (Forms)**

**Archivo:** `apps/academicTutoring/requirements/requirements_forms.json`

#### Mapeo Global → Técnico:
- **DV-001 a DV-008** → Reglas de validación de datos
- **AUTH-001 a AUTH-010** → Reglas de autenticación
- **4 formularios con trazabilidad completa**

#### Contratos Técnicos Implementados:
1. **Validación del lado del servidor que coincide con Criterios de Aceptación Globales**
2. **Métodos clean() que previenen conflictos de programación identificados en lógica Global**
3. **Validación de formato de email usando EmailField de Django**
4. **Restricciones de longitud máxima para campos de texto**
5. **Mensajes de error personalizados en español**

### 🔄 **CAPA DE EXPOSICIÓN DE DATOS (Serializers)**

**Archivo:** `apps/accounts/requirements/requirements_serializers.json`

#### Mapeo Global → Técnico:
- **AUTH-001 a AUTH-010** → Reglas de autenticación y privacidad
- **SEC-001 a SEC-008** → Políticas de seguridad de datos
- **DV-001 a DV-008** → Validación de integridad de datos
- **4 módulos de serializadores con trazabilidad completa**

#### Contratos Técnicos Implementados:
1. **MUST_NOT estrictos para exponer campos sensibles (password, internal_location)**
2. **Campos de solo lectura obligatorios para prevenir escalación de roles durante actualizaciones de Perfil**
3. **Principio de mínimo privilegio para exposición de datos**
4. **Protección de información personal sensible en vistas de lista**
5. **Validación de relaciones anidadas con profundidad apropiada**

## VERIFICACIÓN DE CONSISTENCIA

### ✅ **NO CONTRADICCIÓN**
- Los contratos MUST de hijos no contradicen MUST de padres
- Los contratos MUST_NOT de hijos refuerzan MUST_NOT de padres
- Los contratos MAY de hijos son extensiones válidas de padres

### ✅ **COMPLETITUD**
- Todos los criterios de aceptación globales tienen proyecciones técnicas
- Cada capa técnica cubre su dominio de responsabilidad específico
- Los arrays `out_of_scope` definen claramente los límites de responsabilidad

### ✅ **TRACEABILITY**
- Atributo `parent_requirements` en cada archivo hijo
- Atributo `parent_trace` en cada requisito técnico
- Objeto `traceability` que mapea categorías globales → IDs técnicos

## ESTRUCTURA DE REFERENCIA RFC 2119

### **PADRE (globalRequirements.json)**
```json
{
  "authentication": { "MUST": ["AUTH-001", ...], "MUST_NOT": [...] },
  "geolocation": { "MUST": ["GEO-001", ...], "MUST_NOT": [...] },
  "security": { "MUST": ["SEC-001", ...], "MUST_NOT": [...] },
  "data_validation": { "MUST": ["DV-001", ...], "MUST_NOT": [...] }
}
```

### **HIJO (requirements_security.json)**
```json
{
  "parent_requirements": "apps/globalRequirements.json",
  "traceability": {
    "geolocation_must": ["GEO-001", "GEO-002", ...],
    "security_must": ["SEC-001", "SEC-002", ...]
  },
  "requirements": [{
    "id": "REQ-SEC-001",
    "parent_trace": ["GEO-001", "GEO-002", "SEC-001", ...],
    "contracts": {
      "MUST": [
        "Middleware MUST intercept all requests... (GEO-001, GEO-002, GEO-003)",
        "Middleware MUST return 403 Forbidden... (GEO-006, SEC-004)"
      ]
    }
  }]
}
```

## BENEFICIOS DE LA ARQUITECTURA DESCENTRALIZADA

### 1. **SEPARACIÓN DE PREOCUPACIONES**
- **Negocio:** Requisitos funcionales en globalRequirements.json
- **Técnico:** Implementación específica por capa en archivos hijos

### 2. **MANTENIBILIDAD**
- Cambios en requisitos de negocio → Actualización centralizada
- Cambios en implementación técnica → Aislamiento por capa
- Trazabilidad bidireccional para auditoría

### 3. **AUDITORÍA DE SEGURIDAD**
- Contratos MUST_NOT explícitos para prevención de fugas de datos
- Validación redundante entre capas
- Logging de decisiones de acceso geográfico

### 4. **CALIDAD DEL CÓDIGO**
- Contratos RFC 2119 específicos por módulo
- Definición clara de out_of_scope por capa
- Consistencia en mensajes de error y validación

## CONCLUSIÓN

La descentralización de `globalRequirements.json` en contratos RFC 2119 específicos por capa ha sido implementada exitosamente con:

1. **Trazabilidad completa** entre requisitos de negocio y implementación técnica
2. **Validación redundante** que garantiza consistencia entre capas
3. **Separación clara** de responsabilidades por dominio técnico
4. **Contratos RFC 2119** que reflejan fielmente la implementación actual del código

La arquitectura resultante proporciona una base sólida para desarrollo futuro, auditoría de seguridad y mantenimiento del proyecto 'SubjectSupport'.