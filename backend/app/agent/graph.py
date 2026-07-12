"""
Builds the LangGraph StateGraph for the HCP Log Interaction agent.

Graph shape:

    START -> agent -> (conditional) -> tools -> agent -> ... -> END
                    -> (no tool call) -> END

`agent` is the Groq-backed LLM (gemma2-9b-it, tools bound). `tools` executes
whichever tool(s) the LLM asked for and feeds results back as ToolMessages.
This is the standard LangGraph ReAct pattern -- kept intentionally simple so
it's easy to defend in the video walkthrough, while still being a real
multi-tool agent instead of a single hard-coded prompt chain.
"""
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS
from app.config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are the AI co-pilot inside a pharmaceutical CRM's HCP
(Healthcare Professional) module. A field rep is describing an interaction
with a doctor, either through a structured form or free-form chat.

Your job:
1. When the rep describes a visit/call that isn't saved yet, call
   log_interaction with the hcp_id and their notes verbatim.
2. If they want to correct or add to something already logged, call
   edit_interaction.
3. Use analyze_sentiment, check_compliance, track_sample_drop,
   schedule_followup, and summarize_hcp_history proactively when relevant
   -- don't wait to be asked for compliance screening on sensitive notes.
4. Always confirm back to the rep in plain, brief language what you did.
5. Never fabricate an hcp_id -- ask for clarification if you don't have one.

Be concise. You're a working tool for a busy field rep, not a chatbot for
chit-chat.
"""


class _FallbackChatModel:
    """Small deterministic fallback so the demo can run locally without Groq."""

    def __init__(self):
        self.tools = ALL_TOOLS

    def bind_tools(self, tools):
        self.tools = tools
        return self

    def invoke(self, messages, state=None):
        user_text = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_text = msg.content or ""
                break

        lower = user_text.lower()
        tool_calls = []
        hcp_id = (state or {}).get("hcp_id") or "demo-hcp"

        if lower.startswith("give me a briefing") or "briefing" in lower or "history" in lower:
            tool_calls.append({
                "name": "summarize_hcp_history",
                "args": {"hcp_id": hcp_id, "limit": 5},
            })
            return AIMessage(content="Demo mode reply: I pulled a briefing from the HCP history.", tool_calls=tool_calls)

        products = []
        if "cardioflow" in lower:
            products.append("CardioFlow 10mg")
        if "metformin" in lower:
            products.append("Metformin")
        if "insulin" in lower:
            products.append("Insulin")

        tool_calls.append({
            "name": "log_interaction",
            "args": {
                "hcp_id": hcp_id,
                "raw_notes": user_text or "Demo interaction from local fallback mode.",
                "products_discussed": products,
            },
        })
        tool_calls.append({
            "name": "analyze_sentiment",
            "args": {"text": user_text or "Demo interaction from local fallback mode."},
        })
        tool_calls.append({
            "name": "check_compliance",
            "args": {"interaction_id": "demo-interaction"},
        })

        if "sample" in lower or "samples" in lower:
            tool_calls.append({
                "name": "track_sample_drop",
                "args": {"interaction_id": "demo-interaction", "samples": {"CardioFlow 10mg": 20}},
            })
        if "follow up" in lower or "follow-up" in lower or "2 weeks" in lower:
            tool_calls.append({
                "name": "schedule_followup",
                "args": {"interaction_id": "demo-interaction", "days_from_now": 14, "note": "Follow-up requested by HCP"},
            })

        return AIMessage(content="Demo mode reply: I logged the interaction and triggered the supporting tools.", tool_calls=tool_calls)


def build_agent_graph():
    if settings.groq_api_key:
        llm = ChatGroq(
            model=settings.primary_model,
            api_key=settings.groq_api_key,
            temperature=0.2,
        ).bind_tools(ALL_TOOLS)
    else:
        llm = _FallbackChatModel().bind_tools(ALL_TOOLS)

    def call_model(state: AgentState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm.invoke(messages, state=state) if not settings.groq_api_key else llm.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled once, reused across requests.
agent_executor = build_agent_graph()
