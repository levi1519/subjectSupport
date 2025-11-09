"""
Test utilities and factories for accounts app
"""
from accounts.models import User, TutorProfile, ClientProfile


class UserFactory:
    """Factory for creating test users"""

    @staticmethod
    def create_tutor(email='tutor@test.com', password='testpass123', name='Test Tutor',
                     subjects='Mathematics, Physics', city='Quito', country='Ecuador'):
        """Create a tutor user with profile"""
        user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            name=name,
            user_type='tutor'
        )
        TutorProfile.objects.create(
            user=user,
            subjects=subjects,
            bio='Experienced tutor',
            experience='5 years of teaching',
            city=city,
            country=country
        )
        return user

    @staticmethod
    def create_client(email='client@test.com', password='testpass123', name='Test Client',
                      city='Quito', country='Ecuador', is_minor=False):
        """Create a client user with profile"""
        user = User.objects.create_user(
            email=email,
            username=email,
            password=password,
            name=name,
            user_type='client'
        )
        ClientProfile.objects.create(
            user=user,
            is_minor=is_minor,
            city=city,
            country=country
        )
        return user

    @staticmethod
    def create_multiple_tutors(count=5, city='Quito', country='Ecuador'):
        """Create multiple tutors for testing"""
        tutors = []
        for i in range(count):
            tutor = UserFactory.create_tutor(
                email=f'tutor{i}@test.com',
                name=f'Tutor {i}',
                subjects=f'Subject {i}',
                city=city,
                country=country
            )
            tutors.append(tutor)
        return tutors

    @staticmethod
    def create_tutors_by_location():
        """Create tutors in different locations for geographical testing"""
        tutors = {
            'same_city': UserFactory.create_tutor(
                email='tutor_quito@test.com',
                name='Quito Tutor',
                city='Quito',
                country='Ecuador'
            ),
            'same_country': UserFactory.create_tutor(
                email='tutor_guayaquil@test.com',
                name='Guayaquil Tutor',
                city='Guayaquil',
                country='Ecuador'
            ),
            'different_country': UserFactory.create_tutor(
                email='tutor_colombia@test.com',
                name='Colombia Tutor',
                city='Bogota',
                country='Colombia'
            )
        }
        return tutors
