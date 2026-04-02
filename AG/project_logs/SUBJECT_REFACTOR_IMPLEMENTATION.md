# 🎯 Refactorización de Asignaturas - Arquitectura Level + SubjectLevel

**Fecha:** 16 de Diciembre, 2025  
**Rama:** `feature/subject-refactor`  
**Prioridad:** 🔵🔵🔵🔵 **P4 - REFACTORIZACIÓN ARQUITECTÓNICA**  
**Estado:** ✅ MODELOS IMPLEMENTADOS - Pendiente de migración

---

## 📋 Objetivo de la Refactorización

Implementar una arquitectura de datos más robusta que permita:
- ✅ Asociar materias con niveles educativos específicos
- ✅ Búsqueda más precisa de tutores por materia Y nivel
- ✅ Mejor UX al filtrar tutores según necesidades del estudiante
- ✅ Escalabilidad para futuras funcionalidades (precios por nivel, etc.)

---

## 🏗️ Arquitectura Anterior vs Nueva

### ❌ Arquitectura Anterior (Limitada)

```
TutorProfile
    ↓
subjects (ManyToMany)
    ↓
Subject (Matemáticas, Física, Química...)
```

**Problemas:**
- ❌ No distingue entre "Matemáticas de Primaria" vs "Matemáticas de Universidad"
- ❌ Búsquedas imprecisas (tutor puede enseñar nivel que no domina)
- ❌ UX confusa para estudiantes
- ❌ Dificulta implementar precios diferenciados por nivel

---

### ✅ Arquitectura Nueva (Mejorada)

```
TutorProfile
    ↓
subjects_taught (ManyToMany)
    ↓
SubjectLevel
    ├─ subject → Subject (Matemáticas)
    └─ level → Level (Primaria, Universidad)
```

**Beneficios:**
- ✅ Tutores especifican EXACTAMENTE qué nivel enseñan por materia
- ✅ Búsquedas precisas: "Matemáticas de Universidad" vs "Matemáticas de Primaria"
- ✅ Mejora UX: estudiante encuentra tutor adecuado a su nivel
- ✅ Escalable: permite precios diferenciados, certificaciones por nivel, etc.

---

## 📝 Modelos Implementados

### 1️⃣ Modelo `Level` (Nivel Educativo)

**Archivo:** `core/models.py`

```python
class Level(models.Model):
    """
    Modelo para niveles educativos (ej: Primaria, Secundaria, Universidad).
    
    Permite organizar las materias por nivel académico para mejor filtrado
    y búsqueda de tutores según el nivel que necesita el estudiante.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre del Nivel',
        help_text='Ej: Primaria, Secundaria, Bachillerato, Universidad'
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización (menor primero)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Nivel Educativo'
        verbose_name_plural = 'Niveles Educativos'

    def __str__(self):
        return self.name
```

**Características:**
- ✅ **`name`**: Nombre único del nivel (ej: "Primaria", "Universidad")
- ✅ **`order`**: Control de orden de visualización
- ✅ **`unique=True`**: No duplicados
- ✅ **Ordering automático** por `order` y `name`

**Ejemplos de Datos:**
```python
Level.objects.create(name="Primaria", order=1)
Level.objects.create(name="Secundaria", order=2)
Level.objects.create(name="Bachillerato", order=3)
Level.objects.create(name="Universidad", order=4)
Level.objects.create(name="Postgrado", order=5)
```

---

### 2️⃣ Modelo `SubjectLevel` (Materia por Nivel)

**Archivo:** `core/models.py`

```python
class SubjectLevel(models.Model):
    """
    Modelo intermedio que relaciona Subject con Level.
    
    Permite que una misma materia (ej: Matemáticas) exista en múltiples
    niveles educativos (Matemáticas de Primaria, Matemáticas de Universidad).
    Los tutores especifican qué combinación Subject+Level pueden enseñar.
    """
    subject = models.ForeignKey(
        'accounts.Subject',
        on_delete=models.CASCADE,
        related_name='subject_levels',
        verbose_name='Materia'
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='subject_levels',
        verbose_name='Nivel'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('subject', 'level')]
        ordering = ['level__order', 'subject__name']
        verbose_name = 'Materia por Nivel'
        verbose_name_plural = 'Materias por Nivel'

    def __str__(self):
        return f"{self.subject.name} - {self.level.name}"
```

**Características:**
- ✅ **Relación ForeignKey** a `Subject` y `Level`
- ✅ **`unique_together`**: No duplicar misma materia+nivel
- ✅ **Ordering inteligente**: Por nivel (order) y materia (alfabético)
- ✅ **Representación clara**: "Matemáticas - Universidad"

**Ejemplos de Datos:**
```python
# Matemáticas en todos los niveles
SubjectLevel.objects.create(subject=matematicas, level=primaria)
SubjectLevel.objects.create(subject=matematicas, level=secundaria)
SubjectLevel.objects.create(subject=matematicas, level=universidad)

# Química solo en niveles avanzados
SubjectLevel.objects.create(subject=quimica, level=secundaria)
SubjectLevel.objects.create(subject=quimica, level=universidad)
```

---

### 3️⃣ Actualización de `TutorProfile`

**Archivo:** `accounts/models.py`

```python
class TutorProfile(models.Model):
    """Profile for tutors with additional information"""
    user = models.OneToOneField(...)
    
    # ✅ NUEVO: Relación con SubjectLevel (Materia + Nivel)
    subjects_taught = models.ManyToManyField(
        'core.SubjectLevel',
        related_name='tutors',
        verbose_name='Materias y Niveles',
        blank=True,
        help_text='Materias y niveles educativos que enseña este tutor'
    )
    
    # ⚠️ LEGACY: Mantener por compatibilidad durante migración
    subjects = models.ManyToManyField(
        Subject,
        related_name='tutors_legacy',
        verbose_name='Materias (Legacy)',
        blank=True,
        help_text='[DEPRECADO] Use subjects_taught en su lugar'
    )
    
    # ... resto de campos
```

**Cambios:**
- ✅ **Nuevo campo `subjects_taught`**: Apunta a `SubjectLevel`
- ⚠️ **Campo legacy `subjects`**: Mantenido temporalmente
- ✅ **`related_name` cambiado**: `tutors_legacy` para evitar conflicto
- ✅ **Documentación clara**: Help text indica deprecación

---

## 🎨 Administración Django

### 1️⃣ `LevelAdmin` - Gestión de Niveles

**Archivo:** `core/admin.py`

```python
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    """
    Admin configuration for Level model.
    Permite gestionar niveles educativos (Primaria, Secundaria, etc.).
    """
    list_display = ['name', 'order', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']
    list_editable = ['order']
```

**Características:**
- ✅ **`list_editable = ['order']`**: Cambiar orden inline
- ✅ Búsqueda por nombre
- ✅ Filtros por fecha de creación
- ✅ Campos readonly para auditoría

---

### 2️⃣ `SubjectLevelAdmin` - Gestión de Combinaciones

**Archivo:** `core/admin.py`

```python
@admin.register(SubjectLevel)
class SubjectLevelAdmin(admin.ModelAdmin):
    """
    Admin configuration for SubjectLevel model.
    Permite gestionar combinaciones de Materia + Nivel Educativo.
    """
    list_display = ['subject', 'level', 'created_at']
    list_filter = ['level', 'subject', 'created_at']
    search_fields = ['subject__name', 'level__name']
    readonly_fields = ['created_at']
    ordering = ['level__order', 'subject__name']
    autocomplete_fields = ['subject']
    
    actions = ['duplicate_for_all_levels']
    
    def duplicate_for_all_levels(self, request, queryset):
        """Duplicar materias seleccionadas en todos los niveles"""
        # ... implementación
```

**Características:**
- ✅ **Acción personalizada**: Duplicar materia en todos los niveles
- ✅ **Autocomplete** para búsquedas rápidas
- ✅ **Filtros** por nivel y materia
- ✅ **Búsqueda** en campos relacionados (subject__name, level__name)

---

### 3️⃣ `TutorProfileAdmin` - Actualizado para ambos campos

**Archivo:** `accounts/admin.py`

```python
@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    """Admin configuration for TutorProfile model"""
    list_display = [
        'user', 
        'get_subjects_taught_display',  # ✅ NUEVO
        'get_subjects_legacy_display',  # ⚠️ LEGACY
        'hourly_rate', 
        'phone_number', 
        'created_at'
    ]
    filter_horizontal = ['subjects_taught', 'subjects']  # Ambos durante transición

    def get_subjects_taught_display(self, obj):
        """Display SubjectLevel combinations"""
        subject_levels = obj.subjects_taught.all()[:3]
        return ", ".join([f"{sl.subject.name} ({sl.level.name})" for sl in subject_levels]) or "Ninguno"
    get_subjects_taught_display.short_description = 'Materias + Niveles (Nuevo)'

    def get_subjects_legacy_display(self, obj):
        """Display legacy subjects"""
        subjects = obj.subjects.all()[:3]
        return ", ".join([subject.name for subject in subjects]) or "Ninguno"
    get_subjects_legacy_display.short_description = 'Materias (Legacy)'
```

**Características:**
- ✅ **Dos columnas**: Nueva y legacy para comparación
- ✅ **Display mejorado**: Muestra "Matemáticas (Universidad)"
- ✅ **Transición suave**: Ambos campos visibles durante migración

---

## 📊 Comparación de Queries

### ❌ Query Anterior (Limitado)

```python
# Buscar tutores que enseñan Matemáticas
# PROBLEMA: No distingue nivel
tutors = TutorProfile.objects.filter(subjects__name='Matemáticas')

# Resultado: Mezcla tutores de primaria con universidad ❌
```

---

### ✅ Query Nueva (Preciso)

```python
# Buscar tutores que enseñan Matemáticas de Universidad
matematicas_universidad = SubjectLevel.objects.get(
    subject__name='Matemáticas',
    level__name='Universidad'
)

tutors = TutorProfile.objects.filter(subjects_taught=matematicas_universidad)

# Resultado: Solo tutores calificados para nivel universitario ✅
```

---

## 🎯 Ejemplos de Uso

### Ejemplo 1: Crear Niveles Iniciales

```python
# Script de poblado inicial
from core.models import Level

niveles = [
    {'name': 'Primaria', 'order': 1},
    {'name': 'Secundaria', 'order': 2},
    {'name': 'Bachillerato', 'order': 3},
    {'name': 'Universidad', 'order': 4},
    {'name': 'Postgrado', 'order': 5},
]

for nivel_data in niveles:
    Level.objects.get_or_create(**nivel_data)
```

---

### Ejemplo 2: Crear SubjectLevels para Matemáticas

```python
from accounts.models import Subject
from core.models import Level, SubjectLevel

# Obtener materia y niveles
matematicas = Subject.objects.get(name='Matemáticas')
primaria = Level.objects.get(name='Primaria')
secundaria = Level.objects.get(name='Secundaria')
universidad = Level.objects.get(name='Universidad')

# Crear combinaciones
SubjectLevel.objects.create(subject=matematicas, level=primaria)
SubjectLevel.objects.create(subject=matematicas, level=secundaria)
SubjectLevel.objects.create(subject=matematicas, level=universidad)
```

---

### Ejemplo 3: Asignar SubjectLevels a Tutor

```python
from accounts.models import TutorProfile
from core.models import SubjectLevel

# Obtener tutor
tutor = TutorProfile.objects.get(user__email='tutor@example.com')

# Obtener combinaciones que enseña
mat_universidad = SubjectLevel.objects.get(subject__name='Matemáticas', level__name='Universidad')
fis_universidad = SubjectLevel.objects.get(subject__name='Física', level__name='Universidad')

# Asignar
tutor.subjects_taught.add(mat_universidad, fis_universidad)
```

---

### Ejemplo 4: Búsqueda de Tutores por Nivel

```python
# Estudiante de Universidad busca tutor de Matemáticas
matematicas_universidad = SubjectLevel.objects.get(
    subject__name='Matemáticas',
    level__name='Universidad'
)

tutors_calificados = TutorProfile.objects.filter(
    subjects_taught=matematicas_universidad
)

print(f"Encontrados {tutors_calificados.count()} tutores calificados")
```

---

## 🔄 Plan de Migración (Siguiente Fase)

### Fase 1: Crear Datos Base ✅ (Pendiente de ejecución)
```bash
# Después de makemigrations y migrate
python manage.py populate_levels  # Crear niveles iniciales
python manage.py populate_subject_levels  # Crear combinaciones
```

### Fase 2: Migrar Datos Existentes ⏳
```python
# Script de migración de datos legacy
from accounts.models import TutorProfile
from core.models import SubjectLevel, Level

# Para cada tutor con subjects legacy
for tutor in TutorProfile.objects.all():
    # Asumir nivel "General" o "Universidad" por defecto
    nivel_default = Level.objects.get(name='Universidad')
    
    for subject in tutor.subjects.all():
        # Obtener o crear SubjectLevel
        subject_level, _ = SubjectLevel.objects.get_or_create(
            subject=subject,
            level=nivel_default
        )
        # Agregar a subjects_taught
        tutor.subjects_taught.add(subject_level)
```

### Fase 3: Actualizar Vistas y Forms ⏳
```python
# Actualizar forms.py para usar subjects_taught
class TutorSubjectsForm(forms.ModelForm):
    class Meta:
        model = TutorProfile
        fields = ['subjects_taught']  # Cambiar de 'subjects' a 'subjects_taught'
```

### Fase 4: Actualizar Templates ⏳
```django
{# Actualizar templates para mostrar nivel #}
{% for subject_level in tutor.subjects_taught.all %}
    <span>{{ subject_level.subject.name }} - {{ subject_level.level.name }}</span>
{% endfor %}
```

### Fase 5: Eliminar Campo Legacy ⏳
```python
# Después de verificar que todo funciona
class TutorProfile(models.Model):
    # ... otros campos
    # ELIMINAR subjects (campo legacy)
    # subjects = models.ManyToManyField(...)  ← BORRAR ESTA LÍNEA
```

---

## 📝 Commit

```bash
commit [hash] (HEAD -> feature/subject-refactor)

feat(subject): Implementación de modelos Level y SubjectLevel para refactorización de asignaturas

Archivos modificados:
- core/models.py: Agregados modelos Level y SubjectLevel
- core/admin.py: Agregados LevelAdmin y SubjectLevelAdmin
- accounts/models.py: Agregado campo subjects_taught a TutorProfile
- accounts/admin.py: Actualizado TutorProfileAdmin para mostrar ambos campos

Nuevos modelos:
1. Level: Niveles educativos (Primaria, Secundaria, Universidad, etc.)
   - name: CharField único
   - order: IntegerField para ordenamiento
   
2. SubjectLevel: Combinación de Subject + Level
   - subject: ForeignKey a Subject
   - level: ForeignKey a Level
   - unique_together: (subject, level)

Cambios en TutorProfile:
- Agregado subjects_taught: ManyToMany a SubjectLevel (nuevo sistema)
- Mantenido subjects: ManyToMany a Subject (legacy, compatibilidad)
- related_name cambiado a 'tutors_legacy' en subjects

Administración:
- LevelAdmin: Gestión de niveles con list_editable
- SubjectLevelAdmin: Gestión de combinaciones con acción duplicar
- TutorProfileAdmin: Muestra ambos campos durante transición

Nota: NO se ejecutaron migraciones. Solo cambios en código Python.
```

---

## ✅ Archivos Modificados

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| **`core/models.py`** | +2 modelos (Level, SubjectLevel) | +69 |
| **`core/admin.py`** | +2 admins (LevelAdmin, SubjectLevelAdmin) | +87 |
| **`accounts/models.py`** | +1 campo (subjects_taught), renamed (subjects→legacy) | +15 |
| **`accounts/admin.py`** | Updated TutorProfileAdmin, TutorProfileInline | +12 |

**Total:** ~183 líneas agregadas/modificadas

---

## 🧪 Testing Manual (Después de Migración)

### Test 1: Crear Niveles en Admin
```
1. Ir a /admin/core/level/
2. Click "Agregar nivel"
3. Nombre: "Primaria", Order: 1
4. Guardar
5. VERIFICAR: Nivel creado correctamente
```

### Test 2: Crear SubjectLevels en Admin
```
1. Ir a /admin/core/subjectlevel/
2. Click "Agregar materia por nivel"
3. Subject: Matemáticas
4. Level: Primaria
5. Guardar
6. VERIFICAR: Combinación creada
7. VERIFICAR: __str__ muestra "Matemáticas - Primaria"
```

### Test 3: Asignar SubjectLevels a Tutor
```
1. Ir a /admin/accounts/tutorprofile/
2. Seleccionar un tutor
3. En filter_horizontal de "Materias y Niveles (Nuevo)":
   - Agregar "Matemáticas - Universidad"
   - Agregar "Física - Universidad"
4. Guardar
5. VERIFICAR: Columna muestra "Matemáticas (Universidad), Física (Universidad)"
```

### Test 4: Acción Duplicar Materia
```
1. Ir a /admin/core/subjectlevel/
2. Crear "Matemáticas - Primaria"
3. Seleccionar checkbox
4. Acción: "Duplicar materia en todos los niveles"
5. Ejecutar
6. VERIFICAR: Se crearon combinaciones para todos los niveles
```

---

## 🎉 Beneficios de la Refactorización

### Para el Negocio
- ✅ **Búsquedas más precisas**: Estudiantes encuentran tutores adecuados
- ✅ **Mejor conversión**: Match correcto tutor-estudiante
- ✅ **Escalabilidad**: Base para precios diferenciados por nivel

### Para Usuarios
- ✅ **Claridad**: "Matemáticas de Universidad" vs "Matemáticas de Primaria"
- ✅ **Confianza**: Saben que el tutor domina SU nivel
- ✅ **Ahorro de tiempo**: Menos filtrado manual

### Para Desarrollo
- ✅ **Arquitectura limpia**: Separación de concerns
- ✅ **Código mantenible**: Queries más expresivos
- ✅ **Extensibilidad**: Fácil agregar features futuras

---

## 🔮 Funcionalidades Futuras Posibles

### 1. Precios Diferenciados por Nivel
```python
class SubjectLevel(models.Model):
    # ... campos existentes
    recommended_rate = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        null=True,
        help_text='Tarifa recomendada para este nivel'
    )
```

### 2. Certificaciones por Nivel
```python
class TutorCertification(models.Model):
    tutor = models.ForeignKey(TutorProfile)
    subject_level = models.ForeignKey(SubjectLevel)
    certificate_url = models.URLField()
    verified = models.BooleanField(default=False)
```

### 3. Estadísticas por Nivel
```python
# Análisis de demanda
demanda_por_nivel = SubjectLevel.objects.annotate(
    num_busquedas=Count('searches'),
    num_tutores=Count('tutors')
).order_by('-num_busquedas')
```

---

## ✅ Conclusión

La refactorización de asignaturas con modelos `Level` y `SubjectLevel` ha sido implementada exitosamente en el código.

**Estado Actual:**
- ✅ **Modelos creados** en `core/models.py`
- ✅ **Administración configurada** en `core/admin.py` y `accounts/admin.py`
- ✅ **TutorProfile actualizado** con campo `subjects_taught`
- ✅ **Compatibilidad mantenida** con campo legacy `subjects`
- ⏳ **Pendiente:** Ejecutar migraciones en servidor

**Próximos Pasos:**
1. Ejecutar `makemigrations` en servidor
2. Ejecutar `migrate` para crear tablas
3. Poblar niveles iniciales (script)
4. Crear SubjectLevels para materias existentes
5. Migrar datos de tutores legacy a nuevo sistema
6. Actualizar vistas y formularios
7. Eliminar campo legacy después de verificación

---

**Documentado por:** GitHub Copilot  
**Fecha:** 16 de Diciembre, 2025  
**Rama:** `feature/subject-refactor`  
**Prioridad:** 🔵🔵🔵🔵 **P4 - REFACTORIZACIÓN**  
**Status:** ✅ **CÓDIGO COMPLETADO - PENDIENTE DE MIGRACIÓN**
