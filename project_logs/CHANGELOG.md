# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.1] - 2025-12-13

### 🔒 Security & GeoIP Hardening

#### Fixed

- **[CRITICAL] Fallo de seguridad por acceso a registro de estudiantes**
  - Los usuarios fuera de Milagro podían acceder directamente a `/accounts/register/client/` sin validación geográfica adecuada
  - Se implementó validación estricta en `register_client()` que verifica la ubicación antes de permitir el registro
  - Usuarios de otras ciudades de Ecuador son redirigidos automáticamente a `tutor_landing` con mensaje informativo

- **[CRITICAL] Redirección incorrecta en la raíz para usuarios fuera de Milagro**
  - La lógica de `GeoRootRouterView` permitía que algunos usuarios no-Milagro accedieran a la landing de estudiantes
  - Se fortaleció la lógica de enrutamiento geográfico:
    - `Milagro` → `/estudiantes/` (landing de estudiantes)
    - `Resto de Ecuador` → `/tutores/` (landing de tutores) - **Blindaje estricto**
    - `Fuera de Ecuador` → `/servicio-no-disponible/`

- **[CRITICAL] Errores NoReverseMatch en formularios de registro**
  - `register_tutor()` redirigía a `'dashboard'` genérico causando errores en producción
  - `register_client()` redirigía a `'dashboard'` genérico causando errores en producción
  - **Solución**: Cambio a redirecciones específicas:
    - Tutores → `'tutor_dashboard'`
    - Clientes → `'client_dashboard'`

- **[CRITICAL] Error 500 post-registro por redirección a URL obsoleta**
  - El sistema intentaba usar URLs no configuradas o renombradas después del registro
  - Se sincronizaron todas las redirecciones con los nombres correctos definidos en `urls.py`

#### Added

- **Lógica de Geo-bloqueo estricto en `student_landing_view`**
  - Implementación de doble capa de protección para acceso a landing de estudiantes
  - Usuarios que intentan acceder directamente a `/estudiantes/` desde fuera de Milagro ahora ven una página informativa (`city_locked.html`) en lugar de ser redirigidos
  - La página de bloqueo incluye:
    - Mensaje amigable explicando la restricción geográfica
    - Detección y visualización de la ubicación del usuario
    - Botón destacado para acceso a landing de tutores
    - Opción para recibir notificaciones cuando el servicio llegue a su ciudad
    - Diseño responsive y moderno coherente con la plataforma

- **Template `core/templates/core/city_locked.html`**
  - Nueva página de bloqueo geográfico para estudiantes
  - Diseño profesional con gradientes y animaciones
  - Mensajes contextuales basados en la ubicación detectada
  - Call-to-action claro para tutores
  - Información sobre características de la plataforma

#### Changed

- **Mejora en logging de seguridad**
  - `GeoRootRouterView` ahora registra todos los intentos de acceso con información detallada de geolocalización
  - `student_landing_view` registra intentos de acceso no autorizados desde fuera de Milagro
  - `register_client()` registra con nivel `ERROR` intentos de registro desde ubicaciones no permitidas

- **Documentación de código mejorada**
  - Actualización de docstrings en vistas críticas para reflejar la nueva lógica de seguridad
  - Comentarios en línea más descriptivos sobre restricciones geográficas
  - Documentación clara de flujos de redirección

#### Security

- **Endurecimiento de controles de acceso geográfico**
  - Validación en múltiples capas (middleware + vistas)
  - Fallback robusto cuando los datos de geolocalización no están disponibles
  - Prevención de bypass mediante acceso directo a URLs

- **Protección contra acceso no autorizado**
  - Blindaje de rutas de estudiantes para usuarios fuera de Milagro
  - Validación case-insensitive para nombres de ciudades
  - Mensajes de error informativos sin exponer detalles del sistema

---

## [1.0.0] - 2025-12-XX

### Initial Release

- Lanzamiento inicial de SubjectSupport
- Sistema de autenticación con tipos de usuario (Tutor/Cliente)
- Gestión de sesiones de tutoría
- Integración con plataformas de videoconferencia (Zoom, Google Meet, Microsoft Teams)
- Sistema de geolocalización básico
- Panel de administración Django
- Dashboards diferenciados para tutores y estudiantes
- Sistema de notificaciones de expansión geográfica
