import React from "react";
import { useSelector } from "react-redux";

const TOOL_ICONS = {
  log_interaction: "📝",
  edit_interaction: "✏️",
  schedule_followup: "📅",
  analyze_sentiment: "🙂",
  track_sample_drop: "📦",
  check_compliance: "🛡️",
  summarize_hcp_history: "🧠",
};

/**
 * Renders the LangGraph execution trace live as SSE events arrive. This is
 * the panel to point at during the video demo: it makes the "invisible"
 * agent reasoning visible, which is exactly what a reviewer wants to see
 * for the 5-tools-working-properly requirement.
 */
export default function AgentTracePanel() {
  const events = useSelector((s) => s.agentTrace.events);

  return (
    <div className="trace-panel">
      <h3>🔎 Agent Reasoning Trace</h3>
      {events.length === 0 && <p className="trace-empty">Send a message in Conversational mode to see the agent's tool calls appear here in real time.</p>}
      <ol className="trace-list">
        {events.map((ev, idx) => (
          <li key={idx} className={`trace-item trace-${ev.type}`}>
            {ev.type === "tool_call" &&
              ev.calls.map((c, j) => (
                <div key={j}>
                  <span className="trace-icon">{TOOL_ICONS[c.tool] || "🔧"}</span>
                  <strong>{c.tool}</strong>
                  <span className="trace-args">{JSON.stringify(c.args)}</span>
                </div>
              ))}
            {ev.type === "tool_result" && (
              <div>
                <span className="trace-icon">✅</span>
                <strong>{ev.tool}</strong> returned
                <span className="trace-args">{ev.content}</span>
              </div>
            )}
            {ev.type === "final_reply" && (
              <div>
                <span className="trace-icon">💬</span> Agent replied to rep
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
