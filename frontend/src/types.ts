export interface RoleSummary {
  id: number
  code: string
  name: string
}

export interface Permission {
  id: number
  code: string
  name: string
  resource_type: string
  action: string
  description: string | null
}

export interface Role extends RoleSummary {
  description: string | null
  is_system: boolean
  permissions: Permission[]
}

export interface User {
  id: number
  username: string
  email: string
  display_name: string
  department_id: number | null
  status: 'active' | 'disabled'
  is_superuser: boolean
  roles: RoleSummary[]
  permission_codes?: string[]
  created_at: string
}

export interface Department {
  id: number
  parent_id: number | null
  name: string
  sort: number
  is_active: boolean
  children: Department[]
}

export interface ResourceGrant {
  id: number
  subject_type: 'user' | 'role' | 'department'
  subject_id: number
  resource_type: 'space' | 'project' | 'document'
  resource_id: string
  action: string
  effect: 'allow' | 'deny'
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type SpaceVisibility = 'private' | 'department' | 'public'
export type DocumentStatus = 'draft' | 'in_review' | 'published' | 'rejected' | 'archived'

export interface KnowledgeSpace {
  id: number
  name: string
  code: string
  description: string | null
  visibility: SpaceVisibility
  department_id: number | null
  created_by: number
  is_active: boolean
  created_at: string
}

export interface Category {
  id: number
  space_id: number
  parent_id: number | null
  name: string
  sort: number
  children: readonly Category[]
}

export interface Tag {
  id: number
  name: string
  color: string
  usage_count: number
}

export interface KnowledgeDocument {
  id: number
  space_id: number
  category_id: number | null
  title: string
  content: string
  content_format: 'markdown' | 'plain' | 'html'
  status: DocumentStatus
  author_id: number
  reviewer_id: number | null
  review_comment: string | null
  version_no: number
  tags: readonly Tag[]
  created_at: string
  updated_at: string
}

export interface DocumentVersion {
  id: number
  document_id: number
  version_no: number
  title: string
  content: string
  content_format: string
  created_by: number
  created_at: string
}

export interface DocumentFile {
  id: number
  document_id: number
  file_name: string
  mime_type: string
  file_size: number
  checksum: string
  uploaded_by: number
  parse_status: 'queued' | 'processing' | 'completed' | 'failed' | 'unsupported'
  parse_task_id: string | null
  parse_error: string | null
  parsed_text_length: number
  created_at: string
}

export interface FileParseResult {
  id: number
  parse_status: DocumentFile['parse_status']
  parse_task_id: string | null
  parse_error: string | null
  parsed_text: string | null
  parse_started_at: string | null
  parse_completed_at: string | null
}

export interface FileAccess {
  url: string
  expires_in: number
  previewable: boolean
}

export type SearchMode = 'hybrid' | 'semantic' | 'lexical'
export type SearchSourceType = 'all' | 'document' | 'file'

export interface SearchFilters {
  query: string
  mode: SearchMode
  space_id: number | null
  category_id: number | null
  status: DocumentStatus | null
  tag_ids: number[]
  source_type: SearchSourceType
  updated_range: [string, string] | null
  semantic_weight: number
  limit: number
}

export interface SearchResultScore {
  semantic: number
  lexical: number
  fused: number
  rerank: number
}

export interface SearchResult {
  chunk_id: number
  document_id: number
  document_title: string
  space_id: number
  category_id: number | null
  status: DocumentStatus
  tag_ids: number[]
  tag_names: string[]
  file_id: number | null
  source_name: string
  source_type: Exclude<SearchSourceType, 'all'>
  content: string
  updated_at: string
  score: SearchResultScore
  explanations: string[]
}

export interface SearchResponse {
  query: string
  mode: SearchMode
  model: string
  total_candidates: number
  took_ms: number
  items: SearchResult[]
}

export interface Citation {
  index: number
  document_id: number
  document_title: string
  chunk_id: number
  source_name: string
  excerpt: string
  score: number
  source_type: 'text' | 'image'
  image_url: string | null
  image_name: string | null
  image_mime_type: string | null
  image_document_title: string | null
}

export interface AskResponse {
  conversation_id: number
  question_message_id: number
  answer_message_id: number
  answer: string
  confidence: number
  model: string
  citations: Citation[]
}

export interface AIConversation {
  id: number
  title: string
  status: 'active' | 'archived'
  created_at: string
  updated_at: string
}

export interface AIMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  confidence: number | null
  model_name: string | null
  created_at: string
}

export interface GraphEntity {
  id: number
  name: string
  entity_type: string
  description: string | null
}

export interface GraphRelation {
  id: number
  source_entity_id: number
  source_name: string
  target_entity_id: number
  target_name: string
  relation_type: string
  document_id: number
  document_title: string
  confidence: number
  evidence: string | null
}

export interface GraphResponse {
  entities: GraphEntity[]
  relations: GraphRelation[]
}
