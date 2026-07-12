import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api/client";
import { addTraceEvent, resetTrace } from "./agentTraceSlice";

let sessionCounter = 0;
export const newSessionId = () => `session-${Date.now()}-${sessionCounter++}`;

// Thunk that streams SSE events from /api/chat/stream, dispatching each
// node event into the agentTrace slice as it arrives (drives the live panel).
export const sendMessageStreaming = createAsyncThunk(
  "chat/sendStreaming",
  async ({ sessionId, hcpId, message }, { dispatch }) => {
    dispatch(resetTrace());
    dispatch(chatSlice.actions.addUserMessage(message));

    const res = await api.chatStream({ session_id: sessionId, hcp_id: hcpId, message });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finalReply = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop();
      for (const chunk of chunks) {
        const line = chunk.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        const data = JSON.parse(line.replace("data: ", ""));
        dispatch(addTraceEvent(data));
        if (data.type === "final_reply") finalReply = data.content;
      }
    }
    return finalReply;
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: { messages: [], status: "idle" },
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({ role: "user", content: action.payload });
    },
    resetChat(state) {
      state.messages = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessageStreaming.pending, (state) => {
        state.status = "loading";
      })
      .addCase(sendMessageStreaming.fulfilled, (state, action) => {
        state.status = "succeeded";
        if (action.payload) state.messages.push({ role: "assistant", content: action.payload });
      })
      .addCase(sendMessageStreaming.rejected, (state) => {
        state.status = "failed";
        state.messages.push({ role: "assistant", content: "Sorry, something went wrong reaching the agent." });
      });
  },
});

export const { addUserMessage, resetChat } = chatSlice.actions;
export default chatSlice.reducer;
