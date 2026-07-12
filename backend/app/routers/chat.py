import ast
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.agent.graph import agent_executor

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory session store keyed by session_id -> list of LangChain messages.
# Fine for an assignment/demo; swap for Redis in production for multi-worker deployments.
_SESSIONS: dict[str, list] = {}


def _safe_parse_tool_content(content: str) -> dict | None:
    """Best-effort parse of a ToolMessage's content back into a dict. Tries
    JSON first (in case a future LangChain version serializes that way),
    then falls back to Python literal parsing (today's actual format)."""
    for parser in (json.loads, ast.literal_eval):
        try:
            result = parser(content)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError, SyntaxError):
            continue
    return None


def _persist_trace(db: Session, session_id: str, node_name: str, tool_name, input_snap, output_snap, duration_ms):
    log = models.AgentTraceLog(
        session_id=session_id,
        node_name=node_name,
        tool_name=tool_name,
        input_snapshot=input_snap,
        output_snapshot=output_snap,
        duration_ms=duration_ms,
    )
    db.add(log)
    db.commit()


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatMessage, db: Session = Depends(get_db)):
    """Non-streaming chat turn -- returns the reply plus the full node trace."""
    history = _SESSIONS.setdefault(payload.session_id, [])
    history.append(HumanMessage(content=payload.message))

    trace = []
    final_state = None
    t0 = time.time()

    for step in agent_executor.stream(
        {"messages": history, "session_id": payload.session_id, "hcp_id": payload.hcp_id,
         "active_interaction_id": None, "compliance_alert": None},
        stream_mode="values",
    ):
        final_state = step
        last_msg = step["messages"][-1]
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            for tc in last_msg.tool_calls:
                trace.append({"node": "agent", "type": "tool_call", "tool": tc["name"], "args": tc["args"]})
        elif isinstance(last_msg, ToolMessage):
            trace.append({"node": "tools", "type": "tool_result", "tool": last_msg.name, "content": last_msg.content[:500]})
        elif isinstance(last_msg, AIMessage):
            trace.append({"node": "agent", "type": "final_reply", "content": last_msg.content})

    duration_ms = (time.time() - t0) * 1000
    _persist_trace(db, payload.session_id, "graph_run", None, {"message": payload.message}, {"trace_len": len(trace)}, duration_ms)

    history[:] = final_state["messages"]
    reply = history[-1].content if history else ""

    interaction_out = None
    for t in trace:
        if t.get("type") == "tool_result" and t.get("tool") == "log_interaction":
            # ToolMessage.content is Python's str(dict) repr, not JSON (single
            # quotes, True/False/None) -- ast.literal_eval handles that safely,
            # including apostrophes inside AI-generated summaries, where a naive
            # '->" swap would corrupt the string and fail to parse.
            data = _safe_parse_tool_content(t["content"])
            if data and "interaction_id" in data:
                interaction_out = db.get(models.Interaction, data["interaction_id"])

    return schemas.ChatResponse(session_id=payload.session_id, reply=reply, trace=trace, interaction=interaction_out)


@router.post("/stream")
def chat_stream(payload: schemas.ChatMessage):
    """
    Server-Sent Events version of the same endpoint. Streams one JSON event
    per graph step so the frontend's Agent Reasoning Trace panel can light
    up node-by-node in real time instead of waiting for the whole turn.
    """
    history = _SESSIONS.setdefault(payload.session_id, [])
    history.append(HumanMessage(content=payload.message))

    def event_stream():
        for step in agent_executor.stream(
            {"messages": history, "session_id": payload.session_id, "hcp_id": payload.hcp_id,
             "active_interaction_id": None, "compliance_alert": None},
            stream_mode="values",
        ):
            last_msg = step["messages"][-1]
            event = None
            if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                event = {"node": "agent", "type": "tool_call",
                         "calls": [{"tool": tc["name"], "args": tc["args"]} for tc in last_msg.tool_calls]}
            elif isinstance(last_msg, ToolMessage):
                event = {"node": "tools", "type": "tool_result", "tool": last_msg.name, "content": last_msg.content[:500]}
            elif isinstance(last_msg, AIMessage):
                event = {"node": "agent", "type": "final_reply", "content": last_msg.content}
                history[:] = step["messages"]

            if event:
                yield f"data: {json.dumps(event)}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
