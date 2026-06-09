import { http } from './http'
import type {
  Category,
  DocumentFile,
  DocumentVersion,
  FileAccess,
  FileParseResult,
  KnowledgeDocument,
  KnowledgeSpace,
  Page,
  Tag,
} from '@/types'

export const knowledgeApi = {
  async spaces() {
    return (await http.get<KnowledgeSpace[]>('/spaces')).data
  },
  async createSpace(payload: Record<string, unknown>) {
    return (await http.post<KnowledgeSpace>('/spaces', payload)).data
  },
  async updateSpace(id: number, payload: Record<string, unknown>) {
    return (await http.patch<KnowledgeSpace>(`/spaces/${id}`, payload)).data
  },
  async deleteSpace(id: number) {
    await http.delete(`/spaces/${id}`)
  },
  async categories(spaceId: number) {
    return (await http.get<Category[]>(`/spaces/${spaceId}/categories`)).data
  },
  async createCategory(spaceId: number, payload: Record<string, unknown>) {
    return (await http.post<Category>(`/spaces/${spaceId}/categories`, payload)).data
  },
  async updateCategory(id: number, payload: Record<string, unknown>) {
    return (await http.patch<Category>(`/categories/${id}`, payload)).data
  },
  async deleteCategory(id: number) {
    await http.delete(`/categories/${id}`)
  },
  async tags() {
    return (await http.get<Tag[]>('/tags')).data
  },
  async createTag(payload: Record<string, unknown>) {
    return (await http.post<Tag>('/tags', payload)).data
  },
  async documents(params: Record<string, unknown>) {
    return (await http.get<Page<KnowledgeDocument>>('/documents', { params })).data
  },
  async document(id: number) {
    return (await http.get<KnowledgeDocument>(`/documents/${id}`)).data
  },
  async createDocument(payload: Record<string, unknown>) {
    return (await http.post<KnowledgeDocument>('/documents', payload)).data
  },
  async updateDocument(id: number, payload: Record<string, unknown>) {
    return (await http.patch<KnowledgeDocument>(`/documents/${id}`, payload)).data
  },
  async deleteDocument(id: number) {
    await http.delete(`/documents/${id}`)
  },
  async submitDocument(id: number) {
    return (await http.post<KnowledgeDocument>(`/documents/${id}/submit`)).data
  },
  async reviewDocument(id: number, action: 'approve' | 'reject', comment?: string) {
    return (
      await http.post<KnowledgeDocument>(`/documents/${id}/${action}`, {
        comment: comment || null,
      })
    ).data
  },
  async archiveDocument(id: number) {
    return (await http.post<KnowledgeDocument>(`/documents/${id}/archive`)).data
  },
  async versions(id: number) {
    return (await http.get<DocumentVersion[]>(`/documents/${id}/versions`)).data
  },
  async restoreVersion(documentId: number, versionId: number) {
    return (
      await http.post<KnowledgeDocument>(
        `/documents/${documentId}/versions/${versionId}/restore`,
      )
    ).data
  },
  async files(documentId: number) {
    return (await http.get<DocumentFile[]>(`/files/documents/${documentId}`)).data
  },
  async uploadFile(documentId: number, file: File, onProgress?: (percent: number) => void) {
    const body = new FormData()
    body.append('file', file)
    return (
      await http.post<DocumentFile>(`/files/documents/${documentId}`, body, {
        onUploadProgress: (event) => {
          if (event.total) onProgress?.(Math.round((event.loaded / event.total) * 100))
        },
      })
    ).data
  },
  async fileAccess(fileId: number, mode: 'preview' | 'download') {
    return (await http.get<FileAccess>(`/files/${fileId}/${mode}`)).data
  },
  async fileParse(fileId: number) {
    return (await http.get<FileParseResult>(`/files/${fileId}/parse`)).data
  },
  async retryFileParse(fileId: number) {
    return (await http.post<DocumentFile>(`/files/${fileId}/parse`)).data
  },
  async deleteFile(fileId: number) {
    await http.delete(`/files/${fileId}`)
  },
}
