import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { v4 as uuidv4 } from 'uuid'
import { sendChatMessage } from '../api/client'

const initialState = {
  sessionId: uuidv4(),
  messages: [
    {
      role: 'assistant',
      content:
        'Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.',
    },
  ],
  status: 'idle',
  lastDraftInteraction: null,
}

export const sendMessage = createAsyncThunk(
  'chat/send',
  async (message, { getState }) => {
    const { sessionId } = getState().chat
    const { data } = await sendChatMessage(sessionId, message)
    return data
  }
)

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({ role: 'user', content: action.payload })
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = 'idle'
        state.messages.push({ role: 'assistant', content: action.payload.reply })
        state.lastDraftInteraction = action.payload.draft_interaction || null
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = 'error'
        state.messages.push({
          role: 'assistant',
          content: "Sorry, I couldn't reach the assistant service. Please try again.",
        })
      })
  },
})

export const { addUserMessage } = chatSlice.actions
export default chatSlice.reducer
