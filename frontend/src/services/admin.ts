import { http } from './http'
import type { Department, Page, Permission, ResourceGrant, Role, User } from '@/types'

export const adminApi = {
  async users(params: { page?: number; page_size?: number; keyword?: string } = {}) {
    return (await http.get<Page<User>>('/users', { params })).data
  },
  async createUser(payload: Record<string, unknown>) {
    return (await http.post<User>('/users', payload)).data
  },
  async updateUser(id: number, payload: Record<string, unknown>) {
    return (await http.patch<User>(`/users/${id}`, payload)).data
  },
  async departments() {
    return (await http.get<Department[]>('/departments')).data
  },
  async createDepartment(payload: Record<string, unknown>) {
    return (await http.post<Department>('/departments', payload)).data
  },
  async updateDepartment(id: number, payload: Record<string, unknown>) {
    return (await http.patch<Department>(`/departments/${id}`, payload)).data
  },
  async roles() {
    return (await http.get<Role[]>('/rbac/roles')).data
  },
  async createRole(payload: Record<string, unknown>) {
    return (await http.post<Role>('/rbac/roles', payload)).data
  },
  async updateRole(id: number, payload: Record<string, unknown>) {
    return (await http.patch<Role>(`/rbac/roles/${id}`, payload)).data
  },
  async permissions() {
    return (await http.get<Permission[]>('/rbac/permissions')).data
  },
  async grants() {
    return (await http.get<ResourceGrant[]>('/rbac/grants')).data
  },
  async createGrant(payload: Record<string, unknown>) {
    return (await http.post<ResourceGrant>('/rbac/grants', payload)).data
  },
  async deleteGrant(id: number) {
    await http.delete(`/rbac/grants/${id}`)
  },
}

