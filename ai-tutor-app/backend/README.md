# AI Tutor Backend — Infinity Loop (SBHRCCIIT035)

A working backend for "AI Tutor: The Netflix of Learning" — adapts what a
student studies next and how it's explained, based on their real answers.

## What it actually does

1. **Logs every attempt** (`POST /interact`) — right/wrong, time taken, video rewinds.
2. **Updates a mastery score per topic** using Bayesian Knowledge Tracing (BKT) —
   a real, published algorithm (Corbett & Anderson, 1994), not a hardcoded number.
3. **Recommends the next topic + format** (`GET /recommend/{student_id}`) — biggest
   mastery gap among unlocked topics, in whichever format (video/text/practice)
   this student's recent behaviour suggests they need.
4. **Generates a personalised explanation** (`POST /explain`) via the **Gemini API**
   — the same topic explained differently depending on the student's mastery level
   and chosen format. This is the live "AI" part to show judges.
5. **Gives a teacher/parent dashboard** (`GET /dashboard/{student_id}`) — mastery
   per topic across the whole syllabus.

## Setup (5 minutes)

```bash
cd ai-tutor-backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste your free Gemini key from https://aistudio.google.com/app/apikey

# Optional model configuration:
# GEMINI_MODEL=gemma-4-26b-a4b-it
# GEMINI_SEARCH_MODEL=gemini-3.6-flash

uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** — interactive Swagger UI, seeded with sample
topics/content on first run. This is genuinely fine to demo directly from if you
don't have time to build a frontend.

No `GEMINI_API_KEY`? The `/explain` endpoint still works — it returns a clearly
labeled fallback explanation instead of failing, so a flaky venue wifi or an
unset key never breaks the demo mid-presentation.

Gemma 4 26B can power tutor explanations through `GEMINI_MODEL`. Internet topic
search uses `GEMINI_SEARCH_MODEL` because Google Search grounding is a Gemini
tool capability and may not be supported by Gemma models.

### Rehearse the full flow

```bash
python demo.py   # in a second terminal, while uvicorn is running
```

Creates a student, simulates them struggling on "Fractions," shows the
recommendation switch to practice drills, pulls a live Gemini explanation, then
simulates them improving and shows mastery climb on the dashboard.

## Architecture

```
Student answers a question / watches a video
        │
        ▼
POST /interact  ──────────────►  BKT engine (app/bkt.py)
   (right/wrong, time,               updates P(knows topic)
    rewinds)                          for that student+topic
        │
        ▼
GET /recommend/{id}  ──────────► Recommender (app/recommender.py)
                                   1. which topic = biggest mastery
                                      gap among unlocked topics
                                   2. which format = inferred from
                                      recent rewinds / wrong answers
        │
        ▼
POST /explain  ────────────────► Gemini API (app/gemini_service.py)
                                   generates the explanation in that
                                   format, calibrated to mastery level
        │
        ▼
GET /dashboard/{id}  ──────────► teacher/parent view across topics
```

**Data model** (`app/models.py`): `Student`, `Topic` (with BKT params +
prerequisites), `Content` (video/text/practice per topic), `Interaction` (raw
log), `Mastery` (current P(know) per student×topic).

## Honest scope note (say this to judges, don't hide it)

The deck names a **PyTorch Deep Knowledge Tracing** model as the long-term
approach — that needs a trained dataset, which you won't have by tomorrow. BKT
is the standard lightweight substitute: same job (tracking per-skill mastery
probability from attempt data), zero training data required, closed-form
update. Frame it as **"BKT now, DKT is the trained-model upgrade path once we
have usage data"** — that's a legitimate, defensible roadmap, not a shortcut
you have to hide.

## Swapping to MongoDB later

Everything is SQLAlchemy models talking to SQLite (`app/database.py`) — chosen
so the demo never depends on a database server being reachable. Each ORM model
maps directly onto a Mongo collection with the same fields (`Student`, `Topic`,
`Content`, `Interaction`, `Mastery`), so migrating means swapping the query
layer, not redesigning the schema.

## Endpoint reference

| Method | Path | Purpose |
|---|---|---|
| POST | `/students` | create a student |
| GET | `/students` | list students |
| GET | `/topics` | list topics |
| GET | `/topics/{id}/contents` | content items for a topic |
| POST | `/interact` | log an attempt, updates mastery |
| GET | `/recommend/{student_id}` | next content to show |
| POST | `/explain` | Gemini-generated personalised explanation |
| GET | `/dashboard/{student_id}` | mastery across all topics |
