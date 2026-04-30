from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


def update_weak_topic_profile(attempt):
    """
    Actualiza (o crea) StudentWeakTopicProfile para cada tema del intento.
    Debe llamarse DESPUÉS de attempt.calculate_score().
    """
    subject = attempt.simulator.subject
    student = attempt.student

    for topic, stats in attempt.performance_by_topic.items():
        correct = stats.get('correct', 0)
        total = stats.get('total', 0)

        profile, _ = StudentWeakTopicProfile.objects.get_or_create(
            student=student,
            subject=subject,
            topic_tag=topic,
            defaults={
                'total_questions_seen': 0,
                'total_correct': 0,
                'cumulative_score_pct': 0,
                'consecutive_failures': 0,
            }
        )
        profile.update_from_attempt(correct=correct, questions_in_topic=total)


class Simulator(models.Model):
    """
    Simulador de preguntas asociado a una sesión de clase.

    Un tutor puede generar uno o más simuladores por sesión:
    - DIAGNOSTIC: antes de la clase, basado en el material subido por el estudiante
    - REINFORCEMENT: después de la clase, focalizado en temas débiles detectados

    El contenido (preguntas) se genera automáticamente via API de Anthropic,
    pero el tutor puede revisar y publicar antes de que el estudiante lo vea.
    """

    class SimulatorType(models.TextChoices):
        DIAGNOSTIC = 'diagnostic', 'Diagnóstico'
        REINFORCEMENT = 'reinforcement', 'Refuerzo'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PUBLISHED = 'published', 'Publicado'
        PENDING_APPROVAL = 'pending_approval', 'Pendiente de aprobación'
        APPROVED = 'approved', 'Aprobado por tutor'
        REJECTED = 'rejected', 'Rechazado por tutor'
        CLOSED = 'closed', 'Cerrado'

    class GenerationStatus(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        GENERATING = 'generating', 'Generando...'
        DONE = 'done', 'Listo'
        FAILED = 'failed', 'Error al generar'

    session = models.ForeignKey(
        'academicTutoring.ClassSession',
        on_delete=models.CASCADE,
        related_name='simulators',
        verbose_name='Sesión de clase'
    )
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_simulators',
        limit_choices_to={'user_type': 'tutor'},
        verbose_name='Tutor que lo generó'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_simulators',
        limit_choices_to={'user_type': 'client'},
        verbose_name='Estudiante asignado'
    )

    simulator_type = models.CharField(
        max_length=20,
        choices=SimulatorType.choices,
        default=SimulatorType.DIAGNOSTIC,
        verbose_name='Tipo de simulador'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Estado'
    )
    generation_status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING,
        verbose_name='Estado de generación'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Ej: Diagnóstico — Cálculo diferencial'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='Materia o tema general'
    )

    # Contexto que se usó para generar las preguntas (para auditoría y re-generación)
    source_material_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL del material fuente',
        help_text='Material que subió el estudiante al solicitar la clase'
    )
    source_material_text = models.TextField(
        blank=True,
        null=True,
        verbose_name='Texto del material fuente',
        help_text='Contenido extraído del material para pasarle al LLM'
    )

    # Temas débiles detectados en intentos anteriores — se pasan al prompt de re-generación
    weak_topics_context = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Temas débiles detectados',
        help_text='Lista de temas en que el estudiante falló en simuladores previos'
    )

    # Prompt usado para la generación (para debugging y auditoría)
    generation_prompt = models.TextField(
        blank=True,
        null=True,
        verbose_name='Prompt enviado al LLM'
    )
    generation_error = models.TextField(
        blank=True,
        null=True,
        verbose_name='Error de generación si falló'
    )

    # Tiempo límite por pregunta en segundos (0 = sin límite)
    time_limit_per_question = models.PositiveIntegerField(
        default=0,
        verbose_name='Tiempo límite por pregunta (segundos)',
        help_text='0 significa sin límite de tiempo'
    )

    # Cuántos intentos puede hacer el estudiante
    max_attempts = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        verbose_name='Intentos máximos permitidos'
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Publicado el'
    )
    tutor_reviewed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Revisado por tutor el'
    )
    tutor_feedback = models.TextField(
        blank=True,
        null=True,
        verbose_name='Comentario del tutor',
        help_text='Visible al estudiante si el simulacro es rechazado'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Simulador'
        verbose_name_plural = 'Simuladores'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_simulator_type_display()}) — {self.student.name}"

    def clean(self):
        if self.session.tutor != self.tutor:
            raise ValidationError(
                'El tutor del simulador debe coincidir con el tutor de la sesión.'
            )
        if self.session.client != self.student:
            raise ValidationError(
                'El estudiante del simulador debe coincidir con el cliente de la sesión.'
            )

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def is_published(self):
        return self.status in (
            self.Status.PUBLISHED,
            self.Status.PENDING_APPROVAL,
            self.Status.APPROVED
        )

    @property
    def attempts_by_student(self):
        return self.attempts.filter(student=self.student).count()

    @property
    def student_can_attempt(self):
        return (
            self.status in (self.Status.PUBLISHED, self.Status.APPROVED)
            and self.attempts_by_student < self.max_attempts
        )


class SimulatorQuestion(models.Model):
    """
    Pregunta individual de un simulador.

    Generada automáticamente por el LLM, pero puede ser editada
    o eliminada por el tutor antes de publicar el simulador.

    Cada pregunta tiene exactamente 4 opciones (A, B, C, D)
    y un identificador de tema para poder calcular el desempeño
    por área de conocimiento.
    """

    class DifficultyLevel(models.TextChoices):
        LOW = 'low', 'Baja'
        MEDIUM = 'medium', 'Media'
        HIGH = 'high', 'Alta'

    simulator = models.ForeignKey(
        Simulator,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Simulador'
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden de aparición'
    )

    # Tema al que pertenece esta pregunta (para análisis de desempeño por área)
    topic_tag = models.CharField(
        max_length=100,
        verbose_name='Tema',
        help_text='Ej: "derivadas implícitas", "herencia en POO", "balance de masas"'
    )

    difficulty = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        verbose_name='Dificultad'
    )

    statement = models.TextField(
        verbose_name='Enunciado de la pregunta'
    )

    # Las 4 opciones de respuesta
    option_a = models.TextField(verbose_name='Opción A')
    option_b = models.TextField(verbose_name='Opción B')
    option_c = models.TextField(verbose_name='Opción C')
    option_d = models.TextField(verbose_name='Opción D')

    CORRECT_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    correct_option = models.CharField(
        max_length=1,
        choices=CORRECT_CHOICES,
        verbose_name='Opción correcta'
    )

    # Explicación que se muestra al estudiante después de responder
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name='Explicación de la respuesta correcta'
    )

    # Flag por si el tutor quiere ocultar una pregunta mal generada
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pregunta del simulador'
        verbose_name_plural = 'Preguntas del simulador'
        ordering = ['simulator', 'order']
        unique_together = [['simulator', 'order']]

    def __str__(self):
        return f"P{self.order}: {self.statement[:60]}..."

    def get_option_text(self, letter):
        """Devuelve el texto de la opción dado su letra (A, B, C, D)."""
        mapping = {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }
        return mapping.get(letter, '')

    @property
    def correct_option_text(self):
        return self.get_option_text(self.correct_option)


class SimulatorAttempt(models.Model):
    """
    Intento completo de un estudiante en un simulador.

    Un intento agrupa todas las respuestas de una sola sesión de juego.
    Se crea cuando el estudiante inicia el simulador y se cierra
    cuando lo termina o se agota el tiempo.

    El campo `performance_by_topic` es el insumo clave para generar
    simuladores de refuerzo adaptativos: contiene el porcentaje de
    aciertos por tema.
    """

    class AttemptStatus(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'En progreso'
        COMPLETED = 'completed', 'Completado'
        ABANDONED = 'abandoned', 'Abandonado'

    simulator = models.ForeignKey(
        Simulator,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Simulador'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='simulator_attempts',
        limit_choices_to={'user_type': 'client'},
        verbose_name='Estudiante'
    )

    attempt_number = models.PositiveIntegerField(
        verbose_name='Número de intento',
        help_text='1 para el primero, 2 para el segundo, etc.'
    )

    status = models.CharField(
        max_length=20,
        choices=AttemptStatus.choices,
        default=AttemptStatus.IN_PROGRESS,
        verbose_name='Estado del intento'
    )

    # Puntaje final: porcentaje de aciertos (0.0 a 100.0)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Puntaje (%)'
    )

    # Total de preguntas correctas e incorrectas
    correct_count = models.PositiveIntegerField(default=0, verbose_name='Respuestas correctas')
    incorrect_count = models.PositiveIntegerField(default=0, verbose_name='Respuestas incorrectas')
    unanswered_count = models.PositiveIntegerField(default=0, verbose_name='Sin responder')

    # Tiempo total que tardó el estudiante (en segundos)
    total_time_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name='Tiempo total (segundos)'
    )

    # Desempeño desglosado por tema — alimenta la generación de simuladores adaptativos
    # Estructura: {"derivadas implícitas": {"correct": 1, "total": 3, "pct": 33.3}, ...}
    performance_by_topic = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Desempeño por tema',
        help_text='Calculado automáticamente al finalizar el intento'
    )

    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Inicio')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='Fin')

    class Meta:
        verbose_name = 'Intento de simulador'
        verbose_name_plural = 'Intentos de simulador'
        ordering = ['-started_at']
        unique_together = [['simulator', 'student', 'attempt_number']]

    def __str__(self):
        score_display = self.score if self.score is not None else 'en progreso'
        suffix = '%' if self.score is not None else ''
        return (
            f"Intento #{self.attempt_number} de {self.student.name} "
            f"en '{self.simulator.title}' — {score_display}{suffix}"
        )

    def calculate_score(self):
        """
        Calcula y guarda el puntaje final + desempeño por tema.
        Llamar este método al finalizar el intento.
        """
        responses = self.responses.select_related('question').all()
        total = responses.count()

        if total == 0:
            return

        correct = sum(1 for r in responses if r.is_correct)
        incorrect = sum(1 for r in responses if not r.is_correct and r.selected_option)
        unanswered = sum(1 for r in responses if not r.selected_option)

        self.correct_count = correct
        self.incorrect_count = incorrect
        self.unanswered_count = unanswered
        self.score = round((correct / total) * 100, 2)

        # Desempeño por tema
        topic_stats = {}
        for r in responses:
            topic = r.question.topic_tag
            if topic not in topic_stats:
                topic_stats[topic] = {'correct': 0, 'total': 0}
            topic_stats[topic]['total'] += 1
            if r.is_correct:
                topic_stats[topic]['correct'] += 1

        self.performance_by_topic = {
            topic: {
                'correct': stats['correct'],
                'total': stats['total'],
                'pct': round((stats['correct'] / stats['total']) * 100, 1)
            }
            for topic, stats in topic_stats.items()
        }

        self.save(update_fields=[
            'score', 'correct_count', 'incorrect_count',
            'unanswered_count', 'performance_by_topic'
        ])

    @property
    def weak_topics(self):
        """
        Devuelve lista de temas donde el puntaje fue menor al 60%.
        Se usa como insumo para generar simuladores de refuerzo.
        """
        return [
            topic
            for topic, stats in self.performance_by_topic.items()
            if stats.get('pct', 100) < 60
        ]

    def finalize(self):
        """
        Finaliza el intento: calcula score y actualiza perfiles de temas débiles.
        Llama a este método cuando el estudiante termina el simulador.
        """
        from django.utils import timezone
        self.calculate_score()
        self.status = self.AttemptStatus.COMPLETED
        self.finished_at = timezone.now()
        self.save(update_fields=['status', 'finished_at'])
        update_weak_topic_profile(self)


class SimulatorResponse(models.Model):
    """
    Respuesta individual de un estudiante a una pregunta específica.

    Es el registro más granular del sistema: una fila por pregunta
    por intento. Permite reconstruir exactamente qué respondió
    el estudiante, en cuánto tiempo y si fue correcto.
    """

    attempt = models.ForeignKey(
        SimulatorAttempt,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Intento'
    )
    question = models.ForeignKey(
        SimulatorQuestion,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='Pregunta'
    )

    # La opción que seleccionó (null si no respondió)
    selected_option = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        null=True,
        blank=True,
        verbose_name='Opción seleccionada'
    )

    is_correct = models.BooleanField(
        default=False,
        verbose_name='Es correcta'
    )

    # Tiempo que tardó en responder esta pregunta específica (en segundos)
    time_spent_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name='Tiempo en esta pregunta (segundos)'
    )

    answered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Respondida el'
    )

    class Meta:
        verbose_name = 'Respuesta del simulador'
        verbose_name_plural = 'Respuestas del simulador'
        unique_together = [['attempt', 'question']]
        ordering = ['question__order']

    def __str__(self):
        status = "correcta" if self.is_correct else "incorrecta"
        return (
            f"Respuesta {status}: {self.attempt.student.name} "
            f"eligió {self.selected_option or 'nada'} en P{self.question.order}"
        )

    def save(self, *args, **kwargs):
        """Auto-calcula is_correct al guardar."""
        if self.selected_option:
            self.is_correct = (self.selected_option == self.question.correct_option)
        else:
            self.is_correct = False
        super().save(*args, **kwargs)


class StudentWeakTopicProfile(models.Model):
    """
    Perfil acumulado de temas débiles del estudiante por materia.

    Se actualiza cada vez que el estudiante completa un simulador.
    Es la memoria de largo plazo del sistema: permite que simuladores
    futuros sean adaptativos incluso si son de sesiones distintas.

    El tutor también puede ver este perfil para orientar la clase.
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weak_topic_profile',
        limit_choices_to={'user_type': 'client'},
        verbose_name='Estudiante'
    )
    subject = models.CharField(
        max_length=200,
        verbose_name='Materia',
        help_text='Ej: Cálculo diferencial, Programación orientada a objetos'
    )
    topic_tag = models.CharField(
        max_length=100,
        verbose_name='Tema específico',
        help_text='Ej: "derivadas implícitas", "herencia múltiple"'
    )

    # Acumulado histórico
    total_questions_seen = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de preguntas vistas'
    )
    total_correct = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de respuestas correctas'
    )

    # Calculado: porcentaje de aciertos acumulado
    cumulative_score_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Puntaje acumulado (%)'
    )

    # Cuántas veces consecutivas ha fallado este tema
    consecutive_failures = models.PositiveIntegerField(
        default=0,
        verbose_name='Fallos consecutivos'
    )

    last_seen = models.DateTimeField(
        auto_now=True,
        verbose_name='Última vez visto'
    )

    class Meta:
        verbose_name = 'Perfil de tema débil'
        verbose_name_plural = 'Perfiles de temas débiles'
        unique_together = [['student', 'subject', 'topic_tag']]
        ordering = ['cumulative_score_pct']

    def __str__(self):
        return (
            f"{self.student.name} — {self.subject} — "
            f"{self.topic_tag}: {self.cumulative_score_pct}%"
        )

    def update_from_attempt(self, correct: bool, questions_in_topic: int):
        """
        Actualiza el perfil acumulado después de un intento.

        Args:
            correct: número de respuestas correctas en este tema
            questions_in_topic: total de preguntas de este tema en el intento
        """
        self.total_questions_seen += questions_in_topic
        self.total_correct += correct

        if self.total_questions_seen > 0:
            self.cumulative_score_pct = round(
                (self.total_correct / self.total_questions_seen) * 100, 2
            )

        if correct < questions_in_topic:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        self.save()

    @property
    def is_weak(self):
        """True si el puntaje acumulado está por debajo del 60%."""
        return self.cumulative_score_pct < 60

    @property
    def priority_for_reinforcement(self):
        """
        Prioridad de refuerzo del 1 (baja) al 3 (urgente).
        Combina puntaje bajo + fallos consecutivos.
        """
        if self.cumulative_score_pct < 40 or self.consecutive_failures >= 3:
            return 3  # urgente
        if self.cumulative_score_pct < 60 or self.consecutive_failures >= 2:
            return 2  # media
        return 1  # baja