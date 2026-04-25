from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Simulator, SimulatorQuestion,
    SimulatorAttempt, SimulatorResponse,
    StudentWeakTopicProfile
)


class SimulatorQuestionInline(admin.TabularInline):
    model = SimulatorQuestion
    extra = 0
    fields = ['order', 'topic_tag', 'difficulty', 'statement', 'correct_option', 'is_active']
    ordering = ['order']
    show_change_link = True


@admin.register(Simulator)
class SimulatorAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'simulator_type', 'status', 'generation_status',
        'student', 'tutor', 'question_count_display', 'created_at'
    ]
    list_filter = ['simulator_type', 'status', 'generation_status', 'created_at']
    search_fields = ['title', 'subject', 'student__name', 'tutor__name']
    readonly_fields = ['created_at', 'updated_at', 'published_at', 'generation_prompt', 'generation_error']
    inlines = [SimulatorQuestionInline]

    fieldsets = (
        ('Identificación', {
            'fields': ('title', 'subject', 'simulator_type', 'session', 'tutor', 'student')
        }),
        ('Estado', {
            'fields': ('status', 'generation_status', 'published_at')
        }),
        ('Configuración', {
            'fields': ('time_limit_per_question', 'max_attempts')
        }),
        ('Material fuente', {
            'fields': ('source_material_url', 'source_material_text', 'weak_topics_context'),
            'classes': ('collapse',)
        }),
        ('Auditoría de generación', {
            'fields': ('generation_prompt', 'generation_error'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def question_count_display(self, obj):
        count = obj.questions.filter(is_active=True).count()
        return f'{count} preguntas'
    question_count_display.short_description = 'Preguntas'


@admin.register(SimulatorQuestion)
class SimulatorQuestionAdmin(admin.ModelAdmin):
    list_display = ['simulator', 'order', 'topic_tag', 'difficulty', 'correct_option', 'is_active']
    list_filter = ['difficulty', 'is_active', 'simulator__simulator_type']
    search_fields = ['statement', 'topic_tag', 'simulator__title']
    list_editable = ['is_active', 'order']


class SimulatorResponseInline(admin.TabularInline):
    model = SimulatorResponse
    extra = 0
    readonly_fields = ['question', 'selected_option', 'is_correct', 'time_spent_seconds', 'answered_at']
    can_delete = False


@admin.register(SimulatorAttempt)
class SimulatorAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'simulator', 'attempt_number', 'status',
        'score_display', 'correct_count', 'total_time_display', 'started_at'
    ]
    list_filter = ['status', 'started_at']
    search_fields = ['student__name', 'simulator__title']
    readonly_fields = [
        'score', 'correct_count', 'incorrect_count', 'unanswered_count',
        'performance_by_topic', 'started_at', 'finished_at'
    ]
    inlines = [SimulatorResponseInline]

    def score_display(self, obj):
        if obj.score is None:
            return '—'
        score = float(obj.score)
        color = '#27500A' if score >= 60 else '#791F1F'
        return format_html('<span style="color: {}; font-weight: 600;">{:.1f}%</span>', color, score)
    score_display.short_description = 'Puntaje'

    def total_time_display(self, obj):
        minutes = obj.total_time_seconds // 60
        seconds = obj.total_time_seconds % 60
        return f'{minutes}m {seconds}s'
    total_time_display.short_description = 'Tiempo total'


@admin.register(StudentWeakTopicProfile)
class StudentWeakTopicProfileAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'subject', 'topic_tag',
        'cumulative_score_pct', 'consecutive_failures',
        'priority_display', 'last_seen'
    ]
    list_filter = ['subject', 'last_seen']
    search_fields = ['student__name', 'subject', 'topic_tag']
    readonly_fields = ['cumulative_score_pct', 'last_seen']

    def priority_display(self, obj):
        p = obj.priority_for_reinforcement
        labels = {1: ('Baja', '#3B6D11'), 2: ('Media', '#854F0B'), 3: ('Urgente', '#A32D2D')}
        label, color = labels[p]
        return format_html('<span style="color: {}; font-weight: 600;">{}</span>', color, label)
    priority_display.short_description = 'Prioridad'