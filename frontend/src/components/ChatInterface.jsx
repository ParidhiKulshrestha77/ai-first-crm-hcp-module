import React, { useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendMessageStreaming, newSessionId, resetChat } from "../store/slices/chatSlice";
import { fetchInteractions } from "../store/slices/interactionsSlice";
import VoiceInput from "./VoiceInput.jsx";

export default function ChatInterface({ hcpId }) {
  const dispatch = useDispatch();
  const { messages, status } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const sessionId = useMemo(() => newSessionId(), [hcpId]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const message = input;
    setInput("");
    await dispatch(sendMessageStreaming({ sessionId, hcpId, message }));
    dispatch(fetchInteractions(hcpId)); // pick up anything the agent just logged
  };

  const quickPrompts = [
    {
      label: "Log a visit",
      text: "Just met Dr. Mehra, discussed CardioFlow 10mg, she was receptive but wants efficacy data for elderly patients. Left 20 samples. Follow up in 2 weeks.",
    },
    {
      label: "Get briefing",
      text: "Give me a briefing before I see Dr. Mehra again.",
    },
  ];

  return (
    <div className="chat-interface">
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Tell me about the visit in your own words, or try a quick demo prompt:</p>
            <div className="demo-prompt-row">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt.label}
                  type="button"
                  className="demo-prompt-btn"
                  onClick={() => setInput(prompt.text)}
                >
                  {prompt.label}
                </button>
              ))}
            </div>
            <p className="chat-example">
              "Just met Dr. Mehra, discussed CardioFlow 10mg, she was receptive but wants
              efficacy data for elderly patients. Left 20 samples. Follow up in 2 weeks."
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            {m.content}
          </div>
        ))}
        {status === "loading" && <div className="chat-bubble assistant typing">Agent is working…</div>}
      </div>

      <div className="demo-helper">Demo mode uses a local fallback agent so you can record the flow instantly.</div>
      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          type="text"
          placeholder="Describe the interaction, or ask the agent to edit/summarize…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <VoiceInput onTranscript={(t) => setInput((prev) => `${prev} ${t}`.trim())} />
        <button type="submit" disabled={status === "loading" || !input.trim()}>
          Send
        </button>
      </form>
      <button type="button" className="link-btn" onClick={() => dispatch(resetChat())}>
        Clear conversation
      </button>
    </div>
  );
}
