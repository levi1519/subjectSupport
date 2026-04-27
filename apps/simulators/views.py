from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone

from apps.simulators.models import (
    Simulator, SimulatorQuestion, SimulatorAttempt,
    SimulatorResponse, StudentWeakTopicProfile
)
from apps.accounts.models import User
from apps.academicTutoring.models import ClassSession

from .forms import SimulatorAttemptForm
from .ai_generator import generate_simulator, generate_reinforcement_simulator


def update_weak_topic_profile(attempt):
    for topic, stats in attempt.performance_by_topic.items():
        profile, _ = StudentWeakTopicProfile.objects.get_or_create(
            student=attempt.student,
            subject=attempt.simulator.subject,
            topic_tag=topic,
        )
        profile.update_from_attempt(
            correct=stats['correct'],
            questions_in_topic=stats['total']
        )


class SimulatorListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'simulators/list.html'

    def test_func(self):
        return self.request.user.user_type == 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        simulators = Simulator.objects.filter(
            student=self.request.user,
            status__in=['published', 'pending_approval', 'approved']
        ).select_related('session', 'tutor').order_by('-created_at')

        for sim in simulators:
            sim.attempt_count = sim.attempts.filter(
                student=self.request.user).count()
            sim.can_attempt = sim.student_can_attempt
            sim.last_attempt = sim.attempts.filter(
                student=self.request.user).order_by('-started_at').first()

        context['simulators'] = simulators
        context['page_title'] = 'Mis Simulacros'
        return context


class SimulatorDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'simulators/detail.html'

    def test_func(self):
        self.simulator = get_object_or_404(
            Simulator,
            pk=self.kwargs['pk'],
            student=self.request.user,
            status__in=['published', 'pending_approval', 'approved', 'rejected']
        )
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = SimulatorAttempt.objects.filter(
            simulator=self.simulator,
            student=self.request.user
        ).order_by('-started_at')

        context['simulator'] = self.simulator
        context['questions'] = self.simulator.questions.filter(
            is_active=True).order_by('order')
        context['attempts'] = attempts
        context['can_attempt'] = self.simulator.student_can_attempt
        context['attempts_remaining'] = (
            self.simulator.max_attempts - attempts.count()
        )
        return context


class SimulatorStartView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        self.simulator = get_object_or_404(
            Simulator,
            pk=self.kwargs['pk'],
            student=self.request.user,
            status__in=['published', 'pending_approval', 'approved']
        )
        return True

    def post(self, request, *args, **kwargs):
        existing = SimulatorAttempt.objects.filter(
            simulator=self.simulator,
            student=request.user,
            status='in_progress'
        ).first()
        if existing:
            messages.info(request, 'Tienes un intento en progreso. Continuando...')
            return redirect('simulators:attempt',
                pk=self.simulator.pk, attempt_pk=existing.pk)

        attempt_count = SimulatorAttempt.objects.filter(
            simulator=self.simulator,
            student=request.user
        ).count()
        if attempt_count >= self.simulator.max_attempts:
            messages.error(request,
                'Has alcanzado el máximo de intentos para este simulacro.')
            return redirect('simulators:detail', pk=self.simulator.pk)

        attempt = SimulatorAttempt.objects.create(
            simulator=self.simulator,
            student=request.user,
            attempt_number=attempt_count + 1,
            status='in_progress'
        )
        return redirect('simulators:attempt',
            pk=self.simulator.pk, attempt_pk=attempt.pk)

    def get(self, request, *args, **kwargs):
        return redirect('simulators:detail', pk=self.kwargs['pk'])


class SimulatorAttemptView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'simulators/attempt.html'

    def test_func(self):
        self.simulator = get_object_or_404(
            Simulator, pk=self.kwargs['pk'],
            student=self.request.user,
            status__in=['published', 'pending_approval', 'approved']
        )
        self.attempt = get_object_or_404(
            SimulatorAttempt,
            pk=self.kwargs['attempt_pk'],
            simulator=self.simulator,
            student=self.request.user
        )
        return True

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if hasattr(self, 'attempt') and self.attempt.status != 'in_progress':
            return redirect('simulators:results',
                pk=self.kwargs['pk'],
                attempt_pk=self.kwargs['attempt_pk'])
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        questions = self.simulator.questions.filter(
            is_active=True).order_by('order')
        form = SimulatorAttemptForm(questions=questions)
        context['simulator'] = self.simulator
        context['attempt'] = self.attempt
        context['questions'] = questions
        context['form'] = form
        context['total_questions'] = questions.count()
        context['time_limit'] = self.simulator.time_limit_per_question
        return context


class SimulatorSubmitView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        self.simulator = get_object_or_404(
            Simulator, pk=self.kwargs['pk'],
            student=self.request.user,
            status__in=['published', 'pending_approval', 'approved']
        )
        self.attempt = get_object_or_404(
            SimulatorAttempt,
            pk=self.kwargs['attempt_pk'],
            simulator=self.simulator,
            student=self.request.user
        )
        return True

    def post(self, request, *args, **kwargs):
        if self.attempt.status != 'in_progress':
            messages.warning(request, 'Este intento ya fue completado.')
            return redirect('simulators:results',
                pk=self.simulator.pk, attempt_pk=self.attempt.pk)

        questions = self.simulator.questions.filter(
            is_active=True).order_by('order')
        form = SimulatorAttemptForm(questions=questions, data=request.POST)

        if not form.is_valid():
            messages.error(request, 'Error al procesar respuestas.')
            return redirect('simulators:attempt',
                pk=self.simulator.pk, attempt_pk=self.attempt.pk)

        answers = form.get_answers()
        now = timezone.now()
        total_seconds = int((now - self.attempt.started_at).total_seconds())

        for question in questions:
            selected = answers.get(question.id)
            SimulatorResponse.objects.update_or_create(
                attempt=self.attempt,
                question=question,
                defaults={
                    'selected_option': selected,
                    'time_spent_seconds': 0,
                }
            )

        self.attempt.total_time_seconds = total_seconds
        self.attempt.status = 'completed'
        self.attempt.finished_at = now
        self.attempt.save(update_fields=[
            'total_time_seconds', 'status', 'finished_at'
        ])

        self.attempt.calculate_score()
        update_weak_topic_profile(self.attempt)

        messages.success(request,
            f'Simulacro completado. Puntaje: {self.attempt.score:.1f}%')
        return redirect('simulators:results',
            pk=self.simulator.pk, attempt_pk=self.attempt.pk)

    def get(self, request, *args, **kwargs):
        return redirect('simulators:attempt',
            pk=self.kwargs['pk'], attempt_pk=self.kwargs['attempt_pk'])


class SimulatorResultsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'simulators/results.html'

    def test_func(self):
        self.simulator = get_object_or_404(
            Simulator, pk=self.kwargs['pk'],
            student=self.request.user,
            status__in=['published', 'pending_approval', 'approved',
                        'rejected', 'closed']
        )
        self.attempt = get_object_or_404(
            SimulatorAttempt,
            pk=self.kwargs['attempt_pk'],
            simulator=self.simulator,
            student=self.request.user
        )
        return self.attempt.status == 'completed'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        responses = self.attempt.responses.select_related(
            'question').order_by('question__order')

        result_rows = []
        for resp in responses:
            result_rows.append({
                'question': resp.question,
                'selected': resp.selected_option,
                'correct': resp.question.correct_option,
                'is_correct': resp.is_correct,
                'explanation': resp.question.explanation,
            })

        context['simulator'] = self.simulator
        context['attempt'] = self.attempt
        context['result_rows'] = result_rows
        context['weak_topics'] = self.attempt.weak_topics
        context['can_retry'] = self.simulator.student_can_attempt
        context['performance_by_topic'] = self.attempt.performance_by_topic
        return context


class SimulatorGenerateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Tutor triggers AI generation of a simulator from
    the session materials.
    """

    def test_func(self):
        return self.request.user.user_type == 'tutor'

    def post(self, request, session_pk):
        session = get_object_or_404(
            ClassSession,
            pk=session_pk,
            tutor=request.user,
            status='completed'
        )
        if session.tutor != request.user:
            messages.error(request, "Solo el tutor puede generar simulacros.")
            return redirect('tutor_dashboard')

        success, message = generate_simulator(session, student=session.client)
        if success:
            from apps.simulators.models import Simulator as Sim
            Sim.objects.filter(
                session=session,
                student=session.client,
                status='rejected'
            ).update(generation_status='failed')
            messages.success(request, message)
            return redirect('tutor_session_history')
        else:
            messages.error(request, message)
            return redirect('tutor_session_history')

    def get(self, request, session_pk):
        return redirect('tutor_session_history')


class ReinforcementGenerateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Student triggers generation of an adaptive reinforcement
    simulator from results of a completed attempt.
    """

    def test_func(self):
        return self.request.user.user_type == 'client'

    def post(self, request, pk, attempt_pk):
        simulator = get_object_or_404(
            Simulator, pk=pk, student=request.user
        )
        attempt = get_object_or_404(
            SimulatorAttempt,
            pk=attempt_pk,
            simulator=simulator,
            student=request.user,
            status='completed'
        )
        success, message = generate_reinforcement_simulator(
            attempt, request.user
        )
        if success:
            messages.success(request, message)
            return redirect('simulators:list')
        else:
            messages.error(request, message)
            return redirect('simulators:results',
                pk=pk, attempt_pk=attempt_pk)

    def get(self, request, pk, attempt_pk):
        return redirect('simulators:results',
            pk=pk, attempt_pk=attempt_pk)
