import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchInteractions } from "../store/slices/interactionsSlice";
import StructuredForm from "./StructuredForm.jsx";
import ChatInterface from "./ChatInterface.jsx";
import AgentTracePanel from "./AgentTracePanel.jsx";
import InteractionHistory from "./InteractionHistory.jsx";

export default function LogInteractionScreen({ hcpId }) {
  const dispatch = useDispatch();
  const [mode, setMode] = useState("form"); // "form" | "chat"
  const draft = useSelector((s) => s.draft);

  useEffect(() => {
    dispatch(fetchInteractions(hcpId));
  }, [dispatch, hcpId]);

  return (
    <div className="log-screen">
      <section className="log-primary">
        <div className="mode-toggle" role="tablist" aria-label="Interaction logging mode">
          <button
            role="tab"
            aria-selected={mode === "form"}
            className={mode === "form" ? "active" : ""}
            onClick={() => setMode("form")}
          >
            📋 Structured Form
          </button>
          <button
            role="tab"
            aria-selected={mode === "chat"}
            className={mode === "chat" ? "active" : ""}
            onClick={() => setMode("chat")}
          >
            💬 Conversational
          </button>
          <span className={`sync-pill sync-${draft.syncStatus}`}>
            {draft.syncStatus === "synced" && "All changes saved"}
            {draft.syncStatus === "pending" && "Saving draft…"}
            {draft.syncStatus === "offline" && "Offline — draft kept locally"}
          </span>
        </div>

        {mode === "form" ? <StructuredForm hcpId={hcpId} /> : <ChatInterface hcpId={hcpId} />}
      </section>

      <aside className="log-sidebar">
        <AgentTracePanel />
        <InteractionHistory hcpId={hcpId} />
      </aside>
    </div>
  );
}
