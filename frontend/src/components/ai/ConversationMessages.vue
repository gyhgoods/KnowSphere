<script setup lang="ts">
import { Check, Close } from '@element-plus/icons-vue'
import { useI18n } from '@/composables/useI18n'
import type { AIMessage, Citation } from '@/types'

defineProps<{ messages: readonly AIMessage[]; loading: boolean }>()
const emit = defineEmits<{ feedback: [messageId: number, rating: 'helpful' | 'unhelpful'] }>()
const { t } = useI18n()

function imageCitations(message: AIMessage) {
  return message.citations.filter((citation) => citation.image_url)
}

function citationLink(citation: Citation) {
  return {
    path: '/knowledge',
    query: { document_id: citation.document_id },
  }
}

function contentParts(message: AIMessage) {
  const parts: Array<{ type: 'text'; text: string } | { type: 'citation'; text: string; citation: Citation }> = []
  const citationMap = new Map(message.citations.map((citation) => [citation.index, citation]))
  const pattern = /\[(\d+)]/g
  let cursor = 0
  for (const match of message.content.matchAll(pattern)) {
    const start = match.index ?? 0
    const citation = citationMap.get(Number(match[1]))
    if (start > cursor) parts.push({ type: 'text', text: message.content.slice(cursor, start) })
    if (citation) {
      parts.push({ type: 'citation', text: match[0], citation })
    } else {
      parts.push({ type: 'text', text: match[0] })
    }
    cursor = start + match[0].length
  }
  if (cursor < message.content.length) {
    parts.push({ type: 'text', text: message.content.slice(cursor) })
  }
  return parts
}
</script>

<template>
  <section class="messages">
    <ElEmpty v-if="!messages.length && !loading" :description="t('emptyAssistant')" />
    <article
      v-for="message in messages"
      :key="message.id"
      class="message"
      :class="`message-${message.role}`"
    >
      <strong>{{ message.role === 'user' ? t('you') : t('assistant') }}</strong>
      <p class="message-content">
        <template v-for="(part, index) in contentParts(message)" :key="index">
          <RouterLink
            v-if="part.type === 'citation'"
            class="inline-citation"
            :to="citationLink(part.citation)"
          >
            {{ part.text }}
          </RouterLink>
          <span v-else>{{ part.text }}</span>
        </template>
      </p>
      <div v-if="message.citations.length" class="citations">
        <RouterLink
          v-for="citation in message.citations"
          :key="citation.index"
          class="citation-link"
          :to="citationLink(citation)"
        >
          <ElTag effect="plain" type="success">
            [{{ citation.index }}] {{ citation.document_title }}
            <template v-if="citation.source_name && citation.source_name !== citation.document_title">
              / {{ citation.source_name }}
            </template>
          </ElTag>
        </RouterLink>
      </div>
      <div v-if="imageCitations(message).length" class="citation-images">
        <RouterLink
          v-for="citation in imageCitations(message)"
          :key="`${citation.index}-${citation.image_url}`"
          class="citation-image"
          :to="citationLink(citation)"
        >
          <figure>
            <img :src="citation.image_url || ''" :alt="citation.image_name || citation.source_name" />
            <figcaption>
              [{{ citation.index }}] 来自文档：{{ citation.image_document_title || citation.document_title }}
              <span>图片：{{ citation.image_name || citation.source_name }}</span>
            </figcaption>
          </figure>
        </RouterLink>
      </div>
      <footer v-if="message.role === 'assistant'" class="message-footer">
        <span>{{ t('confidence') }} {{ Math.round((message.confidence ?? 0) * 100) }}%</span>
        <ElButton
          link
          type="success"
          :icon="Check"
          :disabled="message.id < 0"
          @click="emit('feedback', message.id, 'helpful')"
        >
          {{ t('helpful') }}
        </ElButton>
        <ElButton
          link
          type="danger"
          :icon="Close"
          :disabled="message.id < 0"
          @click="emit('feedback', message.id, 'unhelpful')"
        >
          {{ t('unhelpful') }}
        </ElButton>
      </footer>
    </article>
    <ElSkeleton v-if="loading" :rows="4" animated />
  </section>
</template>

<style scoped>
.messages {
  min-height: 420px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  max-width: 82%;
  padding: 16px;
  border: 1px solid var(--ks-border);
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgb(16 42 33 / 6%);
}

.message-user {
  align-self: flex-end;
  background: #e8f5f1;
}

.message strong {
  color: var(--ks-ink);
}

.message-content {
  margin: 10px 0;
  color: #334b41;
  line-height: 1.65;
  white-space: pre-line;
}

.inline-citation {
  color: var(--ks-primary);
  font-weight: 800;
  text-decoration: none;
}

.citations,
.message-footer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.citation-link {
  text-decoration: none;
}

.citation-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin: 12px 0;
}

.citation-image {
  overflow: hidden;
  border: 1px solid var(--ks-border);
  border-radius: 12px;
  background: #f8fbf9;
  color: inherit;
  text-decoration: none;
}

.citation-image figure {
  margin: 0;
}

.citation-image img {
  display: block;
  width: 100%;
  max-height: 220px;
  object-fit: contain;
  background: #ffffff;
}

.citation-image figcaption {
  padding: 8px 10px;
  color: var(--ks-muted);
  font-size: 12px;
}

.citation-image figcaption span {
  display: block;
  margin-top: 4px;
}

.message-footer {
  color: var(--ks-muted);
  font-size: 12px;
}
</style>
