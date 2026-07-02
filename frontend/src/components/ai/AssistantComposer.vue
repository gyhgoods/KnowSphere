<script setup lang="ts">
import { shallowRef } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import { useI18n } from '@/composables/useI18n'

defineProps<{ loading: boolean }>()
const emit = defineEmits<{ ask: [question: string] }>()
const { t } = useI18n()
const question = shallowRef('')

function submit() {
  const value = question.value.trim()
  if (!value) return
  emit('ask', value)
  question.value = ''
}
</script>

<template>
  <section class="composer">
    <ElInput
      v-model="question"
      type="textarea"
      :rows="3"
      :placeholder="t('askPlaceholder')"
      @keydown.ctrl.enter.prevent="submit"
    />
    <div class="composer-footer">
      <span>{{ t('askHint') }}</span>
      <ElButton type="primary" :icon="Promotion" :loading="loading" @click="submit">
        {{ t('askAI') }}
      </ElButton>
    </div>
  </section>
</template>

<style scoped>
.composer {
  padding: 16px;
  border: 1px solid var(--ks-border);
  border-radius: 14px;
  background: #ffffff;
}

.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  color: var(--ks-muted);
  font-size: 12px;
}
</style>
