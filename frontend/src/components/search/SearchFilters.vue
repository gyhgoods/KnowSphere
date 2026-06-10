<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { useI18n } from '@/composables/useI18n'
import type { Category, KnowledgeSpace, SearchFilters, Tag } from '@/types'

defineProps<{
  spaces: readonly KnowledgeSpace[]
  categories: readonly Category[]
  tags: readonly Tag[]
  loading: boolean
}>()

const filters = defineModel<SearchFilters>({ required: true })
const emit = defineEmits<{
  search: []
  reset: []
}>()
const { t } = useI18n()
</script>

<template>
  <section class="search-panel">
    <div class="query-row">
      <ElInput
        v-model="filters.query"
        size="large"
        clearable
        :prefix-icon="Search"
        :placeholder="t('unifiedSearchPlaceholder')"
        @keyup.enter="emit('search')"
      />
      <ElButton type="primary" size="large" :loading="loading" @click="emit('search')">
        {{ t('search') }}
      </ElButton>
    </div>

    <div class="filter-grid">
      <ElSelect v-model="filters.mode" :placeholder="t('searchMode')">
        <ElOption :label="t('hybridSearch')" value="hybrid" />
        <ElOption :label="t('semanticSearch')" value="semantic" />
        <ElOption :label="t('lexicalSearch')" value="lexical" />
      </ElSelect>
      <ElSelect v-model="filters.space_id" clearable :placeholder="t('allSpaces')">
        <ElOption v-for="space in spaces" :key="space.id" :label="space.name" :value="space.id" />
      </ElSelect>
      <ElSelect
        v-model="filters.category_id"
        clearable
        :disabled="!filters.space_id"
        :placeholder="t('allCategories')"
      >
        <ElOption
          v-for="category in categories"
          :key="category.id"
          :label="category.name"
          :value="category.id"
        />
      </ElSelect>
      <ElSelect v-model="filters.status" clearable :placeholder="t('allStatuses')">
        <ElOption :label="t('draft')" value="draft" />
        <ElOption :label="t('inReview')" value="in_review" />
        <ElOption :label="t('published')" value="published" />
        <ElOption :label="t('rejected')" value="rejected" />
        <ElOption :label="t('archived')" value="archived" />
      </ElSelect>
      <ElSelect
        v-model="filters.tag_ids"
        multiple
        collapse-tags
        clearable
        :placeholder="t('tags')"
      >
        <ElOption v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
      </ElSelect>
      <ElSelect v-model="filters.source_type" :placeholder="t('allSources')">
        <ElOption :label="t('allSources')" value="all" />
        <ElOption :label="t('documentSource')" value="document" />
        <ElOption :label="t('fileSource')" value="file" />
      </ElSelect>
      <ElDatePicker
        v-model="filters.updated_range"
        type="datetimerange"
        value-format="YYYY-MM-DDTHH:mm:ssZ"
        :start-placeholder="t('updatedFrom')"
        :end-placeholder="t('updatedTo')"
      />
      <ElButton class="reset-button" @click="emit('reset')">{{ t('reset') }}</ElButton>
    </div>
  </section>
</template>

<style scoped>
.search-panel {
  padding: 22px;
  border: 1px solid var(--ks-border);
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 10px 28px rgb(16 42 33 / 8%);
}

.query-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.filter-grid :deep(.el-date-editor) {
  width: 100%;
}

.reset-button {
  justify-self: end;
}

@media (max-width: 1100px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }
}

@media (max-width: 680px) {
  .query-row,
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .reset-button {
    justify-self: stretch;
  }
}
</style>
