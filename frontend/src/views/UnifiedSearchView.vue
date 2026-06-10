<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SearchFilters from '@/components/search/SearchFilters.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import { useI18n } from '@/composables/useI18n'
import { useUnifiedSearch } from '@/composables/useUnifiedSearch'
import type { SearchResult } from '@/types'

const router = useRouter()
const search = useUnifiedSearch()
const { t } = useI18n()

onMounted(search.initialize)

async function openResult(result: SearchResult) {
  await router.push({
    path: '/knowledge',
    query: {
      space_id: String(result.space_id),
      category_id: result.category_id ? String(result.category_id) : undefined,
      keyword: result.document_title,
    },
  })
}
</script>

<template>
  <main class="search-view">
    <header class="search-header">
      <p>ENTERPRISE RETRIEVAL</p>
      <h2>{{ t('unifiedSearch') }}</h2>
      <span>{{ t('unifiedSearchDescription') }}</span>
    </header>
    <SearchFilters
      v-model="search.filters"
      :spaces="search.spaces.value"
      :categories="search.categories.value"
      :tags="search.tags.value"
      :loading="search.loading.value"
      @search="search.search"
      @reset="search.reset"
    />
    <SearchResults
      :response="search.response.value"
      :results="search.results.value"
      :loading="search.loading.value"
      :searched="search.searched.value"
      @open="openResult"
    />
  </main>
</template>

<style scoped>
.search-view {
  max-width: 1320px;
  margin: 0 auto;
}

.search-header {
  margin-bottom: 20px;
}

.search-header p {
  margin: 0 0 7px;
  color: var(--ks-primary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.search-header h2 {
  margin: 0;
  color: var(--ks-ink);
  font-size: 26px;
}

.search-header span {
  display: block;
  margin-top: 8px;
  color: var(--ks-muted);
}
</style>
