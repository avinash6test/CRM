from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class InteractionBase(BaseModel):
    hcp_id: str
    interaction_type: str = "Meeting"
    date: Optional[datetime] = None
    attendees: List[str] = []
    topics_discussed: Optional[str] = None
    materials_shared: List[str] = []
    samples_distributed: List[str] = []
    sentiment: str = "neutral"
    sentiment_confidence: Optional[float] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    source: str = "form"
    raw_voice_note: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    date: Optional[datetime] = None
    attendees: Optional[List[str]] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[List[str]] = None
    samples_distributed: Optional[List[str]] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionOut(InteractionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None


class HCPOut(HCPBase):
    id: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    # populated when the agent has enough info to show/confirm a draft interaction
    draft_interaction: Optional[dict] = None
    suggested_follow_ups: List[str] = []
    tool_calls: List[str] = []
