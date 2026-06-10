<script setup lang="ts">
import { Document, Files, Right } from '@element-plus/icons-vue'
import { useI18n } from '@/composables/useI18n'
import type { SearchResponse, SearchResult } from '@/types'

defineProps<{
  response: SearchResponse | null
  results: readonly SearchResult[]
  loading: boolean
  searched: boolean
}>()

const emit = defineEmits<{
  open: [result: SearchResult]
}>()
const { t } = useI18n()

function explanationLabel(value: string) {
  const labels: Record<string, string> = {
    semantic_match: t('semanticMatch'),
    title_phrase: t('titlePhraseMatch'),
    title_terms: t('titleTermsMatch'),
    content_phrase: t('contentPhraseMatch'),
    content_terms: t('contentTermsMatch'),
    primary_document: t('primaryDocumentMatch'),
  }
  return labels[value] ?? value
}
</script>

<template>
  <section class="results">
    <header v-if="response" class="results-summary">
      <strong>{{ t('resultCount', { count: results.length }) }}</strong>
      <span>{{ response.took_ms }} ms · {{ response.model }}</span>
    </header>

    <ElSkeleton v-if="loading" :rows="6" animated />
    <ElEmpty v-else-if="!searched" :description="t('searchPrompt')" />
    <ElEmpty v-else-if="!results.length" :description="t('noSearchResults')" />

    <article v-for="result in results" v-else :key="result.chunk_id" class="result-card">
      <div class="result-icon">
        <ElIcon><Files v-if="result.source_type === 'file'" /><Document v-else /></ElIcon>
      </div>
      <div class="result-body">
        <div class="result-heading">
          <div>
            <h3>{{ result.document_title }}</h3>
            <p>{{ result.source_name }} · {{ new Date(result.updated_at).toLocaleString() }}</p>
          </div>
          <div class="score">{{ Math.round(result.score.rerank * 100) }}</div>
        </div>
        <p class="snippet">{{ result.content }}</p>
        <div class="result-footer">
          <div class="badges">
            <ElTag v-for="tag in result.tag_names" :key="tag" size="small" effect="plain">
              {{ tag }}
            </ElTag>
            <ElTag
              v-for="reason in result.explanations"
              :key="reason"
              size="small"
              type="success"
              effect="light"
            >
              {{ explanationLabel(reason) }}
            </ElTag>
          </div>
          <div class="result-actions">
            <span>{{ t('semanticScore') }} {{ result.score.semantic.toFixed(2) }}</span>
            <span>{{ t('lexicalScore') }} {{ result.score.lexical.toFixed(2) }}</span>
            <ElButton link type="primary" :icon="Right" @click="emit('open', result)">
              {{ t('openDocument') }}
            </ElButton>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped>
.results {
  margin-top: 20px;
}

.results-summary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  color: var(--ks-muted);
  font-size: 13px;
}

.result-card {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr);
  gap: 15px;
  margin-bottom: 12px;
  padding: 20px;
  border: 1px solid var(--ks-border);
  border-radius: 13px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgb(16 42 33 / 6%);
}

.result-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: var(--ks-primary);
  background: #e8f5f1;
  font-size: 20px;
}

.result-heading,
.result-footer,
.result-actions,
.badges {
  display: flex;
  align-items: center;
}

.result-heading,
.result-footer {
  justify-content: space-between;
  gap: 16px;
}

.result-heading h3 {
  margin: 0 0 5px;
  color: var(--ks-ink);
  font-size: 17px;
}

.result-heading p {
  margin: 0;
  color: var(--ks-muted);
  font-size: 12px;
}

.score {
  min-width: 48px;
  padding: 8px;
  border-radius: 9px;
  color: #ffffff;
  background: var(--ks-primary);
  text-align: center;
  font-weight: 800;
}

.snippet {
  display: -webkit-box;
  margin: 13px 0;
  overflow: hidden;
  color: #40564d;
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.badges,
.result-actions {
  flex-wrap: wrap;
  gap: 7px;
}

.result-actions {
  justify-content: flex-end;
  color: var(--ks-muted);
  font-size: 12px;
}

@media (max-width: 760px) {
  .result-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
