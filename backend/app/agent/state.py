from typing import Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state threaded through every node of the LangGraph graph.
    `messages` accumulates via LangGraph's add_messages reducer so the
    agent keeps full conversational context across tool calls.
    """
    messages: Annotated[list, add_messages]
    session_id: str
    hcp_id: Optional[str]
    active_interaction_id: Optional[str]
    compliance_alert: Optional[str]
