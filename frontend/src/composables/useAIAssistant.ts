import { computed, shallowRef } from 'vue'
import { aiApi } from '@/services/ai'
import { knowledgeApi } from '@/services/knowledge'
import type { AIConversation, AIMessage, AskResponse, KnowledgeSpace } from '@/types'

export function useAIAssistant() {
  const conversations = shallowRef<AIConversation[]>([])
  const messages = shallowRef<AIMessage[]>([])
  const spaces = shallowRef<KnowledgeSpace[]>([])
  const activeConversationId = shallowRef<number | null>(null)
  const selectedSpaceId = shallowRef<number | null>(null)
  const loading = shallowRef(false)
  const latestAnswer = shallowRef<AskResponse | null>(null)
  const activeConversation = computed(
    () =>
      conversations.value.find((item) => item.id === activeConversationId.value) ?? null,
  )

  async function initialize() {
    ;[conversations.value, spaces.value] = await Promise.all([
      aiApi.conversations(),
      knowledgeApi.spaces(),
    ])
  }

  async function selectConversation(id: number) {
    activeConversationId.value = id
    messages.value = await aiApi.messages(id)
  }

  async function ask(question: string) {
    if (!question.trim()) return
    loading.value = true
    const userMessage: AIMessage = {
      id: -Date.now(),
      role: 'user',
      content: question,
      citations: [],
      confidence: null,
      model_name: null,
      created_at: new Date().toISOString(),
    }
    const assistantMessage: AIMessage = {
      id: userMessage.id - 1,
      role: 'assistant',
      content: '',
      citations: [],
      confidence: null,
      model_name: null,
      created_at: new Date().toISOString(),
    }
    messages.value = [...messages.value, userMessage, assistantMessage]
    try {
      await aiApi.askStream(
        {
          question,
          conversation_id: activeConversationId.value,
          space_id: selectedSpaceId.value,
          limit: 3,
        },
        {
          meta(data) {
            activeConversationId.value = data.conversation_id
            userMessage.id = data.question_message_id
            assistantMessage.id = data.answer_message_id
            assistantMessage.citations = data.citations
            assistantMessage.model_name = data.model
            messages.value = [...messages.value]
          },
          delta(text) {
            assistantMessage.content += text
            messages.value = [...messages.value]
          },
          done(data) {
            assistantMessage.content = data.answer
            assistantMessage.citations = data.citations
            assistantMessage.confidence = data.confidence
            assistantMessage.model_name = data.model
            latestAnswer.value = {
              conversation_id: activeConversationId.value ?? 0,
              question_message_id: userMessage.id,
              answer_message_id: assistantMessage.id,
              answer: data.answer,
              confidence: data.confidence,
              model: data.model,
              citations: data.citations,
            }
            messages.value = [...messages.value]
          },
          error(message) {
            assistantMessage.content = message
            assistantMessage.confidence = 0
            messages.value = [...messages.value]
          },
        },
      )
      conversations.value = await aiApi.conversations()
    } finally {
      loading.value = false
    }
  }

  async function sendFeedback(messageId: number, rating: 'helpful' | 'unhelpful') {
    await aiApi.feedback(messageId, rating)
  }

  function newConversation() {
    activeConversationId.value = null
    messages.value = []
    latestAnswer.value = null
  }

  return {
    conversations,
    messages,
    spaces,
    activeConversationId,
    selectedSpaceId,
    activeConversation,
    loading,
    latestAnswer,
    initialize,
    selectConversation,
    ask,
    sendFeedback,
    newConversation,
  }
}
