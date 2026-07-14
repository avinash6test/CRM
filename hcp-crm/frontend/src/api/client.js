import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

export const searchHcps = (query) => api.get('/api/hcps', { params: { search: query } })
export const createInteraction = (payload) => api.post('/api/interactions', payload)
export const updateInteraction = (id, payload) => api.patch(`/api/interactions/${id}`, payload)
export const sendChatMessage = (sessionId, message) =>
  api.post('/api/chat', { session_id: sessionId, message })
