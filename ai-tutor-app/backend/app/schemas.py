from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StudentCreate(BaseModel):
    name: str
    grade: Optional[str] = ""
    password: str


class LoginRequest(BaseModel):
    name: str
    password: str


class StudentOut(BaseModel):
    id: int
    name: str
    grade: str

    class Config:
        from_attributes = True


class AuthOut(BaseModel):
    token: str
    student: StudentOut


class TopicOut(BaseModel):
    id: int
    name: str
    subject: str

    class Config:
        from_attributes = True


class ContentOut(BaseModel):
    id: int
    topic_id: int
    title: str
    format: str
    difficulty: float

    class Config:
        from_attributes = True


class InteractionCreate(BaseModel):
    student_id: int
    content_id: int
    correct: bool
    time_taken_seconds: float = 0.0
    rewinds: int = 0
    quiz_session_id: Optional[str] = None


class InteractionOut(BaseModel):
    id: int
    student_id: int
    content_id: int
    correct: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MasteryUpdateOut(BaseModel):
    topic_id: int
    topic_name: str
    p_know_before: float
    p_know_after: float
    attempts: int


class RecommendationOut(BaseModel):
    content_id: int
    title: str
    format: str
    topic_id: int
    topic_name: str
    reason: str
    mastery_gap: float


class ExplainRequest(BaseModel):
    student_id: int
    topic_id: int
    style: Optional[str] = None  # "video" | "analogy" | "practice" -- auto-picked if omitted


class ExplainResponse(BaseModel):
    topic_name: str
    style_used: str
    mastery_level: float
    explanation: str


class DashboardTopicOut(BaseModel):
    topic_id: int
    topic_name: str
    p_know: float
    attempts: int
    status: str  # "struggling" | "developing" | "mastered"


class DashboardOut(BaseModel):
    student_id: int
    student_name: str
    topics: List[DashboardTopicOut]
    overall_mastery: float


# ---------- Quiz ----------

class QuizGenerateRequest(BaseModel):
    student_id: int
    topic_id: int


class QuizQuestion(BaseModel):
    topic_id: int
    topic_name: str
    content_id: int       # the practice content item to log the result against
    question: str
    options: List[str]    # exactly 4
    answer_index: int     # 0-based index of the correct option
    explanation: str


# ---------- Analytics ----------

class MasteryTrendPoint(BaseModel):
    recorded_at: datetime
    p_know: float
    correct: Optional[bool] = None    # the interaction that triggered this snapshot


class TopicTrend(BaseModel):
    topic_id: int
    topic_name: str
    current_p_know: float
    attempts: int
    status: str
    accuracy: float                   # fraction of correct attempts (0-1)
    trend: List[MasteryTrendPoint]    # chronological mastery snapshots


class StudentAnalyticsOut(BaseModel):
    student_id: int
    student_name: str
    overall_mastery: float
    topics: List[TopicTrend]


class ClassTopicStat(BaseModel):
    topic_id: int
    topic_name: str
    subject: str
    avg_mastery: float
    struggling_count: int
    developing_count: int
    mastered_count: int
    total_attempts: int


class ClassAnalyticsOut(BaseModel):
    total_students: int
    avg_overall_mastery: float
    topics: List[ClassTopicStat]
    recent_interactions: int          # interactions in last 24 h — liveness signal


class TopicSearchRequest(BaseModel):
    query: str
    grade: Optional[str] = ""


class TopicSource(BaseModel):
    title: str
    url: str


class TopicSearchOut(BaseModel):
    query: str
    title: str
    summary: str
    key_points: List[str]
    recommended_topics: List[str]
    sources: List[TopicSource]
    grounded: bool
