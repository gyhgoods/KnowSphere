<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from '@/composables/useI18n'
import { knowledgeApi } from '@/services/knowledge'
import type { DocumentVersion, KnowledgeDocument } from '@/types'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{ document: KnowledgeDocument | null }>()
const emit = defineEmits<{ restored: [] }>()
const versions = shallowRef<DocumentVersion[]>([])
const loading = shallowRef(false)
const { t, locale } = useI18n()

async function load() {
  if (!props.document) return
  loading.value = true
  try {
    versions.value = await knowledgeApi.versions(props.document.id)
  } finally {
    loading.value = false
  }
}

watch(
  () => [open.value, props.document?.id] as const,
  ([isOpen]) => {
    if (isOpen) void load()
  },
)

async function restore(version: DocumentVersion) {
  if (!props.document) return
  await knowledgeApi.restoreVersion(props.document.id, version.id)
  ElMessage.success(t('restoredVersion', { version: version.version_no }))
  open.value = false
  emit('restored')
}
</script>

<template>
  <ElDialog v-model="open" :title="t('historyVersions')" width="720px">
    <ElTimeline v-loading="loading">
      <ElTimelineItem
        v-for="version in versions"
        :key="version.id"
        :timestamp="new Date(version.created_at).toLocaleString(locale === 'zh' ? 'zh-CN' : 'en-US')"
        placement="top"
      >
        <div class="version-card">
          <div>
            <strong>v{{ version.version_no }} · {{ version.title }}</strong>
            <p>{{ version.content.slice(0, 140) || t('emptyContent') }}</p>
          </div>
          <ElButton
            v-if="version.version_no !== document?.version_no"
            size="small"
            @click="restore(version)"
          >
            {{ t('restore') }}
          </ElButton>
        </div>
      </ElTimelineItem>
    </ElTimeline>
    <ElEmpty v-if="!loading && !versions.length" :description="t('noVersions')" />
  </ElDialog>
</template>

<style scoped>
.version-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 14px;
  border: 1px solid var(--ks-border);
  border-radius: 10px;
  background: #fbfcfb;
}

.version-card p {
  margin: 8px 0 0;
  color: #788981;
  line-height: 1.5;
}
</style>
