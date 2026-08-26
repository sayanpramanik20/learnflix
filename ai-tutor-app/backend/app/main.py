"""
AI Tutor backend -- FastAPI app.

Endpoint map:
  POST /students                       create a student
  GET  /students                       list students
  GET  /topics                         list topics (+ content)
  POST /interact                       log a quiz/video attempt -> updates BKT mastery
  GET  /recommend/{student_id}         "recommended for you" -- what to study next
  POST /explain                        Gemini-generated personalised explanation
  GET  /dashboard/{student_id}         teacher/parent view across all topics

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs  (interactive Swagger UI -- good for a live demo)
"""
from dotenv import load_dotenv
load_dotenv()  # picks up GEMINI_API_KEY from a local .env file, if present

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import List
import hashlib
import hmac
import json
import os
import secrets

from cryptography.fernet import Fernet, InvalidToken

from . import models, schemas, recommender, gemini_service, quiz_service
from .database import engine, Base, get_db
from .bkt import update_mastery, mastery_status, BKTParams
from .seed import seed as seed_db

Base.metadata.create_all(bind=engine)

security = HTTPBearer(auto_error=False)
SESSION_DAYS = 7


def _fernet():
    key = os.environ.get("DATA_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("DATA_ENCRYPTION_KEY is required")
    return Fernet(key.encode())


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{salt.hex()}${digest.hex()}"


def _check_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000)
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def _encrypt_profile(name: str, grade: str) -> str:
    return _fernet().encrypt(json.dumps({"name": name, "grade": grade}).encode()).decode()


def _issue_session(student: models.Student, db: Session) -> str:
    token = secrets.token_urlsafe(32)
    db.add(models.AuthSession(
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        student_id=student.id,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DAYS),
    ))
    return token


def current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.Student:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Login required")
    token_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    session = (
        db.query(models.AuthSession)
        .filter(models.AuthSession.token_hash == token_hash, models.AuthSession.expires_at > datetime.utcnow())
        .first()
    )
    if not session:
        raise HTTPException(401, "Session expired or invalid")
    return session.student


def require_owner(student_id: int, student: models.Student):
    if student_id != student.id:
        raise HTTPException(403, "You cannot access another student's data")

app = FastAPI(
    title="AI Tutor API",
    description="Adaptive tutoring backend -- SIH problem statement SBHRCCIIT035",
    version="0.1.0",
)

# Wide-open CORS for hackathon demo purposes (tighten before any real deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # create_all does not add columns to an existing SQLite demo database.
    with engine.begin() as connection:
        student_columns = connection.execute(text("PRAGMA table_info(students)")).fetchall()
        if student_columns and not any(column[1] == "password_hash" for column in student_columns):
            try:
                connection.execute(text("ALTER TABLE students ADD COLUMN password_hash VARCHAR"))
            except Exception:
                pass
        if student_columns and not any(column[1] == "private_data" for column in student_columns):
            try:
                connection.execute(text("ALTER TABLE students ADD COLUMN private_data TEXT"))
            except Exception:
                pass
    with engine.begin() as connection:
        interaction_columns = connection.execute(text("PRAGMA table_info(interactions)")).fetchall()
        if interaction_columns and not any(column[1] == "quiz_session_id" for column in interaction_columns):
            try:
                connection.execute(text("ALTER TABLE interactions ADD COLUMN quiz_session_id VARCHAR"))
            except Exception:
                pass
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(mastery_history)")).fetchall()
        if columns and not any(column[1] == "correct" for column in columns):
            try:
                connection.execute(text("ALTER TABLE mastery_history ADD COLUMN correct BOOLEAN"))
            except Exception:
                pass
    seed_db()


@app.get("/", tags=["meta"])
def root():
    return {"status": "ok", "service": "ai-tutor-backend"}


# ---------- Students ----------

@app.post("/auth/register", response_model=schemas.AuthOut, tags=["auth"])
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    if len(payload.password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters")
    if db.query(models.Student).filter(models.Student.name == payload.name.strip()).first():
        raise HTTPException(409, "That student name is already registered")
    student = models.Student(
        name=payload.name.strip(),
        grade=payload.grade or "",
        password_hash=_hash_password(payload.password),
        private_data=_encrypt_profile(payload.name.strip(), payload.grade or ""),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    token = _issue_session(student, db)
    db.commit()
    return schemas.AuthOut(token=token, student=student)


@app.post("/auth/login", response_model=schemas.AuthOut, tags=["auth"])
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.name == payload.name.strip()).first()
    if not student or not student.password_hash or not _check_password(payload.password, student.password_hash):
        raise HTTPException(401, "Invalid student name or password")
    token = _issue_session(student, db)
    db.commit()
    return schemas.AuthOut(token=token, student=student)


@app.post("/auth/logout", tags=["auth"])
def logout(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    if credentials:
        token_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()
        db.query(models.AuthSession).filter(models.AuthSession.token_hash == token_hash).delete()
        db.commit()
    return {"status": "ok"}


@app.get("/students/me", response_model=schemas.StudentOut, tags=["students"])
def me(student: models.Student = Depends(current_student)):
    return student


# ---------- Topics / Content ----------

@app.get("/topics", response_model=List[schemas.TopicOut], tags=["content"])
def list_topics(db: Session = Depends(get_db)):
    return db.query(models.Topic).all()


@app.get("/topics/{topic_id}/contents", response_model=List[schemas.ContentOut], tags=["content"])
def list_topic_contents(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    return db.query(models.Content).filter(models.Content.topic_id == topic_id).all()


# ---------- Interactions (the raw learning signal) ----------

@app.post("/interact", response_model=schemas.MasteryUpdateOut, tags=["learning"])
def log_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db), student: models.Student = Depends(current_student)):
    require_owner(payload.student_id, student)
    student = db.query(models.Student).get(payload.student_id)
    content = db.query(models.Content).get(payload.content_id)
    if not student or not content:
        raise HTTPException(404, "Student or content not found")

    interaction = models.Interaction(
        student_id=payload.student_id,
        content_id=payload.content_id,
        correct=payload.correct,
        time_taken_seconds=payload.time_taken_seconds,
        rewinds=payload.rewinds,
    )
    db.add(interaction)

    topic = content.topic
    mastery = (
        db.query(models.Mastery)
        .filter(models.Mastery.student_id == student.id, models.Mastery.topic_id == topic.id)
        .first()
    )
    if mastery is None:
        mastery = models.Mastery(student_id=student.id, topic_id=topic.id, p_know=topic.p_init, attempts=0)
        db.add(mastery)
        db.flush()

    p_before = mastery.p_know
    params = BKTParams(p_transit=topic.p_transit, p_slip=topic.p_slip, p_guess=topic.p_guess)
    p_after = update_mastery(p_before, payload.correct, params)

    mastery.p_know = p_after
    mastery.attempts += 1

    db.add(
        models.MasteryHistory(
            student_id=student.id,
            topic_id=topic.id,
            p_know=p_after,
            correct=payload.correct,
        )
    )

    db.commit()

    return schemas.MasteryUpdateOut(
        topic_id=topic.id,
        topic_name=topic.name,
        p_know_before=round(p_before, 4),
        p_know_after=round(p_after, 4),
        attempts=mastery.attempts,
    )


# ---------- Micro-quiz ----------

@app.post("/quiz/generate", response_model=schemas.QuizQuestion, tags=["quiz"])
def generate_quiz(payload: schemas.QuizGenerateRequest, db: Session = Depends(get_db), student: models.Student = Depends(current_student)):
    require_owner(payload.student_id, student)
    student = db.query(models.Student).get(payload.student_id)
    topic = db.query(models.Topic).get(payload.topic_id)
    if not student or not topic:
        raise HTTPException(404, "Student or topic not found")

    practice = (
        db.query(models.Content)
        .filter(models.Content.topic_id == topic.id, models.Content.format == "practice")
        .first()
    )
    if not practice:
        raise HTTPException(404, "No practice content found for this topic")

    mastery = (
        db.query(models.Mastery)
        .filter(models.Mastery.student_id == student.id, models.Mastery.topic_id == topic.id)
        .first()
    )
    question = quiz_service.generate_quiz(
        topic_name=topic.name,
        subject=topic.subject,
        mastery=mastery.p_know if mastery else topic.p_init,
    )
    return schemas.QuizQuestion(topic_id=topic.id, topic_name=topic.name, content_id=practice.id, **question)


# ---------- Recommendation ("Netflix of Learning") ----------

@app.get("/recommend/{student_id}", response_model=schemas.RecommendationOut, tags=["learning"])
def recommend(student_id: int, db: Session = Depends(get_db), student: models.Student = Depends(current_student)):
    require_owner(student_id, student)
    student = db.query(models.Student).get(student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    content, topic, reason, gap = recommender.recommend_content(db, student_id)
    if content is None:
        raise HTTPException(404, reason)  # nothing left to recommend -- still informative

    return schemas.RecommendationOut(
        content_id=content.id,
        title=content.title,
        format=content.format,
        topic_id=topic.id,
        topic_name=topic.name,
        reason=reason,
        mastery_gap=round(gap, 4),
    )


# ---------- AI-generated explanation (Gemini) ----------

@app.post("/explain", response_model=schemas.ExplainResponse, tags=["ai"])
def explain(payload: schemas.ExplainRequest, db: Session = Depends(get_db), student: models.Student = Depends(current_student)):
    require_owner(payload.student_id, student)
    student = db.query(models.Student).get(payload.student_id)
    topic = db.query(models.Topic).get(payload.topic_id)
    if not student or not topic:
        raise HTTPException(404, "Student or topic not found")

    style = payload.style or recommender.infer_preferred_format(db, payload.student_id, payload.topic_id)

    mastery = (
        db.query(models.Mastery)
        .filter(models.Mastery.student_id == student.id, models.Mastery.topic_id == topic.id)
        .first()
    )
    p_know = mastery.p_know if mastery else topic.p_init

    explanation_text = gemini_service.generate_explanation(
        topic_name=topic.name, style=style, mastery=p_know, subject=topic.subject
    )

    return schemas.ExplainResponse(
        topic_name=topic.name,
        style_used=style,
        mastery_level=round(p_know, 4),
        explanation=explanation_text,
    )


# ---------- Dashboard (teacher / parent view) ----------

@app.get("/dashboard/{student_id}", response_model=schemas.DashboardOut, tags=["dashboard"])
def dashboard(student_id: int, db: Session = Depends(get_db), student: models.Student = Depends(current_student)):
    require_owner(student_id, student)
    student = db.query(models.Student).get(student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    topics = db.query(models.Topic).all()
    rows = []
    total = 0.0
    for topic in topics:
        m = (
            db.query(models.Mastery)
            .filter(models.Mastery.student_id == student_id, models.Mastery.topic_id == topic.id)
            .first()
        )
        p_know = m.p_know if m else topic.p_init
        attempts = m.attempts if m else 0
        total += p_know
        rows.append(
            schemas.DashboardTopicOut(
                topic_id=topic.id,
                topic_name=topic.name,
                p_know=round(p_know, 4),
                attempts=attempts,
                status=mastery_status(p_know),
            )
        )

    overall = total / len(topics) if topics else 0.0
    return schemas.DashboardOut(
        student_id=student.id,
        student_name=student.name,
        topics=rows,
        overall_mastery=round(overall, 4),
    )


# ---------- Analytics ----------

@app.get("/analytics/student/{student_id}", response_model=schemas.StudentAnalyticsOut, tags=["analytics"])
def student_analytics(student_id: int, db: Session = Depends(get_db), student: models.Student = Depends(current_student)):
    require_owner(student_id, student)
    student = db.query(models.Student).get(student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    topics = db.query(models.Topic).all()
    rows = []
    total = 0.0
    for topic in topics:
        mastery = (
            db.query(models.Mastery)
            .filter(models.Mastery.student_id == student_id, models.Mastery.topic_id == topic.id)
            .first()
        )
        history = (
            db.query(models.MasteryHistory)
            .filter(
                models.MasteryHistory.student_id == student_id,
                models.MasteryHistory.topic_id == topic.id,
            )
            .order_by(models.MasteryHistory.recorded_at.asc())
            .all()
        )
        interactions = (
            db.query(models.Interaction)
            .join(models.Content)
            .filter(models.Interaction.student_id == student_id, models.Content.topic_id == topic.id)
            .all()
        )
        current = mastery.p_know if mastery else topic.p_init
        total += current
        rows.append(
            schemas.TopicTrend(
                topic_id=topic.id,
                topic_name=topic.name,
                current_p_know=round(current, 4),
                attempts=len(interactions),
                status=mastery_status(current),
                accuracy=round(sum(1 for item in interactions if item.correct) / len(interactions), 4) if interactions else 0.0,
                trend=[schemas.MasteryTrendPoint(recorded_at=item.recorded_at, p_know=item.p_know, correct=item.correct) for item in history],
            )
        )

    return schemas.StudentAnalyticsOut(
        student_id=student.id,
        student_name=student.name,
        overall_mastery=round(total / len(topics), 4) if topics else 0.0,
        topics=rows,
    )


@app.get("/analytics/class", response_model=schemas.ClassAnalyticsOut, tags=["analytics"])
def class_analytics(db: Session = Depends(get_db)):
    students = db.query(models.Student).all()
    topics = db.query(models.Topic).all()
    student_masteries = []
    for student in students:
        values = []
        for topic in topics:
            mastery = (
                db.query(models.Mastery)
                .filter(models.Mastery.student_id == student.id, models.Mastery.topic_id == topic.id)
                .first()
            )
            values.append(mastery.p_know if mastery else topic.p_init)
        student_masteries.append(sum(values) / len(values) if values else 0.0)

    topic_rows = []
    for topic in topics:
        values = []
        attempts = 0
        for student in students:
            mastery = (
                db.query(models.Mastery)
                .filter(models.Mastery.student_id == student.id, models.Mastery.topic_id == topic.id)
                .first()
            )
            value = mastery.p_know if mastery else topic.p_init
            values.append(value)
            attempts += mastery.attempts if mastery else 0
        topic_rows.append(
            schemas.ClassTopicStat(
                topic_id=topic.id,
                topic_name=topic.name,
                subject=topic.subject,
                avg_mastery=round(sum(values) / len(values), 4) if values else 0.0,
                struggling_count=sum(1 for value in values if mastery_status(value) == "struggling"),
                developing_count=sum(1 for value in values if mastery_status(value) == "developing"),
                mastered_count=sum(1 for value in values if mastery_status(value) == "mastered"),
                total_attempts=attempts,
            )
        )

    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent = db.query(models.Interaction).filter(models.Interaction.created_at >= cutoff).count()
    return schemas.ClassAnalyticsOut(
        total_students=len(students),
        avg_overall_mastery=round(sum(student_masteries) / len(student_masteries), 4) if student_masteries else 0.0,
        topics=topic_rows,
        recent_interactions=recent,
    )


@app.post("/learn/search", response_model=schemas.TopicSearchOut, tags=["learning"])
def search_topic(payload: schemas.TopicSearchRequest):
    query = payload.query.strip()
    if len(query) < 2:
        raise HTTPException(422, "Search for at least two characters")
    return schemas.TopicSearchOut(query=query, **gemini_service.search_and_teach(query, payload.grade or ""))
