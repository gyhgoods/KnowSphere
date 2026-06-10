import { http } from './http'
import type { SearchFilters, SearchResponse } from '@/types'

export const searchApi = {
  async hybrid(filters: SearchFilters) {
    const payload = {
      query: filters.query.trim(),
      mode: filters.mode,
      space_id: filters.space_id,
      category_id: filters.category_id,
      status: filters.status,
      tag_ids: filters.tag_ids,
      source_type: filters.source_type,
      updated_from: filters.updated_range?.[0] ?? null,
      updated_to: filters.updated_range?.[1] ?? null,
      semantic_weight: filters.semantic_weight,
      limit: filters.limit,
    }
    return (await http.post<SearchResponse>('/search/hybrid', payload)).data
  },
}
