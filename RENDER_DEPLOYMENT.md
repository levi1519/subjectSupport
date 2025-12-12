# 🚀 Configuración de Variables de Entorno en Render

## Variables de Entorno Necesarias

En el panel de Render, ve a tu servicio → **Environment** y añade estas variables:

```bash
DEBUG=False
SECRET_KEY=omae_o_zutto_aishiteru
ALLOWED_HOSTS=.onrender.com,tu-app.onrender.com
```

### Opcional (si usas PostgreSQL en Render):
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
```

## Configuración Actual del Proyecto

El proyecto ahora soporta configuración dual:
- **Local**: Lee variables de `.env`
- **Producción**: Lee variables de entorno del sistema (Render)

## Verificar Configuración

```bash
# En local
python manage.py check --deploy
```

## Notas de Seguridad

⚠️ **IMPORTANTE**: Genera un nuevo SECRET_KEY para producción:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Luego actualiza la variable en Render con el nuevo valor.
