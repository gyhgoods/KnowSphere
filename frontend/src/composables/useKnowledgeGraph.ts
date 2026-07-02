import { computed, shallowRef } from 'vue'
import { graphApi } from '@/services/ai'
import { knowledgeApi } from '@/services/knowledge'
import type { GraphResponse, KnowledgeSpace } from '@/types'

export function useKnowledgeGraph() {
  const spaces = shallowRef<KnowledgeSpace[]>([])
  const selectedSpaceId = shallowRef<number | null>(null)
  const relationFilter = shallowRef<'all' | 'strong'>('all')
  const graph = shallowRef<GraphResponse>({ entities: [], relations: [] })
  const loading = shallowRef(false)
  const hasGraph = computed(() => graph.value.relations.length > 0)

  async function initialize() {
    spaces.value = await knowledgeApi.spaces()
    await loadGraph()
  }

  async function loadGraph() {
    loading.value = true
    try {
      graph.value = await graphApi.graph({
        space_id: selectedSpaceId.value,
        relation_filter: relationFilter.value,
      })
    } finally {
      loading.value = false
    }
  }

  return {
    spaces,
    selectedSpaceId,
    relationFilter,
    graph,
    loading,
    hasGraph,
    initialize,
    loadGraph,
  }
}
