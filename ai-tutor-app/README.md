# AI Tutor — Infinity Loop (SBHRCCIIT035)

Full stack in one folder:

```
ai-tutor-app/
├── backend/    FastAPI + SQLite + BKT engine + Gemini integration
└── frontend/   React + Vite UI
```

## Run it (two terminals)

**Terminal 1 — backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # paste a free key from https://aistudio.google.com/app/apikey
uvicorn app.main:app --reload
```
Leave this running. Check `http://127.0.0.1:8000/docs` loads.

**Terminal 2 — frontend**
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

If the frontend shows a red banner saying it can't reach the backend, the
backend terminal isn't running or is on a different port — check `.env` in
`frontend/` matches.

## What I could and couldn't test from here

This sandbox has no internet access (`pip install` and `npm install` both get
blocked by the network egress policy — verified: PyPI and the npm registry
both return 403 here), so I could not actually spin up uvicorn or Vite and
click through the app end-to-end myself. Be sure to run the checklist below
once, tonight, before you rely on it.

What I *could* verify without network, and did:
- Every `.py` file compiles cleanly (`python3 -m py_compile`) — no syntax errors.
- Every `.jsx`/`.js` file parses cleanly (`esbuild` transform) — no syntax errors.
- The BKT mastery-update algorithm itself, run standalone with no dependencies:
  a sequence of right/wrong answers produces a `p_know` that rises on correct
  answers, dips on a wrong one, stays within `[0, 1]`, and converges toward
  "mastered" — confirmed with real numbers, not just eyeballed.

What's *not* verified: that FastAPI wires the routes correctly at runtime,
that the frontend's fetch calls match the backend's actual response shapes
once real JSON is flowing, and that the Gemini call succeeds with a real key.
These only surface by actually running both servers.

## Local test checklist (run this once, tonight)

1. `cd backend && uvicorn app.main:app --reload` — should print `Application
   startup complete` with no traceback. If it errors immediately, read the
   traceback; it'll usually be a missing package (`pip install -r
   requirements.txt` again) or a port already in use.
2. Open `http://127.0.0.1:8000/docs` — you should see the Swagger UI with all
   8 endpoints listed. Try `GET /topics` there directly ("Try it out" → 
   "Execute") — should return 4 seeded topics.
3. `cd backend && python demo.py` (backend still running in terminal 1) —
   walks the whole flow end to end and prints each step. If this completes
   without a traceback, the backend logic is solid.
4. `cd frontend && npm run dev`, open `localhost:5173` — add a student, you
   should see a recommendation card and topic rings appear within a second.
5. Click "Got it wrong" twice, then "Explain this to me" — if you set a real
   `GEMINI_API_KEY`, you'll see AI-generated text within a couple seconds; if
   not, you'll see the labeled offline fallback text (not an error) — both
   are correct behavior.
6. Click "Got it right" a few times — the mastery ring should visibly climb
   and the status badge should change color/label.

If any step fails, the error message (terminal traceback or the browser's
network tab) will point at the exact file — send it back to me and I'll fix
it directly rather than guessing blind.
