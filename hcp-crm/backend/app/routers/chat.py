import json

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.orm import Session

from .. import models, schemas
from ..agent.graph import build_graph
from ..database import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _history_to_messages(rows: list[models.ChatMessage]):
    messages = []
    for row in rows:
        if row.role == "user":
            messages.append(HumanMessage(content=row.content))
        elif row.role == "assistant":
            messages.append(AIMessage(content=row.content))
    return messages


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    history_rows = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == payload.session_id)
        .order_by(models.ChatMessage.created_at)
        .all()
    )
    graph = build_graph(db)
    messages = _history_to_messages(history_rows) + [HumanMessage(content=payload.message)]

    result = graph.invoke({"messages": messages})
    tool_calls_used = []
    draft_interaction = None
    for msg in result["messages"]:
        if getattr(msg, "tool_calls", None):
            tool_calls_used.extend(tc["name"] for tc in msg.tool_calls)
        # capture the last log_interaction/edit_interaction tool result as the "draft"
        if getattr(msg, "name", None) in ("log_interaction", "edit_interaction"):
            try:
                draft_interaction = json.loads(msg.content)
            except (json.JSONDecodeError, TypeError):
                pass

    final_reply = result["messages"][-1].content

    db.add(models.ChatMessage(session_id=payload.session_id, role="user", content=payload.message))
    db.add(models.ChatMessage(session_id=payload.session_id, role="assistant", content=final_reply))
    db.commit()

    return schemas.ChatResponse(
        session_id=payload.session_id,
        reply=final_reply,
        draft_interaction=draft_interaction,
        suggested_follow_ups=[],
        tool_calls=tool_calls_used,
    )
