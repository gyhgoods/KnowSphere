<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { useI18n } from '@/composables/useI18n'
import type { Category, KnowledgeDocument, KnowledgeSpace, Tag } from '@/types'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  document: KnowledgeDocument | null
  spaces: readonly KnowledgeSpace[]
  categories: readonly Category[]
  tags: readonly Tag[]
  defaultSpaceId: number | null
  defaultCategoryId: number | null
}>()
const emit = defineEmits<{ save: [payload: Record<string, unknown>, id: number | null] }>()
const { t } = useI18n()

const form = reactive({
  space_id: 0,
  category_id: null as number | null,
  title: '',
  content: '',
  content_format: 'markdown',
  tag_ids: [] as number[],
})

const title = computed(() => (props.document ? t('edit') : t('createDocument')))

const categoryOptions = computed(() => {
  const items: Array<{ id: number; label: string }> = []
  function visit(nodes: readonly Category[], prefix = '') {
    for (const node of nodes) {
      items.push({ id: node.id, label: `${prefix}${node.name}` })
      visit(node.children, `${prefix}— `)
    }
  }
  visit(props.categories)
  return items
})

watch(
  () => [open.value, props.document] as const,
  ([isOpen, document]) => {
    if (!isOpen) return
    Object.assign(form, {
      space_id: document?.space_id ?? props.defaultSpaceId ?? 0,
      category_id: document?.category_id ?? props.defaultCategoryId,
      title: document?.title ?? '',
      content: document?.content ?? '',
      content_format: document?.content_format ?? 'markdown',
      tag_ids: document?.tags.map((tag) => tag.id) ?? [],
    })
  },
  { immediate: true },
)

function save() {
  emit('save', { ...form }, props.document?.id ?? null)
}
</script>

<template>
  <ElDialog v-model="open" :title="title" width="min(900px, 92vw)" destroy-on-close>
    <ElForm label-position="top">
      <div class="form-grid">
        <ElFormItem :label="t('space')">
          <ElSelect v-model="form.space_id" :disabled="Boolean(document)">
            <ElOption
              v-for="space in spaces"
              :key="space.id"
              :label="space.name"
              :value="space.id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem :label="t('category')">
          <ElSelect v-model="form.category_id" clearable>
            <ElOption
              v-for="category in categoryOptions"
              :key="category.id"
              :label="category.label"
              :value="category.id"
            />
          </ElSelect>
        </ElFormItem>
      </div>
      <ElFormItem :label="t('title')"><ElInput v-model="form.title" maxlength="255" /></ElFormItem>
      <div class="form-grid">
        <ElFormItem :label="t('contentFormat')">
          <ElRadioGroup v-model="form.content_format">
            <ElRadioButton value="markdown">Markdown</ElRadioButton>
            <ElRadioButton value="plain">{{ t('plainText') }}</ElRadioButton>
            <ElRadioButton value="html">{{ t('richText') }}</ElRadioButton>
          </ElRadioGroup>
        </ElFormItem>
        <ElFormItem :label="t('tags')">
          <ElSelect v-model="form.tag_ids" multiple filterable>
            <ElOption v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </ElSelect>
        </ElFormItem>
      </div>
      <ElFormItem :label="t('content')">
        <ElInput
          v-model="form.content"
          type="textarea"
          :rows="16"
          resize="vertical"
          :placeholder="t('contentPlaceholder')"
        />
      </ElFormItem>
    </ElForm>
    <template #footer>
      <ElButton @click="open = false">{{ t('cancel') }}</ElButton>
      <ElButton type="primary" :disabled="!form.title || !form.space_id" @click="save">
        {{ t('saveDraft') }}
      </ElButton>
    </template>
  </ElDialog>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-textarea__inner) {
  font-family: "Cascadia Code", Consolas, monospace;
  line-height: 1.65;
}

@media (max-width: 680px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
