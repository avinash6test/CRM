"""LangGraph StateGraph that powers the conversational side of the
'Log HCP Interaction' screen (the right-hand AI Assistant chat panel).

Flow:
  START -> agent (LLM decides whether to call a tool or reply) -> [tools?] -> agent -> END

The agent node binds the 5 tools from tools.py to the Groq model (gemma2-9b-it)
via tool-calling, and loops through a ToolNode until the model produces a
final natural-language reply (ReAct-style loop, capped to avoid runaway tool use).
"""
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .llm import get_llm
from .tools import build_tools

SYSTEM_PROMPT = """You are the AI Assistant embedded in a pharma CRM's "Log HCP Interaction"
screen. Field reps describe visits/calls with healthcare professionals (HCPs) in plain
language; your job is to turn that into a structured, saved interaction record and help
the rep manage it — using your tools, never by inventing data.

Rules:
- If the rep is describing a new visit, gather at minimum: HCP name and what was discussed.
  If missing, ask a short clarifying question before calling log_interaction.
- Use search_hcp first if you're unsure an HCP already exists in the system.
- Use log_interaction to persist a new note into a structured interaction record.
- Use edit_interaction when the rep corrects or adds to something already logged
  (you'll need the interaction id from a prior log_interaction/edit_interaction result).
- After logging, call suggest_follow_ups and present them as suggestions, not commitments.
- Keep replies concise and confirm what was captured in plain language.
"""


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_graph(db):
    tools = build_tools(db)
    llm = get_llm(temperature=0.1).bind_tools(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
