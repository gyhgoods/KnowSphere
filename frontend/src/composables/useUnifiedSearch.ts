import { computed, reactive, readonly, shallowRef, watch } from 'vue'
import { knowledgeApi } from '@/services/knowledge'
import { searchApi } from '@/services/search'
import type {
  Category,
  KnowledgeSpace,
  SearchFilters,
  SearchResponse,
  Tag,
} from '@/types'

const defaultFilters = (): SearchFilters => ({
  query: '',
  mode: 'hybrid',
  space_id: null,
  category_id: null,
  status: null,
  tag_ids: [],
  source_type: 'all',
  updated_range: null,
  semantic_weight: 0.65,
  limit: 10,
})

function flattenCategories(items: readonly Category[], depth = 0): Category[] {
  return items.flatMap((item) => [
    { ...item, name: `${'— '.repeat(depth)}${item.name}` },
    ...flattenCategories(item.children, depth + 1),
  ])
}

export function useUnifiedSearch() {
  const filters = reactive<SearchFilters>(defaultFilters())
  const spaces = shallowRef<KnowledgeSpace[]>([])
  const categories = shallowRef<Category[]>([])
  const tags = shallowRef<Tag[]>([])
  const response = shallowRef<SearchResponse | null>(null)
  const loading = shallowRef(false)
  const searched = shallowRef(false)
  const results = computed(() => response.value?.items ?? [])
  const categoryOptions = computed(() => flattenCategories(categories.value))

  watch(
    () => filters.space_id,
    async (spaceId) => {
      filters.category_id = null
      categories.value = spaceId ? await knowledgeApi.categories(spaceId) : []
    },
  )

  async function initialize() {
    ;[spaces.value, tags.value] = await Promise.all([knowledgeApi.spaces(), knowledgeApi.tags()])
  }

  async function search() {
    if (!filters.query.trim()) return
    loading.value = true
    searched.value = true
    try {
      response.value = await searchApi.hybrid(filters)
    } finally {
      loading.value = false
    }
  }

  function reset() {
    Object.assign(filters, defaultFilters())
    response.value = null
    searched.value = false
  }

  return {
    filters,
    spaces: readonly(spaces),
    categories: categoryOptions,
    tags: readonly(tags),
    response,
    results,
    loading: readonly(loading),
    searched: readonly(searched),
    initialize,
    search,
    reset,
  }
}
