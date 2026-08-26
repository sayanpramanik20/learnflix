"""
quiz_service.py — generates a 4-option MCQ for any topic.

Primary path: ask Gemini to return JSON with {question, options, answer_index,
explanation}.  The model is prompted to stay concise and curriculum-appropriate.

Fallback path (no API key, or the model returns malformed JSON): draw from a
hard-coded question bank keyed by topic name so a live demo never breaks.
"""
import os
import json
import logging
import random
from typing import Optional

logger = logging.getLogger("ai_tutor.quiz")

# ---------------------------------------------------------------------------
# Hard-coded fallback bank — at least 2 questions per seeded topic so
# the fallback path always has something fresh to show.
# ---------------------------------------------------------------------------
_FALLBACK_BANK: dict[str, list[dict]] = {
    "Fractions": [
        {
            "question": "What is ½ + ¼?",
            "options": ["¾", "⅔", "⅖", "1"],
            "answer_index": 0,
            "explanation": "Convert to a common denominator: 2/4 + 1/4 = 3/4.",
        },
        {
            "question": "Which fraction is equivalent to 2/4?",
            "options": ["1/3", "1/2", "3/4", "2/3"],
            "answer_index": 1,
            "explanation": "2/4 simplifies by dividing numerator and denominator by 2 → 1/2.",
        },
    ],
    "Linear Equations": [
        {
            "question": "Solve for x:  2x + 3 = 11",
            "options": ["x = 3", "x = 4", "x = 5", "x = 7"],
            "answer_index": 1,
            "explanation": "Subtract 3: 2x = 8.  Divide by 2: x = 4.",
        },
        {
            "question": "Which value of x satisfies  x − 5 = 0?",
            "options": ["x = 0", "x = −5", "x = 5", "x = 10"],
            "answer_index": 2,
            "explanation": "Add 5 to both sides: x = 5.",
        },
    ],
    "Photosynthesis": [
        {
            "question": "What gas do plants release during photosynthesis?",
            "options": ["Carbon dioxide", "Nitrogen", "Oxygen", "Hydrogen"],
            "answer_index": 2,
            "explanation": "Plants split water molecules and release oxygen as a by-product.",
        },
        {
            "question": "Which organelle is the site of photosynthesis?",
            "options": ["Mitochondria", "Nucleus", "Ribosome", "Chloroplast"],
            "answer_index": 3,
            "explanation": "Chloroplasts contain chlorophyll, the pigment that captures light energy.",
        },
    ],
    "Cellular Respiration": [
        {
            "question": "What molecule stores energy produced during cellular respiration?",
            "options": ["DNA", "ATP", "ADP", "RNA"],
            "answer_index": 1,
            "explanation": "ATP (adenosine triphosphate) is the universal energy currency of the cell.",
        },
        {
            "question": "What gas do cells consume during aerobic respiration?",
            "options": ["Oxygen", "Carbon dioxide", "Nitrogen", "Methane"],
            "answer_index": 0,
            "explanation": "Aerobic respiration uses oxygen to fully break down glucose.",
        },
    ],
}

_DEFAULT_FALLBACK = [
    {
        "question": "Which of the following best describes a hypothesis?",
        "options": [
            "A proven fact",
            "A testable prediction",
            "A final conclusion",
            "An observation",
        ],
        "answer_index": 1,
        "explanation": "A hypothesis is a tentative, testable prediction made before an experiment.",
    }
]

_MODEL_NAME = "gemini-1.5-flash"

_QUIZ_PROMPT = """\
You are an AI tutor generating a multiple-choice quiz question for a student
studying '{topic}' ({subject}).  Their current mastery level is {mastery:.0%}
(0% = total beginner, 100% = fully mastered).

Generate exactly ONE question that is appropriately challenging for this mastery
level.  Respond ONLY with a JSON object in this exact shape — no markdown fences,
no extra keys:

{{
  "question": "...",
  "options": ["A", "B", "C", "D"],
  "answer_index": 0,
  "explanation": "One or two sentences explaining why the answer is correct."
}}

Rules:
- options must have exactly 4 elements
- answer_index is 0-based (0 = first option is correct)
- Keep question under 25 words; each option under 10 words
- Do NOT include A/B/C/D labels inside the option strings themselves
"""


def _fallback(topic_name: str) -> dict:
    pool = _FALLBACK_BANK.get(topic_name, _DEFAULT_FALLBACK)
    return random.choice(pool)


def generate_quiz(topic_name: str, subject: str, mastery: float) -> dict:
    """Return a dict with keys: question, options, answer_index, explanation."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set; returning fallback quiz question.")
        return _fallback(topic_name)

    prompt = _QUIZ_PROMPT.format(topic=topic_name, subject=subject, mastery=mastery)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_MODEL_NAME)
        response = model.generate_content(prompt)
        raw = getattr(response, "text", "") or ""
        # Strip potential markdown fences
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        # Validate shape
        assert isinstance(data["question"], str)
        assert isinstance(data["options"], list) and len(data["options"]) == 4
        assert isinstance(data["answer_index"], int) and 0 <= data["answer_index"] <= 3
        assert isinstance(data["explanation"], str)

        return data
    except Exception as exc:
        logger.error("Gemini quiz generation failed, using fallback: %s", exc)
        return _fallback(topic_name)
