"""
Django REST Framework Serializers for accounts app.
Handles serialization of Subject and TutorProfile models for API endpoints.
"""

from rest_framework import serializers
from .models import Subject, TutorProfile, User


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Subject model.
    Returns subject name and slug for display in frontend.
    """

    class Meta:
        model = Subject
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']


class TutorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for TutorProfile model.
    Includes nested subject information and tutor details.
    """
    # Nested representation of subjects
    subjects = SubjectSerializer(many=True, read_only=True)

    # Subject IDs for write operations
    subject_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Subject.objects.all(),
        write_only=True,
        source='subjects',
        required=False
    )

    # Display username instead of user ID
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)

    # Hourly rate with proper formatting
    hourly_rate = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    class Meta:
        model = TutorProfile
        fields = [
            'id',
            'username',
            'email',
            'name',
            'subjects',
            'subject_ids',
            'hourly_rate',
            'bio',
            'experience',
            'city',
            'country',
            'created_at'
        ]
        read_only_fields = ['id', 'username', 'email', 'name', 'created_at']

    def to_representation(self, instance):
        """
        Customize the output representation.
        Adds formatted hourly_rate display.
        """
        representation = super().to_representation(instance)

        # Add formatted hourly rate
        if instance.hourly_rate:
            representation['hourly_rate_formatted'] = f"${instance.hourly_rate}/hr"
        else:
            representation['hourly_rate_formatted'] = "No especificado"

        # Add subject count
        representation['subject_count'] = instance.subjects.count()

        return representation


class TutorProfileListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing tutors.
    Used in search/list endpoints for better performance.
    """
    subjects = SubjectSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = TutorProfile
        fields = [
            'id',
            'username',
            'name',
            'subjects',
            'hourly_rate',
            'city',
            'country'
        ]
        read_only_fields = fields
