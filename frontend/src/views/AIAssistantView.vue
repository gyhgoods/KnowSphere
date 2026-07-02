<script setup lang="ts">
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AssistantComposer from '@/components/ai/AssistantComposer.vue'
import ConversationMessages from '@/components/ai/ConversationMessages.vue'
import { useAIAssistant } from '@/composables/useAIAssistant'
import { useI18n } from '@/composables/useI18n'

const assistant = useAIAssistant()
const { t } = useI18n()

onMounted(assistant.initialize)

async function feedback(messageId: number, rating: 'helpful' | 'unhelpful') {
  await assistant.sendFeedback(messageId, rating)
  ElMessage.success(t('feedbackSaved'))
}
</script>

<template>
  <main class="assistant-view">
    <aside class="conversation-panel">
      <header>
        <h3>{{ t('aiAssistant') }}</h3>
        <ElButton size="small" @click="assistant.newConversation">{{ t('newChat') }}</ElButton>
      </header>
      <ElSelect
        v-model="assistant.selectedSpaceId.value"
        clearable
        :placeholder="t('allSpaces')"
        class="space-filter"
      >
        <ElOption
          v-for="space in assistant.spaces.value"
          :key="space.id"
          :label="space.name"
          :value="space.id"
        />
      </ElSelect>
      <button
        v-for="conversation in assistant.conversations.value"
        :key="conversation.id"
        class="conversation-item"
        :class="{ active: conversation.id === assistant.activeConversationId.value }"
        @click="assistant.selectConversation(conversation.id)"
      >
        {{ conversation.title }}
      </button>
    </aside>
    <section class="chat-panel">
      <header class="chat-header">
        <p>GROUNDED ASSISTANT</p>
        <h2>{{ assistant.activeConversation.value?.title ?? t('aiAssistant') }}</h2>
        <span>{{ t('assistantDescription') }}</span>
      </header>
      <ConversationMessages
        :messages="assistant.messages.value"
        :loading="assistant.loading.value"
        @feedback="feedback"
      />
      <AssistantComposer :loading="assistant.loading.value" @ask="assistant.ask" />
    </section>
  </main>
</template>

<style scoped>
.assistant-view {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 20px;
}

.conversation-panel,
.chat-panel {
  border: 1px solid var(--ks-border);
  border-radius: 14px;
  background: #f8fbf9;
}

.conversation-panel {
  padding: 16px;
}

.conversation-panel header,
.chat-header {
  margin-bottom: 16px;
}

.conversation-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.conversation-panel h3,
.chat-header h2 {
  margin: 0;
}

.space-filter {
  width: 100%;
  margin-bottom: 14px;
}

.conversation-item {
  width: 100%;
  margin-bottom: 8px;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 10px;
  color: #314a40;
  background: #ffffff;
  text-align: left;
  cursor: pointer;
}

.conversation-item.active {
  border-color: var(--ks-primary);
  color: var(--ks-primary);
  font-weight: 700;
}

.chat-panel {
  padding: 20px;
}

.chat-header p {
  margin: 0 0 7px;
  color: var(--ks-primary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.chat-header span {
  color: var(--ks-muted);
}

@media (max-width: 900px) {
  .assistant-view {
    grid-template-columns: 1fr;
  }
}
</style>
