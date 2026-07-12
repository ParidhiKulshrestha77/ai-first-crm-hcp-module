import { configureStore } from "@reduxjs/toolkit";
import interactionsReducer from "./slices/interactionsSlice";
import chatReducer from "./slices/chatSlice";
import hcpReducer from "./slices/hcpSlice";
import agentTraceReducer from "./slices/agentTraceSlice";
import draftReducer from "./slices/draftSlice";

export const store = configureStore({
  reducer: {
    interactions: interactionsReducer,
    chat: chatReducer,
    hcps: hcpReducer,
    agentTrace: agentTraceReducer,
    draft: draftReducer,
  },
});
