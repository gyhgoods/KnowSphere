import { createRouter, createWebHistory } from 'vue-router'
import { tokenStorage } from '@/services/http'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/knowledge' },
        {
          path: 'knowledge',
          component: () => import('@/views/KnowledgeWorkspaceView.vue'),
          meta: { permission: 'document.view' },
        },
        {
          path: 'search',
          component: () => import('@/views/UnifiedSearchView.vue'),
          meta: { permission: 'document.view' },
        },
        {
          path: 'admin/users',
          component: () => import('@/views/UsersView.vue'),
          meta: { permission: 'user.manage' },
        },
        {
          path: 'admin/departments',
          component: () => import('@/views/DepartmentsView.vue'),
          meta: { permission: 'department.manage' },
        },
        {
          path: 'admin/roles',
          component: () => import('@/views/RolesView.vue'),
          meta: { permission: 'rbac.manage' },
        },
        {
          path: 'admin/grants',
          component: () => import('@/views/GrantsView.vue'),
          meta: { permission: 'rbac.manage' },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth && !tokenStorage.accessToken) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && tokenStorage.accessToken) return '/'
  if (to.meta.permission && tokenStorage.accessToken) {
    const auth = useAuthStore()
    if (!auth.user) await auth.fetchCurrentUser()
    if (!auth.hasPermission(String(to.meta.permission))) return { name: 'forbidden' }
  }
})

export default router
