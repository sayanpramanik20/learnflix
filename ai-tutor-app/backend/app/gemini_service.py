"""
Gemini integration -- this is the "AI" in AI Tutor.

Everything else in this backend (BKT, recommender) decides WHAT the
student should study next. This module generates the actual
explanation, in the teaching style the recommender picked, personalised
to that student's current mastery level. This is the part to point at
during the demo when judges ask "where's the AI."

Uses google-generativeai with the free-tier "gemini-1.5-flash" model
(fast + generous free quota, good for a live demo). Falls back to a
canned explanation if GEMINI_API_KEY isn't set or the call fails, so a
flaky venue wifi never breaks your demo mid-presentation.
"""
import os
import logging
import json

logger = logging.getLogger("ai_tutor.gemini")

_MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemma-4-26b-a4b-it")
_SEARCH_MODEL_NAME = os.environ.get("GEMINI_SEARCH_MODEL", "gemini-3.6-flash")

_SEARCH_PROMPT = """
You are a careful school tutor helping a {grade} student learn about "{query}".
Use Google Search grounding to verify current facts. Return ONLY valid JSON with
this exact shape:
{{
    "title": "short topic title",
    "summary": "a clear 120-word explanation for the student",
    "key_points": ["three concise factual takeaways"],
    "recommended_topics": ["three logical next topics to study"]
}}
Do not invent citations or URLs. Explain unfamiliar terms, mention uncertainty
when sources disagree, and avoid presenting current events as timeless facts.
"""

STYLE_INSTRUCTIONS = {
    "video": (
        "Write this as a short spoken video-narration script (like a YouTube "
        "explainer): conversational, step-by-step, with a concrete visual example "
        "the narrator would point to."
    ),
    "text": (
        "Explain this primarily through ONE clear real-world analogy, then connect "
        "the analogy explicitly back to the concept. Keep it concise."
    ),
    "practice": (
        "Give a very short refresher (2-3 sentences), then write ONE practice "
        "problem similar to what the student keeps getting wrong, followed by a "
        "step-by-step worked solution."
    ),
}


def _fallback_explanation(topic_name: str, style: str, mastery: float) -> str:
    level = "just starting out on" if mastery < 0.4 else (
        "getting the basics of" if mastery < 0.75 else "close to mastering"
    )
    return (
        f"[Offline fallback -- set GEMINI_API_KEY for live AI generation]\n"
        f"This student is {level} '{topic_name}'. A {style}-style explanation would "
        f"normally be generated here by Gemini, tailored to their current mastery "
        f"level ({mastery:.0%}) and recent mistakes."
    )


def generate_explanation(topic_name: str, style: str, mastery: float, subject: str = "") -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set; returning fallback explanation.")
        return _fallback_explanation(topic_name, style, mastery)

    style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["text"])

    prompt = (
        f"You are an AI tutor for a school student studying '{topic_name}'"
        f"{f' ({subject})' if subject else ''}.\n"
        f"Their current estimated mastery of this concept is {mastery:.0%} "
        f"(0% = no understanding, 100% = fully mastered).\n"
        f"{style_instruction}\n"
        f"Keep the whole response under 180 words. Do not mention the mastery "
        f"percentage number itself in the output -- just calibrate the difficulty "
        f"and pace to it."
    )

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_MODEL_NAME)
        response = model.generate_content(prompt)
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Empty response from Gemini")
        return text.strip()
    except Exception as exc:  # noqa: BLE001 -- demo resilience matters more than exact type
        logger.error("Gemini call failed, using fallback: %s", exc)
        return _fallback_explanation(topic_name, style, mastery)


def search_and_teach(query: str, grade: str = "") -> dict:
    """Search the web with Gemini grounding and turn the result into a lesson."""
    fallback = {
        "title": query.strip().title(),
        "summary": (
            "Add GEMINI_API_KEY to enable internet-grounded learning. "
            "Once enabled, this search will use Google Search to build a current explanation."
        ),
        "key_points": ["Search grounding is currently unavailable."],
        "recommended_topics": [query, "How to evaluate sources", "Related real-world applications"],
        "sources": [],
        "grounded": False,
    }
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not query.strip():
        return fallback

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(_SEARCH_MODEL_NAME, tools=[{"google_search_retrieval": {}}])
        response = model.generate_content(_SEARCH_PROMPT.format(grade=grade or "school", query=query.strip()))
        raw = (getattr(response, "text", "") or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        if not isinstance(data.get("key_points"), list) or not isinstance(data.get("recommended_topics"), list):
            raise ValueError("Gemini returned an invalid topic lesson")

        sources = []
        metadata = getattr(response, "grounding_metadata", None)
        for chunk in getattr(metadata, "grounding_chunks", []) or []:
            web = getattr(chunk, "web", None)
            url = getattr(web, "uri", "") if web else ""
            title = getattr(web, "title", "Source") if web else "Source"
            if url:
                sources.append({"title": title, "url": url})

        return {
            "title": str(data.get("title", query.title())),
            "summary": str(data.get("summary", "")),
            "key_points": [str(point) for point in data["key_points"][:5]],
            "recommended_topics": [str(topic) for topic in data["recommended_topics"][:5]],
            "sources": sources,
            "grounded": bool(sources),
        }
    except Exception as exc:
        logger.error("Gemini topic search failed, using fallback: %s", exc)
        return fallback
