"""
Recommendation engine -- picks "what's next" for a student, the same job
a streaming service's homepage does.

Two decisions, made separately:
  1. WHICH TOPIC -- rank unlocked topics (prerequisites already decently
     mastered) by mastery gap, so the student is always pushed toward
     their biggest weak spot that they're actually ready for.
  2. WHICH FORMAT -- video / analogy(text) / practice -- inferred from
     that student's recent behavioural signals on this topic, not just
     right/wrong. This is the "how to teach it, not just what to teach"
     differentiator the deck calls out.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional

from . import models

TARGET_MASTERY = 0.85
PREREQ_UNLOCK_THRESHOLD = 0.5  # must have this much mastery in prereqs to unlock a topic


def _prereqs_met(db: Session, student_id: int, topic: models.Topic) -> bool:
    if not topic.prerequisites:
        return True
    prereq_names = [p.strip() for p in topic.prerequisites.split(",") if p.strip()]
    for name in prereq_names:
        prereq_topic = db.query(models.Topic).filter(models.Topic.name == name).first()
        if not prereq_topic:
            continue
        m = (
            db.query(models.Mastery)
            .filter(
                models.Mastery.student_id == student_id,
                models.Mastery.topic_id == prereq_topic.id,
            )
            .first()
        )
        p_know = m.p_know if m else prereq_topic.p_init
        if p_know < PREREQ_UNLOCK_THRESHOLD:
            return False
    return True


def pick_next_topic(db: Session, student_id: int) -> Optional[models.Topic]:
    """Largest mastery gap among topics whose prerequisites are met."""
    topics = db.query(models.Topic).all()
    best_topic, best_gap = None, -1.0

    for topic in topics:
        if not _prereqs_met(db, student_id, topic):
            continue
        m = (
            db.query(models.Mastery)
            .filter(
                models.Mastery.student_id == student_id,
                models.Mastery.topic_id == topic.id,
            )
            .first()
        )
        p_know = m.p_know if m else topic.p_init
        if p_know >= TARGET_MASTERY:
            continue  # already mastered, nothing to recommend here
        gap = TARGET_MASTERY - p_know
        if gap > best_gap:
            best_gap, best_topic = gap, topic

    return best_topic


def infer_preferred_format(db: Session, student_id: int, topic_id: int) -> str:
    """
    Look at the student's last few interactions on this topic to decide
    HOW to teach it next:
      - lots of rewinds/long time-on-task -> they need it re-explained
        differently -> "video" (or an analogy-style walkthrough)
      - repeated wrong answers with low hesitation -> they're guessing /
        need drilling -> "practice"
      - default -> "text" (a concise analogy-based explanation)
    """
    recent = (
        db.query(models.Interaction)
        .join(models.Content)
        .filter(
            models.Interaction.student_id == student_id,
            models.Content.topic_id == topic_id,
        )
        .order_by(desc(models.Interaction.created_at))
        .limit(5)
        .all()
    )

    if not recent:
        return "video"  # first exposure to a concept: start with a video

    avg_rewinds = sum(i.rewinds for i in recent) / len(recent)
    wrong_count = sum(1 for i in recent if not i.correct)

    if avg_rewinds >= 1.5:
        return "video"
    if wrong_count >= 2:
        return "practice"
    return "text"  # "text" content bodies are analogy-style explanations


def recommend_content(db: Session, student_id: int):
    """
    Returns (content, topic, reason, mastery_gap) or (None, None, reason, 0)
    if the student has mastered everything currently unlocked.
    """
    topic = pick_next_topic(db, student_id)
    if topic is None:
        return None, None, "All unlocked topics are at or above target mastery.", 0.0

    preferred_format = infer_preferred_format(db, student_id, topic.id)

    content = (
        db.query(models.Content)
        .filter(models.Content.topic_id == topic.id, models.Content.format == preferred_format)
        .order_by(models.Content.difficulty)
        .first()
    )
    if content is None:
        # fall back to any content on this topic
        content = (
            db.query(models.Content)
            .filter(models.Content.topic_id == topic.id)
            .first()
        )

    m = (
        db.query(models.Mastery)
        .filter(models.Mastery.student_id == student_id, models.Mastery.topic_id == topic.id)
        .first()
    )
    p_know = m.p_know if m else topic.p_init
    gap = TARGET_MASTERY - p_know

    reason = (
        f"Biggest mastery gap among unlocked topics ({p_know:.0%} -> target {TARGET_MASTERY:.0%}); "
        f"format '{preferred_format}' chosen from recent behaviour on this topic."
    )
    return content, topic, reason, gap
