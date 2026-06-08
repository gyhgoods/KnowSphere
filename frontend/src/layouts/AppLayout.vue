<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  await router.push('/login')
}
</script>

<template>
  <ElContainer class="app-shell">
    <ElAside class="sidebar" width="220px">
      <div class="brand">KnowSphere</div>
      <ElMenu router default-active="/admin/users" class="menu">
        <ElMenuItem v-if="auth.hasPermission('user.manage')" index="/admin/users">
          用户管理
        </ElMenuItem>
        <ElMenuItem v-if="auth.hasPermission('department.manage')" index="/admin/departments">
          部门管理
        </ElMenuItem>
        <ElMenuItem v-if="auth.hasPermission('rbac.manage')" index="/admin/roles">
          角色权限
        </ElMenuItem>
        <ElMenuItem v-if="auth.hasPermission('rbac.manage')" index="/admin/grants">
          数据权限
        </ElMenuItem>
      </ElMenu>
    </ElAside>
    <ElContainer>
      <ElHeader class="header">
        <span>{{ auth.user?.display_name ?? auth.user?.username }}</span>
        <ElButton link type="primary" @click="logout">退出登录</ElButton>
      </ElHeader>
      <ElMain class="content">
        <RouterView />
      </ElMain>
    </ElContainer>
  </ElContainer>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.sidebar {
  background: #101828;
}

.brand {
  height: 64px;
  display: grid;
  place-items: center;
  color: white;
  font-size: 20px;
  font-weight: 700;
}

.menu {
  border: 0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  background: white;
  border-bottom: 1px solid #e7eaf0;
}

.content {
  padding: 24px;
}
</style>
