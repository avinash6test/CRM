"""Thin wrapper around Groq-hosted models used by the LangGraph agent.

Primary model: gemma2-9b-it (fast, cheap — used for the bulk of turn-by-turn
slot filling, entity extraction and summarization).
Fallback model: llama-3.3-70b-versatile (used when gemma2-9b-it's output
fails schema validation twice in a row, e.g. malformed JSON on a complex
multi-topic note — 70B is more reliable at strict structured output).
"""
from langchain_groq import ChatGroq

from ..config import settings


def get_llm(model: str | None = None, temperature: float = 0.1):
    return ChatGroq(
        groq_api_key=settings.groq_api_key,
        model=model or settings.groq_model,
        temperature=temperature,
    )


def get_fallback_llm(temperature: float = 0.1):
    return get_llm(model=settings.groq_fallback_model, temperature=temperature)
