"""LangGraph tool definitions for the HCP Interaction Agent.

Each tool is a plain Python function wrapped with @tool. Tools are built
per-request via `build_tools(db)` so they close over a live SQLAlchemy
session without needing a global.

Five tools (spec requires >=5, and mandates log_interaction + edit_interaction):
  1. search_hcp            - resolve an HCP name/context to a canonical HCP record
  2. log_interaction        - create a new interaction record from structured or freeform input
  3. edit_interaction       - patch fields on an existing interaction
  4. analyze_sentiment      - classify HCP sentiment from free text (used by log_interaction,
                              also callable standalone e.g. to re-score after a correction)
  5. suggest_follow_ups     - generate next-best-action recommendations for a rep
"""
import json
from datetime import datetime
from typing import List, Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from .. import models
from .llm import get_llm, get_fallback_llm


ENTITY_EXTRACTION_PROMPT = """You are a pharma CRM assistant. Extract structured fields from a
field rep's freeform note about a visit with a healthcare professional (HCP).

Return ONLY valid JSON with these keys (use null / [] when unknown, never invent facts):
{{
  "hcp_name": string|null,
  "interaction_type": one of ["Meeting","Call","Email","Conference","Virtual Meeting"],
  "attendees": string[],
  "topics_discussed": string,
  "materials_shared": string[],
  "samples_distributed": string[],
  "outcomes": string|null,
  "follow_up_actions": string|null
}}

Note:
\"\"\"{note}\"\"\"
"""

SENTIMENT_PROMPT = """Classify the healthcare professional's (HCP) sentiment expressed or implied
in this field rep note as exactly one of: positive, neutral, negative.
Return ONLY JSON: {{"sentiment": "...", "confidence": 0.0}}

Note:
\"\"\"{note}\"\"\"
"""

FOLLOWUP_PROMPT = """You are a pharma sales enablement assistant. Given the interaction summary
below, suggest 2-4 concrete, specific follow-up actions a field rep should take
(e.g. scheduling, sending specific literature, adding to advisory boards, sample replenishment).
Return ONLY a JSON array of short strings.

Interaction summary:
\"\"\"{summary}\"\"\"
"""


def _safe_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[-1] if "\n" in text else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    return {}


def build_tools(db: Session):

    @tool("search_hcp")
    def search_hcp(name: str) -> str:
        """Search for an HCP (Healthcare Professional) record by name (fuzzy, case-insensitive).
        Returns JSON with the best match's id, name, specialty, institution, or an empty
        result if none found. Use this before log_interaction if you only have a name string."""
        match = (
            db.query(models.HCP)
            .filter(models.HCP.name.ilike(f"%{name}%"))
            .first()
        )
        if not match:
            return json.dumps({"found": False})
        return json.dumps({
            "found": True,
            "id": match.id,
            "name": match.name,
            "specialty": match.specialty,
            "institution": match.institution,
        })

    @tool("analyze_sentiment")
    def analyze_sentiment(note: str) -> str:
        """Infer the HCP's sentiment (positive/neutral/negative) toward the product/rep from a
        freeform interaction note. Returns JSON {sentiment, confidence}."""
        llm = get_llm(temperature=0)
        resp = llm.invoke(SENTIMENT_PROMPT.format(note=note))
        parsed = _safe_json(resp.content)
        if "sentiment" not in parsed:
            resp = get_fallback_llm(temperature=0).invoke(SENTIMENT_PROMPT.format(note=note))
            parsed = _safe_json(resp.content)
        parsed.setdefault("sentiment", "neutral")
        parsed.setdefault("confidence", 0.5)
        return json.dumps(parsed)

    @tool("log_interaction")
    def log_interaction(hcp_name: str, note: str, source: str = "chat") -> str:
        """Create a new logged interaction from a freeform rep note (voice-note transcript or
        chat message). Extracts entities (attendees, topics, materials, samples, outcomes,
        follow-ups) and sentiment via the LLM, resolves the HCP, and persists an Interaction row.
        Returns JSON with the created interaction's id and extracted fields for confirmation."""
        llm = get_llm(temperature=0.1)
        resp = llm.invoke(ENTITY_EXTRACTION_PROMPT.format(note=note))
        extracted = _safe_json(resp.content)
        if not extracted:
            resp = get_fallback_llm(temperature=0.1).invoke(ENTITY_EXTRACTION_PROMPT.format(note=note))
            extracted = _safe_json(resp.content)

        hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            hcp = models.HCP(name=hcp_name)
            db.add(hcp)
            db.flush()

        sentiment_raw = json.loads(analyze_sentiment.invoke({"note": note}))

        interaction = models.Interaction(
            hcp_id=hcp.id,
            interaction_type=extracted.get("interaction_type") or "Meeting",
            date=datetime.utcnow(),
            attendees=extracted.get("attendees") or [],
            topics_discussed=extracted.get("topics_discussed"),
            materials_shared=extracted.get("materials_shared") or [],
            samples_distributed=extracted.get("samples_distributed") or [],
            sentiment=sentiment_raw.get("sentiment", "neutral"),
            sentiment_confidence=sentiment_raw.get("confidence", 0.5),
            outcomes=extracted.get("outcomes"),
            follow_up_actions=extracted.get("follow_up_actions"),
            source=source,
            raw_voice_note=note,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "id": interaction.id,
            "hcp_name": hcp.name,
            "interaction_type": interaction.interaction_type,
            "attendees": interaction.attendees,
            "topics_discussed": interaction.topics_discussed,
            "materials_shared": interaction.materials_shared,
            "samples_distributed": interaction.samples_distributed,
            "sentiment": interaction.sentiment,
            "outcomes": interaction.outcomes,
            "follow_up_actions": interaction.follow_up_actions,
        })

    @tool("edit_interaction")
    def edit_interaction(interaction_id: str, updates: str) -> str:
        """Modify fields on an already-logged interaction. `updates` is a JSON string with any
        subset of: interaction_type, attendees, topics_discussed, materials_shared,
        samples_distributed, sentiment, outcomes, follow_up_actions. Use this when a rep
        corrects something ('actually it was neutral not positive', 'add Dr. Lee to attendees').
        Returns the updated record as JSON."""
        interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        try:
            patch = json.loads(updates) if isinstance(updates, str) else updates
        except json.JSONDecodeError:
            return json.dumps({"error": "updates must be valid JSON"})

        allowed = {
            "interaction_type", "attendees", "topics_discussed", "materials_shared",
            "samples_distributed", "sentiment", "outcomes", "follow_up_actions",
        }
        for key, value in patch.items():
            if key in allowed:
                setattr(interaction, key, value)
        interaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "id": interaction.id,
            "interaction_type": interaction.interaction_type,
            "attendees": interaction.attendees,
            "topics_discussed": interaction.topics_discussed,
            "materials_shared": interaction.materials_shared,
            "samples_distributed": interaction.samples_distributed,
            "sentiment": interaction.sentiment,
            "outcomes": interaction.outcomes,
            "follow_up_actions": interaction.follow_up_actions,
        })

    @tool("suggest_follow_ups")
    def suggest_follow_ups(interaction_summary: str) -> str:
        """Given a summary of an interaction, suggest 2-4 concrete next-best-action follow-ups
        (e.g. schedule a follow-up meeting, send specific literature, add to an advisory board).
        Returns a JSON array of strings."""
        llm = get_llm(temperature=0.3)
        resp = llm.invoke(FOLLOWUP_PROMPT.format(summary=interaction_summary))
        parsed = resp.content.strip()
        try:
            suggestions = json.loads(parsed)
            if isinstance(suggestions, list):
                return json.dumps(suggestions)
        except json.JSONDecodeError:
            pass
        # fallback: split lines
        lines = [l.strip("-• ").strip() for l in parsed.splitlines() if l.strip()]
        return json.dumps(lines[:4])

    return [search_hcp, log_interaction, edit_interaction, analyze_sentiment, suggest_follow_ups]
