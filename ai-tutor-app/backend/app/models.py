"""
ORM models.

Topic          -- a syllabus concept (e.g. "Linear Equations"). Has BKT priors.
Content        -- one teachable "asset" for a topic: a video, an analogy-style
                  explanation, or a practice drill. This is the thing the
                  recommender actually recommends (the "Netflix row").
Student        -- a learner.
Mastery        -- one row per (student, topic): current P(knows the skill),
                  maintained by the BKT engine.
Interaction    -- a single logged event: student attempted `content_id`,
                  got it right/wrong, took `time_taken_seconds`, etc.
MasteryHistory -- time-series snapshot of p_know appended after every interact
                  call. Powers the trend line in the analytics dashboard.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    subject = Column(String, nullable=False, default="General")
    # Comma-separated topic names this topic depends on, e.g. "Fractions"
    prerequisites = Column(String, default="")

    # BKT parameters (reasonable generic defaults; can be tuned per topic)
    p_init = Column(Float, default=0.3)      # prior P(student already knows it)
    p_transit = Column(Float, default=0.15)  # P(learns it after one attempt)
    p_slip = Column(Float, default=0.1)      # P(knows it but answers wrong)
    p_guess = Column(Float, default=0.2)     # P(doesn't know it but answers right)

    contents = relationship("Content", back_populates="topic")
    masteries = relationship("Mastery", back_populates="topic")


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    title = Column(String, nullable=False)
    format = Column(String, nullable=False)     # "video" | "text" | "practice"
    difficulty = Column(Float, default=0.5)      # 0 (easy) - 1 (hard)
    body = Column(Text, default="")               # static fallback content

    topic = relationship("Topic", back_populates="contents")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    grade = Column(String, default="")
    password_hash = Column(String, nullable=True)
    private_data = Column(Text, nullable=True)

    masteries = relationship("Mastery", back_populates="student")
    interactions = relationship("Interaction", back_populates="student")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class Mastery(Base):
    __tablename__ = "masteries"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    p_know = Column(Float, default=0.3)  # current BKT mastery probability
    attempts = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="masteries")
    topic = relationship("Topic", back_populates="masteries")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    correct = Column(Boolean, nullable=False)
    time_taken_seconds = Column(Float, default=0.0)
    rewinds = Column(Integer, default=0)   # video pauses/rewinds -- hesitation signal
    quiz_session_id = Column(String, nullable=True)   # groups answers from one quiz run
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="interactions")
    content = relationship("Content")


class MasteryHistory(Base):
    """Time-series record of a student's BKT mastery for one topic.
    One row is appended every time /interact is called.  Used by the
    analytics dashboard to draw mastery-over-time trend lines.
    """
    __tablename__ = "mastery_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    p_know = Column(Float, nullable=False)
    correct = Column(Boolean, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    student = relationship("Student")
    topic = relationship("Topic")
