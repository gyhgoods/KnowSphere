<script setup lang="ts">
import { computed, onBeforeUnmount, shallowRef, watch } from 'vue'
import { Delete, Download, Refresh, UploadFilled, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useI18n } from '@/composables/useI18n'
import { knowledgeApi } from '@/services/knowledge'
import type { DocumentFile, FileParseResult, KnowledgeDocument } from '@/types'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{ document: KnowledgeDocument | null }>()
const files = shallowRef<DocumentFile[]>([])
const loading = shallowRef(false)
const uploadProgress = shallowRef(0)
const parseResult = shallowRef<FileParseResult | null>(null)
const parseDialogOpen = shallowRef(false)
const { t } = useI18n()
const title = computed(() => t('attachmentTitle', { title: props.document?.title ?? '' }))
let pollTimer: ReturnType<typeof setTimeout> | undefined

const parseLabels = computed<Record<DocumentFile['parse_status'], string>>(() => ({
  queued: t('parseQueued'),
  processing: t('parseProcessing'),
  completed: t('parseCompleted'),
  failed: t('parseFailed'),
  unsupported: t('parseUnsupported'),
}))

function clearPoll() {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = undefined
  }
}

function schedulePoll() {
  clearPoll()
  if (
    open.value &&
    files.value.some((file) => file.parse_status === 'queued' || file.parse_status === 'processing')
  ) {
    pollTimer = setTimeout(() => void load(), 3000)
  }
}

async function load() {
  if (!props.document) return
  loading.value = true
  try {
    files.value = await knowledgeApi.files(props.document.id)
  } finally {
    loading.value = false
    schedulePoll()
  }
}

watch(
  () => [open.value, props.document?.id] as const,
  ([isOpen]) => {
    if (isOpen) void load()
    else clearPoll()
  },
)

onBeforeUnmount(clearPoll)

async function upload(options: { file: File }) {
  if (!props.document) return
  uploadProgress.value = 0
  await knowledgeApi.uploadFile(props.document.id, options.file, (value) => {
    uploadProgress.value = value
  })
  ElMessage.success(t('attachmentUploaded'))
  await load()
}

async function access(file: DocumentFile, mode: 'preview' | 'download') {
  const result = await knowledgeApi.fileAccess(file.id, mode)
  window.open(result.url, '_blank', 'noopener,noreferrer')
}

async function retryParse(file: DocumentFile) {
  await knowledgeApi.retryFileParse(file.id)
  ElMessage.success(t('parseQueued'))
  await load()
}

async function showParsedContent(file: DocumentFile) {
  parseResult.value = await knowledgeApi.fileParse(file.id)
  parseDialogOpen.value = true
}

async function remove(file: DocumentFile) {
  await knowledgeApi.deleteFile(file.id)
  ElMessage.success(t('attachmentDeleted'))
  await load()
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function statusType(status: DocumentFile['parse_status']) {
  if (status === 'completed') return 'success'
  if (status === 'failed' || status === 'unsupported') return 'danger'
  if (status === 'processing') return 'warning'
  return 'info'
}
</script>

<template>
  <ElDrawer v-model="open" :title="title" size="min(620px, 92vw)">
    <ElUpload :show-file-list="false" :http-request="upload" drag>
      <ElIcon class="upload-icon"><UploadFilled /></ElIcon>
      <div>{{ t('uploadHint') }}</div>
      <template #tip>
        <div class="upload-tip">{{ t('uploadTip') }}</div>
      </template>
    </ElUpload>
    <ElProgress
      v-if="uploadProgress > 0 && uploadProgress < 100"
      class="progress"
      :percentage="uploadProgress"
    />

    <div v-loading="loading" class="file-list">
      <article v-for="file in files" :key="file.id" class="file-row">
        <div class="file-info">
          <strong>{{ file.file_name }}</strong>
          <small>{{ file.mime_type }} · {{ formatSize(file.file_size) }}</small>
          <div class="parse-state">
            <ElTag
              :type="statusType(file.parse_status)"
              size="small"
              :title="file.parse_error || parseLabels[file.parse_status]"
              :class="{ clickable: file.parse_status === 'completed' }"
              @click="file.parse_status === 'completed' && showParsedContent(file)"
            >
              {{ parseLabels[file.parse_status] }}
              <template v-if="file.parse_status === 'completed'">
                · {{ file.parsed_text_length }}
              </template>
            </ElTag>
            <ElButton
              v-if="file.parse_status === 'failed' || file.parse_status === 'unsupported'"
              text
              size="small"
              :icon="Refresh"
              @click="retryParse(file)"
            >
              {{ t('retryParse') }}
            </ElButton>
          </div>
        </div>
        <div class="file-actions">
          <ElButton circle text :icon="View" :title="t('preview')" @click="access(file, 'preview')" />
          <ElButton
            circle
            text
            :icon="Download"
            :title="t('download')"
            @click="access(file, 'download')"
          />
          <ElButton
            circle
            text
            type="danger"
            :icon="Delete"
            :title="t('delete')"
            @click="remove(file)"
          />
        </div>
      </article>
      <ElEmpty v-if="!loading && !files.length" :description="t('noAttachments')" />
    </div>
  </ElDrawer>

  <ElDialog v-model="parseDialogOpen" :title="t('parsedContent')" width="min(760px, 92vw)">
    <pre class="parsed-content">{{ parseResult?.parsed_text || t('emptyParsedContent') }}</pre>
  </ElDialog>
</template>

<style scoped>
.upload-icon {
  margin-bottom: 10px;
  color: var(--ks-primary);
  font-size: 48px;
}

.upload-tip {
  color: #8a9992;
  font-size: 12px;
}

.progress {
  margin-top: 16px;
}

.file-list {
  min-height: 180px;
  display: grid;
  gap: 10px;
  margin-top: 24px;
}

.file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  border: 1px solid var(--ks-border);
  border-radius: 10px;
}

.file-info {
  min-width: 0;
  display: grid;
  gap: 5px;
}

.file-info strong {
  overflow: hidden;
  color: #294138;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-info small {
  color: #84938c;
}

.parse-state {
  display: flex;
  align-items: center;
  gap: 4px;
}

.clickable {
  cursor: pointer;
}

.file-actions {
  flex: 0 0 auto;
}

.parsed-content {
  max-height: 60vh;
  margin: 0;
  padding: 16px;
  overflow: auto;
  border-radius: 8px;
  background: #f4f8f6;
  color: #294138;
  font-family: inherit;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
