from django.contrib import admin
from .models import TutorLead, ClassSession


@admin.register(TutorLead)
class TutorLeadAdmin(admin.ModelAdmin):
    """Admin configuration for TutorLead model"""
    list_display = ['name', 'email', 'subject', 'created_at']
    list_filter = ['created_at', 'subject']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Tutor Information', {
            'fields': ('name', 'email', 'subject')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    """Admin configuration for ClassSession model"""
    list_display = ['subject', 'tutor', 'client', 'scheduled_date', 'scheduled_time', 'status', 'created_at']
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['subject', 'tutor__name', 'tutor__email', 'client__name', 'client__email']
    readonly_fields = ['created_at', 'updated_at', 'meeting_url']
    ordering = ['-scheduled_date', '-scheduled_time']
    date_hierarchy = 'scheduled_date'

    fieldsets = (
        ('Información de la Sesión', {
            'fields': ('tutor', 'client', 'subject')
        }),
        ('Programación', {
            'fields': ('scheduled_date', 'scheduled_time', 'duration')
        }),
        ('Estado y Detalles', {
            'fields': ('status', 'meeting_url', 'notes')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('tutor', 'client')
