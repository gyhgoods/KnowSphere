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
