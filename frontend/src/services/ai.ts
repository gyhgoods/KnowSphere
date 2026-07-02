import { http } from './http'
import { tokenStorage } from './http'
import type { AIConversation, AIMessage, AskResponse, Citation, GraphResponse } from '@/types'

type AskPayload = {
  question: string
  conversation_id?: number | null
  space_id?: number | null
  limit?: number
}

export type AskStreamMeta = {
  conversation_id: number
  question_message_id: number
  answer_message_id: number
  model: string
  citations: Citation[]
}

export type AskStreamDone = {
  answer: string
  confidence: number
  model: string
  citations: Citation[]
}

export const aiApi = {
  async ask(payload: AskPayload) {
    return (await http.post<AskResponse>('/ai/ask', payload)).data
  },
  async askStream(
    payload: AskPayload,
    handlers: {
      meta?: (data: AskStreamMeta) => void
      delta?: (text: string) => void
      done?: (data: AskStreamDone) => void
      error?: (message: string) => void
    },
  ) {
    const response = await fetch(`${http.defaults.baseURL}/ai/ask/stream`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${tokenStorage.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
    if (!response.ok || !response.body) {
      throw new Error(`AI stream request failed: ${response.status}`)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.trim()) continue
        const event = JSON.parse(line) as { event: string; data: Record<string, unknown> }
        if (event.event === 'meta') handlers.meta?.(event.data as AskStreamMeta)
        if (event.event === 'delta') handlers.delta?.(String(event.data.text ?? ''))
        if (event.event === 'done') handlers.done?.(event.data as AskStreamDone)
        if (event.event === 'error') handlers.error?.(String(event.data.message ?? 'AI request failed'))
      }
    }
  },
  async conversations() {
    return (await http.get<AIConversation[]>('/ai/conversations')).data
  },
  async messages(conversationId: number) {
    return (await http.get<AIMessage[]>(`/ai/conversations/${conversationId}/messages`)).data
  },
  async feedback(messageId: number, rating: 'helpful' | 'unhelpful', comment?: string) {
    return (
      await http.post(`/ai/messages/${messageId}/feedback`, {
        rating,
        comment: comment || null,
      })
    ).data
  },
}

export const graphApi = {
  async graph(params: { space_id?: number | null; relation_filter?: 'all' | 'strong' }) {
    return (await http.get<GraphResponse>('/graph', { params })).data
  },
  async extract(documentId: number) {
    return (await http.post('/graph/extract', { document_id: documentId })).data
  },
}
