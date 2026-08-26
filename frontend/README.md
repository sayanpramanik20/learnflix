# AI Tutor Frontend

React + Vite frontend for the AI Tutor backend. Talks to every endpoint the
backend exposes:

| UI element | Backend call |
|---|---|
| Student dropdown / "Add" | `GET /students`, `POST /students` |
| "Recommended for you" hero card | `GET /recommend/{id}` |
| "Got it right / wrong" buttons | `POST /interact` (updates BKT mastery live) |
| "Explain this to me" + style chips | `POST /explain` (Gemini) |
| Topic rows with mastery rings | `GET /dashboard/{id}` |

## Setup

```bash
cd ai-tutor-frontend
npm install
cp .env.example .env       # only needed if your backend isn't on port 8000
npm run dev
```

Open **http://localhost:5173**. Make sure the backend is running first
(`uvicorn app.main:app --reload` from the `ai-tutor-backend` folder) — the
app will show a red banner at the top if it can't reach it.

## How the pieces connect

`src/api.js` is the only file that knows the backend's URL and endpoint
shapes — every component calls through it, never `fetch` directly. If you
change a backend response shape, that's the one file to update.

`App.jsx` owns all state (current student, dashboard, recommendation, tutor
panel) and passes data + callbacks down to the presentational components in
`src/components/`. After any action that changes mastery (`handleAnswer`),
it re-fetches both the dashboard and the recommendation, so the "Recommended
for you" card and the topic mastery rings update immediately — that's the
loop that makes the adaptivity visible in a live demo.

## Demo flow to rehearse

1. Add a student.
2. Click **"Got it wrong"** twice on the recommended practice drill —
   watch the topic's mastery ring drop and the recommendation reason update.
3. Click **"Explain this to me"** — a real Gemini call generates an
   explanation matched to the student's current mastery and the struggling
   format (usually switches to "practice" after repeated misses).
4. Click **"Got it right"** a few times — watch the ring climb and the
   status badge move from *Struggling* → *Developing* → *Mastered*.
5. Click a different topic row directly to pull an explanation for it,
   and try the style chips (Video / Analogy / Practice) to show the same
   concept explained three different ways.

## Notes for judges / production hardening (not needed for the demo)

- CORS is wide open (`*`) on the backend for demo convenience — restrict it
  to your deployed frontend origin before any real deployment.
- No auth — students are just names in a dropdown. A real deployment needs
  login and per-teacher/class scoping.
