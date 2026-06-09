<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '@/composables/useI18n'
import type { KnowledgeDocument } from '@/types'

defineProps<{
  documents: readonly KnowledgeDocument[]
  loading: boolean
}>()

const emit = defineEmits<{
  edit: [document: KnowledgeDocument]
  remove: [document: KnowledgeDocument]
  submit: [document: KnowledgeDocument]
  review: [document: KnowledgeDocument]
  archive: [document: KnowledgeDocument]
  versions: [document: KnowledgeDocument]
  files: [document: KnowledgeDocument]
}>()

const { t, locale } = useI18n()
const statusMap = computed(() => ({
  draft: { label: t('draft'), type: 'info' as const },
  in_review: { label: t('inReview'), type: 'warning' as const },
  published: { label: t('published'), type: 'success' as const },
  rejected: { label: t('rejected'), type: 'danger' as const },
  archived: { label: t('archived'), type: 'info' as const },
}))
</script>

<template>
  <ElTable v-loading="loading" :data="documents" row-key="id">
    <ElTableColumn prop="title" :label="t('document')" min-width="230">
      <template #default="{ row }: { row: KnowledgeDocument }">
        <button class="document-title" type="button" @click="emit('edit', row)">
          <strong>{{ row.title }}</strong>
          <small>v{{ row.version_no }} · {{ row.content_format }}</small>
        </button>
      </template>
    </ElTableColumn>
    <ElTableColumn :label="t('tags')" min-width="180">
      <template #default="{ row }: { row: KnowledgeDocument }">
        <ElTag
          v-for="tag in row.tags"
          :key="tag.id"
          class="tag"
          effect="plain"
          :color="`${tag.color}12`"
        >
          {{ tag.name }}
        </ElTag>
        <span v-if="!row.tags.length" class="muted">-</span>
      </template>
    </ElTableColumn>
    <ElTableColumn :label="t('status')" width="110">
      <template #default="{ row }: { row: KnowledgeDocument }">
        <ElTag :type="statusMap[row.status].type">{{ statusMap[row.status].label }}</ElTag>
      </template>
    </ElTableColumn>
    <ElTableColumn prop="updated_at" :label="t('updatedAt')" width="180">
      <template #default="{ row }: { row: KnowledgeDocument }">
        {{ new Date(row.updated_at).toLocaleString(locale === 'zh' ? 'zh-CN' : 'en-US') }}
      </template>
    </ElTableColumn>
    <ElTableColumn :label="t('actions')" width="310" fixed="right">
      <template #default="{ row }: { row: KnowledgeDocument }">
        <ElButton link type="primary" @click="emit('edit', row)">{{ t('edit') }}</ElButton>
        <ElButton link @click="emit('files', row)">{{ t('files') }}</ElButton>
        <ElButton link @click="emit('versions', row)">{{ t('versions') }}</ElButton>
        <ElButton
          v-if="row.status === 'draft' || row.status === 'rejected'"
          link
          type="success"
          @click="emit('submit', row)"
        >
          {{ t('submit') }}
        </ElButton>
        <ElButton
          v-if="row.status === 'in_review'"
          link
          type="warning"
          @click="emit('review', row)"
        >
          {{ t('review') }}
        </ElButton>
        <ElButton
          v-if="row.status === 'published'"
          link
          type="warning"
          @click="emit('archive', row)"
        >
          {{ t('archive') }}
        </ElButton>
        <ElButton link type="danger" @click="emit('remove', row)">{{ t('delete') }}</ElButton>
      </template>
    </ElTableColumn>
    <template #empty><ElEmpty :description="t('noDocuments')" /></template>
  </ElTable>
</template>

<style scoped>
.document-title {
  display: grid;
  gap: 5px;
  padding: 0;
  border: 0;
  color: #20372e;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.document-title:hover {
  color: var(--ks-primary);
}

.document-title small,
.muted {
  color: #8a9992;
}

.tag {
  margin: 2px 5px 2px 0;
  border-color: transparent;
}
</style>
