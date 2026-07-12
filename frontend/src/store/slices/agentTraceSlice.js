import { createSlice } from "@reduxjs/toolkit";

const agentTraceSlice = createSlice({
  name: "agentTrace",
  initialState: { events: [] },
  reducers: {
    addTraceEvent(state, action) {
      state.events.push({ ...action.payload, ts: Date.now() });
    },
    resetTrace(state) {
      state.events = [];
    },
  },
});

export const { addTraceEvent, resetTrace } = agentTraceSlice.actions;
export default agentTraceSlice.reducer;
