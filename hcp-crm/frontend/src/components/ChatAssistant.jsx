import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { addUserMessage, sendMessage } from '../store/chatSlice'
import { applyAgentDraft, setSuggestedFollowUps } from '../store/interactionSlice'

export default function ChatAssistant() {
  const dispatch = useDispatch()
  const { messages, status } = useSelector((s) => s.chat)
  const [input, setInput] = useState('')

  async function handleSend() {
    const text = input.trim()
    if (!text) return
    dispatch(addUserMessage(text))
    setInput('')
    const action = await dispatch(sendMessage(text))
    if (sendMessage.fulfilled.match(action) && action.payload.draft_interaction) {
      dispatch(applyAgentDraft(action.payload.draft_interaction))
    }
  }

  return (
    <div className="panel chat-panel">
      <h2 className="panel-title">🤖 AI Assistant</h2>
      <div className="panel-subtitle">Log interaction via chat</div>

      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            {m.content}
          </div>
        ))}
        {status === 'loading' && <div className="chat-bubble assistant typing">Thinking…</div>}
      </div>

      <div className="chat-input-row">
        <input
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button className="primary-btn small" onClick={handleSend}>⚠ Log</button>
      </div>
    </div>
  )
}
