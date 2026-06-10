import { computed, readonly, shallowRef } from 'vue'
import { knowledgeApi } from '@/services/knowledge'
import type { Category, KnowledgeDocument, KnowledgeSpace, Tag } from '@/types'

export function useKnowledgeWorkspace() {
  const spaces = shallowRef<KnowledgeSpace[]>([])
  const categories = shallowRef<Category[]>([])
  const tags = shallowRef<Tag[]>([])
  const documents = shallowRef<KnowledgeDocument[]>([])
  const selectedSpaceId = shallowRef<number | null>(null)
  const selectedCategoryId = shallowRef<number | null>(null)
  const keyword = shallowRef('')
  const loading = shallowRef(false)
  const total = shallowRef(0)

  const selectedSpace = computed(
    () => spaces.value.find((space) => space.id === selectedSpaceId.value) ?? null,
  )

  async function initialize(options?: {
    spaceId?: number | null
    categoryId?: number | null
    keyword?: string
  }) {
    loading.value = true
    try {
      ;[spaces.value, tags.value] = await Promise.all([knowledgeApi.spaces(), knowledgeApi.tags()])
      if (options?.keyword) keyword.value = options.keyword
      if (options?.spaceId && spaces.value.some((space) => space.id === options.spaceId)) {
        selectedSpaceId.value = options.spaceId
      }
      if (!selectedSpaceId.value && spaces.value.length) {
        selectedSpaceId.value = spaces.value[0].id
      }
      if (selectedSpaceId.value) {
        await selectSpace(selectedSpaceId.value)
        if (
          options?.categoryId &&
          categories.value.some((category) => category.id === options.categoryId)
        ) {
          await selectCategory(options.categoryId)
        }
      }
    } finally {
      loading.value = false
    }
  }

  async function selectSpace(spaceId: number) {
    selectedSpaceId.value = spaceId
    selectedCategoryId.value = null
    ;[categories.value] = await Promise.all([knowledgeApi.categories(spaceId)])
    await loadDocuments()
  }

  async function selectCategory(categoryId: number | null) {
    selectedCategoryId.value = categoryId
    await loadDocuments()
  }

  async function loadDocuments() {
    if (!selectedSpaceId.value) {
      documents.value = []
      total.value = 0
      return
    }
    loading.value = true
    try {
      const page = await knowledgeApi.documents({
        space_id: selectedSpaceId.value,
        category_id: selectedCategoryId.value ?? undefined,
        keyword: keyword.value || undefined,
      })
      documents.value = page.items
      total.value = page.total
    } finally {
      loading.value = false
    }
  }

  async function refreshSpaces() {
    spaces.value = await knowledgeApi.spaces()
    if (
      selectedSpaceId.value &&
      !spaces.value.some((space) => space.id === selectedSpaceId.value)
    ) {
      selectedSpaceId.value = spaces.value[0]?.id ?? null
      selectedCategoryId.value = null
    }
    if (selectedSpaceId.value) {
      await selectSpace(selectedSpaceId.value)
    } else {
      categories.value = []
      documents.value = []
      total.value = 0
    }
  }

  async function refreshCategories() {
    if (selectedSpaceId.value) {
      categories.value = await knowledgeApi.categories(selectedSpaceId.value)
    }
  }

  async function refreshTags() {
    tags.value = await knowledgeApi.tags()
  }

  return {
    spaces: readonly(spaces),
    categories: readonly(categories),
    tags: readonly(tags),
    documents: readonly(documents),
    selectedSpaceId,
    selectedCategoryId,
    keyword,
    loading: readonly(loading),
    total: readonly(total),
    selectedSpace,
    initialize,
    selectSpace,
    selectCategory,
    loadDocuments,
    refreshSpaces,
    refreshCategories,
    refreshTags,
  }
}
