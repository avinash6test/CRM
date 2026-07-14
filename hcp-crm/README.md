# AI-First CRM — HCP Module: Log Interaction Screen

A prototype "Log HCP Interaction" screen for a pharma field-force CRM. Reps can log a
visit either through a **structured form** or a **conversational chat panel**, both backed
by the same LangGraph agent and database.

---

## 1. Architecture

```
frontend/   React 18 + Redux Toolkit (Vite)
backend/    FastAPI (Python) + LangGraph agent + SQLAlchemy
            LLMs served via Groq: gemma2-9b-it (primary), llama-3.3-70b-versatile (fallback)
db/         PostgreSQL (MySQL-compatible schema, no vendor-specific SQL used)
```

- **Frontend** renders the two-pane screen from the brief: the interaction form on the
  left (HCP, type, date/time, attendees, topics, materials/samples, sentiment, outcomes,
  follow-ups) and an AI Assistant chat panel on the right. Redux (`interactionSlice`,
  `chatSlice`) holds form state and chat history; a chat reply that carries a
  `draft_interaction` payload is merged straight into the form via `applyAgentDraft`, so
  logging by chat and logging by form update the same record.
- **Backend** exposes REST CRUD for HCPs/Interactions (`/api/hcps`, `/api/interactions`)
  plus a single agent endpoint, `/api/chat`, that runs the LangGraph graph on every turn.

## 2. Role of the LangGraph Agent

The LangGraph agent is the reasoning layer sitting behind the chat panel (and, by reuse of
its tools, behind the "Summarize from Voice Note" action on the form). Its job is to turn a
rep's unstructured description of a visit into a structured, auditable CRM record without
the rep filling in every field by hand, while staying strictly grounded in tools rather than
hallucinating data. Concretely it:

1. **Interprets intent** each turn — is the rep describing a brand-new interaction, correcting
   one just logged, asking to look up an HCP, or asking for coaching-style suggestions?
2. **Fills missing slots conversationally** — if the note doesn't mention who was discussed
   or the HCP name is ambiguous, it asks a short clarifying question rather than guessing.
3. **Calls tools to do anything that touches the database or requires the LLM** (entity
   extraction, sentiment inference, persistence, edits) — the agent itself never writes to
   the DB directly, only through the tool layer, which keeps every write auditable.
4. **Loops** (LangGraph's conditional edge) between the `agent` node and a `ToolNode` until
   no more tool calls are requested, then returns a natural-language confirmation plus a
   `draft_interaction` object the frontend can render into the form.
5. **Keeps the rep in control** — every AI action (summarized topics, inferred sentiment,
   suggested follow-ups) is shown back to the rep for the record, not silently auto-saved as
   final; the two write tools (`log_interaction`, `edit_interaction`) are also directly
   reusable from the structured form's "Summarize from Voice Note" button.

Graph shape (`backend/app/agent/graph.py`):

```
START -> agent ──tool_calls?──> tools -> agent ──no tool calls──> END
```

## 3. The Five Tools (`backend/app/agent/tools.py`)

| # | Tool | Purpose |
|---|------|---------|
| 1 | `search_hcp` | Resolves a spoken/typed HCP name to a canonical HCP record (id, specialty, institution) before logging or editing, so interactions never get attached to an ambiguous or duplicate HCP. |
| 2 | **`log_interaction`** | See below. |
| 3 | **`edit_interaction`** | See below. |
| 4 | `analyze_sentiment` | Classifies HCP sentiment (positive/neutral/negative + confidence) from the note text; called internally by `log_interaction` and also exposed standalone so the agent can re-score sentiment if the rep corrects it ("actually he seemed lukewarm, not positive"). |
| 5 | `suggest_follow_ups` | Given an interaction summary, asks the LLM for 2–4 concrete next-best-actions (e.g. "Schedule follow-up in 2 weeks", "Send Phase III data on request") — mirrors the "AI Suggested Follow-ups" list shown in the mock. |

### `log_interaction` (required tool #1)
Input: `hcp_name`, freeform `note` (typed chat message or a voice-note transcript), `source`.
Steps:
1. Sends the note to the Groq LLM with a strict entity-extraction prompt asking for JSON:
   interaction type, attendees, topics discussed, materials shared, samples distributed,
   outcomes, follow-up actions. If gemma2-9b-it returns malformed JSON, it retries once on
   `llama-3.3-70b-versatile` before giving up gracefully.
2. Resolves or creates the `HCP` row via a fuzzy name match.
3. Calls `analyze_sentiment` on the same note.
4. Persists a new `Interaction` row (SQLAlchemy) with `source="chat"` (or `"voice"`) so it's
   distinguishable in reporting from form-entered records, and keeps the raw note
   (`raw_voice_note`) for audit/compliance review.
5. Returns the structured record as JSON — this is what the frontend renders as
   `draft_interaction` and merges into the visible form fields for the rep to confirm/edit.

### `edit_interaction` (required tool #2)
Input: `interaction_id`, `updates` (a JSON object of only the fields that changed).
Steps:
1. Loads the existing `Interaction` row by id (the agent gets this id from the prior
   `log_interaction`/`edit_interaction` tool result carried in conversation state).
2. Whitelists the patchable fields (type, attendees, topics, materials, samples, sentiment,
   outcomes, follow-ups) to prevent the LLM from writing to protected fields (id, hcp_id,
   created_at, rep_id).
3. Applies the patch, bumps `updated_at`, commits, and returns the full updated record so the
   rep sees a clean confirmation of exactly what changed — this supports corrections like
   "actually add Dr. Sharma to the advisory board follow-up" or "change sentiment to neutral."

## 4. Data Model (`backend/app/models.py`)
- `hcps` — id, name, specialty, institution
- `interactions` — hcp_id (FK), type, date, attendees[], topics_discussed, materials_shared[],
  samples_distributed[], sentiment (+confidence), outcomes, follow_up_actions, source
  (form/chat/voice), raw_voice_note, timestamps
- `chat_messages` — session_id, role, content — lets the agent resume a multi-turn slot-filling
  conversation per chat session

## 5. Running Locally

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY and DATABASE_URL
# create the Postgres DB first, e.g.: createdb hcp_crm
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

The frontend expects the API at `http://localhost:8000` (override with `VITE_API_BASE_URL`).

## 6. Tech Stack Recap
React 18 + Redux Toolkit · FastAPI · LangGraph · Groq (`gemma2-9b-it`, fallback
`llama-3.3-70b-versatile`) · PostgreSQL via SQLAlchemy · Google Inter font.

## 7. Known Scaffold Limitations
This is an interview-scoped prototype, not production code: no auth/rep identity layer yet
(`rep_id` is a stub column), no automated tests, and the voice-note "Summarize" button on the
form is wired to call the same `log_interaction` tool as chat but doesn't yet include actual
speech-to-text — it assumes a transcript is already available.
