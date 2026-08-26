"""
Database setup.

Uses SQLite by default so the whole backend runs with zero external
services -- important when you're demoing on hackathon wifi. The models
are written with the same shape you'd use for MongoDB collections
(Student, Topic, Content, Interaction, Mastery), so swapping the engine
line below for a Postgres/Mongo connection string later is a small change,
not a rewrite. See README.md "Swapping to MongoDB" for notes.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./ai_tutor.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
