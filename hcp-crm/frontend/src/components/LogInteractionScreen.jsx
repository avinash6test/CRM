import React from 'react'
import InteractionForm from './InteractionForm.jsx'
import ChatAssistant from './ChatAssistant.jsx'

export default function LogInteractionScreen() {
  return (
    <div className="screen">
      <h1 className="screen-title">Log HCP Interaction</h1>
      <div className="screen-columns">
        <InteractionForm />
        <ChatAssistant />
      </div>
    </div>
  )
}
