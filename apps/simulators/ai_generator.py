"""
Generación de simuladores via LLM (DeepSeek).

Este módulo contiene:
- build_system_prompt()        → prompt de sistema para el LLM
- call_deepseek()              → llamada a la API
- validate_questions()         → validación del JSON de respuesta
- build_reinforcement_prompt() → prompt de refuerzo adaptativo
- generate_reinforcement_simulator() → crea simulador de refuerzo
"""
import json
from django.utils import timezone

from .models import Simulator, SimulatorQuestion, StudentWeakTopicProfile


# ─────────────────────────────────────────────────────────────
# Prompt de sistema (compartido por todos los generadores)
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "Eres un generador de preguntas de opción múltiple para una "
    "plataforma educativa latinoamericana. Responde ÚNICAMENTE con "
    "un JSON válido siguiendo exactamente este esquema:\n\n"
    "{\n"
    '  "questions": [\n'
    "    {\n"
    '      "topic_tag": "string",\n'
    '      "difficulty": "low" | "medium" | "high",\n'
    '      "statement": "string",\n'
    '      "option_a": "string",\n'
    '      "option_b": "string",\n'
    '      "option_c": "string",\n'
    '      "option_d": "string",\n'
    '      "correct_option": "A" | "B" | "C" | "D",\n'
    '      "explanation": "string"\n'
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Reglas:\n"
    "- Genera entre 5 y 10 preguntas.\n"
    "- Cada pregunta tiene exactamente 4 opciones.\n"
    "- La opción correcta debe ser A, B, C o D.\n"
    "- Las opciones incorrectas deben ser plausibles.\n"
    "- Incluye una explicación breve de la respuesta correcta.\n"
    "- El campo topic_tag describe el tema específico de la pregunta.\n"
    "- Responde SOLO con el JSON, sin markdown ni texto adicional."
)


def build_system_prompt() -> str:
    """Retorna el prompt de sistema para el LLM."""
    return SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────
# Llamada a la API de DeepSeek
# ─────────────────────────────────────────────────────────────

def call_deepseek(system_prompt: str, user_prompt: str):
    """
    Llama a la API de DeepSeek y retorna el JSON parseado.

    Returns:
        dict | None: JSON parseado de la respuesta, o None si falla.
    """
    import os
    import requests

    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        # Fallback: intentar con OPENAI_API_KEY
        api_key = os.getenv("OPENAI_API_KEY", "")

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }

    try:
        r = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Validación del JSON de respuesta
# ─────────────────────────────────────────────────────────────

REQUIRED_KEYS = {
    "topic_tag",
    "difficulty",
    "statement",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_option",
}
VALID_DIFFICULTIES = {"low", "medium", "high"}
VALID_OPTIONS = {"A", "B", "C", "D"}


def validate_questions(raw_data):
    """
    Valida que raw_data sea un dict con lista 'questions' válidas.

    Returns:
        list[dict] | None: lista de preguntas válidas, o None.
    """
    if not isinstance(raw_data, dict):
        return None
    questions = raw_data.get("questions")
    if not isinstance(questions, list) or len(questions) == 0:
        return None

    valid = []
    for q in questions:
        if not isinstance(q, dict):
            return None
        if not REQUIRED_KEYS <= set(q.keys()):
            return None
        if q["difficulty"] not in VALID_DIFFICULTIES:
            return None
        if q["correct_option"] not in VALID_OPTIONS:
            return None
        valid.append(q)

    return valid if valid else None


# ─────────────────────────────────────────────────────────────
# Prompt de refuerzo adaptativo
# ─────────────────────────────────────────────────────────────

def build_reinforcement_prompt(attempt, weak_profiles) -> str:
    """
    Construye el prompt de usuario para generar un simulador de refuerzo
    enfocado en los temas débiles del estudiante.
    """
    lines = [
        f"Materia: {attempt.simulator.subject}\n",
        "El estudiante ha completado un simulacro previo con los "
        "siguientes resultados por tema:\n",
    ]

    for topic, pct in attempt.performance_by_topic.items():
        lines.append(f"- {topic}: {pct.get('pct', 0):.1f}% de aciertos\n")

    lines.append(
        "\nTEMAS DÉBILES (puntaje menor al 60%) — "
        "DEBES generar al menos 2 preguntas sobre cada uno:\n"
    )

    for profile in weak_profiles:
        lines.append(
            f"- {profile.topic_tag} "
            f"(puntaje acumulado: {profile.cumulative_score_pct}%, "
            f"fallos consecutivos: {profile.consecutive_failures})\n"
        )

    lines.append(
        "\nGenera entre 5 y 10 preguntas de opción múltiple "
        "enfocadas en reforzar los temas débiles del estudiante. "
        "Aumenta la dificultad progresivamente. "
        "Responde solo con el JSON especificado."
    )

    return "".join(lines)


# ─────────────────────────────────────────────────────────────
# Generador de simulador principal (diagnóstico)
# ─────────────────────────────────────────────────────────────

def generate_simulator(session, student):
    """
    Main entry point: student triggers AI generation of a diagnostic
    simulator from the tutor's session materials.
    Tutor does NOT interact with AI at any point.
    Returns: (success: bool, message: str)
    """
    from apps.academicTutoring.models import SessionMaterial
    from apps.simulators.models import Simulator, SimulatorQuestion

    # Step 1 — Check materials exist
    materials = SessionMaterial.objects.filter(session=session)
    if not materials.exists():
        return False, (
            "La sesión no tiene materiales. "
            "El tutor debe subir material primero."
        )

    # Step 2 — Check session ownership
    if session.client != student:
        return False, "No tienes acceso a esta sesión."

    # Step 3 — Cooldown check (token protection)
    if not check_generation_cooldown(session, student, 'diagnostic'):
        return False, (
            f"Ya generaste un simulacro para esta sesión hoy. "
            f"Espera {GENERATION_COOLDOWN_HOURS} horas antes de regenerar."
        )

    # Step 4 — Check no duplicate published simulator
    existing = Simulator.objects.filter(
        session=session,
        student=student,
        status='published',
        simulator_type='diagnostic'
    ).first()
    if existing:
        return False, "Ya existe un simulacro generado para esta sesión."

    # Step 5 — Create Simulator in GENERATING state
    simulator = Simulator.objects.create(
        session=session,
        tutor=session.tutor,
        student=student,
        simulator_type='diagnostic',
        status='draft',
        generation_status='generating',
        title=f"Simulacro — {session.subject}",
        subject=session.subject,
        source_material_url=(
            materials.filter(type='url').first().url
            if materials.filter(type='url').exists() else None
        ),
        max_attempts=3,
    )

    # Step 6 — Build weak topics context
    weak_profiles = StudentWeakTopicProfile.objects.filter(
        student=student,
        subject=session.subject,
        cumulative_score_pct__lt=60
    ).order_by('cumulative_score_pct')[:5]
    weak_topics = [p.topic_tag for p in weak_profiles]
    simulator.weak_topics_context = weak_topics
    simulator.save(update_fields=['weak_topics_context'])

    # Step 7 — Build prompts
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(session, materials, weak_topics)
    simulator.generation_prompt = user_prompt
    simulator.save(update_fields=['generation_prompt'])

    # Step 8 — Call AI provider
    raw_data = call_ai_provider(system_prompt, user_prompt)
    if raw_data is None:
        simulator.generation_status = 'failed'
        simulator.generation_error = 'API call failed or timed out'
        simulator.save(update_fields=['generation_status', 'generation_error'])
        return False, (
            "Error al conectar con el servicio de IA. "
            "Intenta de nuevo en unos minutos."
        )

    # Step 9 — Validate questions
    questions = validate_questions(raw_data)
    if questions is None:
        simulator.generation_status = 'failed'
        simulator.generation_error = f'Validation failed: {str(raw_data)[:200]}'
        simulator.save(update_fields=['generation_status', 'generation_error'])
        return False, "La IA no generó preguntas válidas. Intenta de nuevo."

    # Step 10 — Create SimulatorQuestion objects
    for i, q in enumerate(questions, start=1):
        SimulatorQuestion.objects.create(
            simulator=simulator,
            order=i,
            topic_tag=q['topic_tag'],
            difficulty=q['difficulty'],
            statement=q['statement'],
            option_a=q['option_a'],
            option_b=q['option_b'],
            option_c=q['option_c'],
            option_d=q['option_d'],
            correct_option=q['correct_option'],
            explanation=q.get('explanation', ''),
            is_active=True,
        )

    # Step 11 — Publish simulator
    simulator.generation_status = 'done'
    simulator.status = 'published'
    simulator.published_at = timezone.now()
    simulator.save(update_fields=[
        'generation_status', 'status', 'published_at'
    ])

    return True, f"Simulacro generado con {len(questions)} preguntas."


# ─────────────────────────────────────────────────────────────
# Generador de simulador de refuerzo
# ─────────────────────────────────────────────────────────────

def generate_reinforcement_simulator(attempt, student):
    """
    Genera un simulador de refuerzo enfocado en los temas débiles
    del estudiante.

    Returns:
        (success: bool, message: str)
    """
    # Step 1 — Get weak topics for this subject
    weak_profiles = StudentWeakTopicProfile.objects.filter(
        student=student,
        subject=attempt.simulator.subject,
        cumulative_score_pct__lt=60,
    ).order_by("cumulative_score_pct")[:8]

    if not weak_profiles.exists():
        return False, (
            "No se detectaron temas débiles. "
            "Tu desempeño es bueno en todos los temas evaluados."
        )

    # Step 2 — Check no duplicate reinforcement simulator for this attempt
    existing = Simulator.objects.filter(
        session=attempt.simulator.session,
        student=student,
        simulator_type=Simulator.SimulatorType.REINFORCEMENT,
    ).filter(
        created_at__gt=attempt.started_at
    ).first()
    if existing and existing.status == Simulator.Status.PUBLISHED:
        return False, "Ya existe un simulacro de refuerzo generado."

    # Step 3 — Create Simulator in GENERATING state
    session = attempt.simulator.session
    simulator = Simulator.objects.create(
        session=session,
        tutor=session.tutor,
        student=student,
        simulator_type=Simulator.SimulatorType.REINFORCEMENT,
        status=Simulator.Status.DRAFT,
        generation_status=Simulator.GenerationStatus.GENERATING,
        title=f"Refuerzo — {attempt.simulator.subject}",
        subject=attempt.simulator.subject,
        weak_topics_context=[p.topic_tag for p in weak_profiles],
        max_attempts=3,
    )

    # Step 4 — Build prompts
    system_prompt = build_system_prompt()
    user_prompt = build_reinforcement_prompt(attempt, weak_profiles)
    simulator.generation_prompt = user_prompt
    simulator.save(update_fields=["generation_prompt"])

    # Step 5 — Call DeepSeek
    raw_data = call_deepseek(system_prompt, user_prompt)
    if raw_data is None:
        simulator.generation_status = Simulator.GenerationStatus.FAILED
        simulator.generation_error = "API call failed"
        simulator.save(update_fields=["generation_status", "generation_error"])
        return False, "Error al conectar con la IA. Intenta de nuevo."

    # Step 6 — Validate and create questions
    questions = validate_questions(raw_data)
    if questions is None:
        simulator.generation_status = Simulator.GenerationStatus.FAILED
        simulator.generation_error = "Validation failed"
        simulator.save(update_fields=["generation_status", "generation_error"])
        return False, "La IA no generó preguntas válidas. Intenta de nuevo."

    for i, q in enumerate(questions, start=1):
        SimulatorQuestion.objects.create(
            simulator=simulator,
            order=i,
            topic_tag=q["topic_tag"],
            difficulty=q["difficulty"],
            statement=q["statement"],
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct_option=q["correct_option"],
            explanation=q.get("explanation", ""),
            is_active=True,
        )

    # Step 7 — Publish
    simulator.generation_status = Simulator.GenerationStatus.DONE
    simulator.status = Simulator.Status.PUBLISHED
    simulator.published_at = timezone.now()
    simulator.save(update_fields=[
        "generation_status", "status", "published_at"
    ])
    return True, (
        f"Simulacro de refuerzo generado con {len(questions)} "
        f"preguntas enfocadas en tus temas débiles."
    )
