<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Collection,
  Files,
  Key,
  Switch,
  OfficeBuilding,
  SwitchButton,
  UserFilled,
} from '@element-plus/icons-vue'
import { useI18n } from '@/composables/useI18n'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { t, toggleLocale } = useI18n()

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/knowledge': t('knowledgeWorkspace'),
    '/admin/users': t('userManagement'),
    '/admin/departments': t('departmentManagement'),
    '/admin/roles': t('rolePermissions'),
    '/admin/grants': t('dataPermissions'),
  }
  return titles[route.path] ?? t('adminCenter')
})

async function logout() {
  await auth.logout()
  await router.push('/login')
}
</script>

<template>
  <ElContainer class="app-shell">
    <ElAside class="sidebar" width="240px">
      <div class="brand">
        <span class="brand-mark">✦</span>
        <span>{{ t('brandName') }}</span>
      </div>
      <p class="menu-caption">{{ t('workspaceManagement') }}</p>
      <ElMenu router :default-active="route.path" class="menu">
        <ElMenuItem v-if="auth.hasPermission('document.view')" index="/knowledge">
          <ElIcon><Files /></ElIcon>
          <span>{{ t('knowledgeWorkspace') }}</span>
        </ElMenuItem>
        <ElMenuItem v-if="auth.hasPermission('user.manage')" index="/admin/users">
          <ElIcon><UserFilled /></ElIcon>
          <span>{{ t('userManagement') }}</span>
        </ElMenuItem>
        <ElMenuItem v-if="auth.hasPermission('department.manage')" index="/admin/departments">
          <ElIcon><OfficeBuilding /></ElIcon>
          <span>{{ t('departmentManagement') }}</span>
        </ElMenuItem>
        <ElMenuItem v-if="auth.hasPermission('rbac.manage')" index="/admin/roles">
          <ElIcon><Key /></ElIcon>
          <span>{{ t('rolePermissions') }}</span>
        </ElMenuItem>
        <ElMenuItem v-if="auth.hasPermission('rbac.manage')" index="/admin/grants">
          <ElIcon><Collection /></ElIcon>
          <span>{{ t('dataPermissions') }}</span>
        </ElMenuItem>
      </ElMenu>
      <div class="sidebar-footer">
        <span class="status-dot"></span>
        {{ t('serviceRunning') }}
      </div>
    </ElAside>
    <ElContainer>
      <ElHeader class="header">
        <div>
          <p>{{ t('consoleName') }}</p>
          <h1>{{ pageTitle }}</h1>
        </div>
        <div class="account">
          <span class="avatar">{{ (auth.user?.display_name ?? auth.user?.username ?? 'A')[0] }}</span>
          <span class="account-name">{{ auth.user?.display_name ?? auth.user?.username }}</span>
          <ElButton class="language" :icon="Switch" @click="toggleLocale">
            {{ t('switchLanguage') }}
          </ElButton>
          <ElButton class="logout" :icon="SwitchButton" @click="logout">{{ t('logout') }}</ElButton>
        </div>
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
  background: #edf3ef;
}

.sidebar {
  position: relative;
  color: white;
  background: #102b22;
}

.brand {
  height: 78px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 22px;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 21px;
  font-weight: 700;
}

.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #15372c;
  background: var(--ks-mint);
  font-size: 22px;
}

.menu-caption {
  margin: 18px 24px 10px;
  color: #8db4a6;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.menu {
  border: 0;
  background: transparent;
}

:deep(.el-menu-item) {
  height: 48px;
  margin: 5px 12px;
  border-radius: 10px;
  color: #b9d0c7;
}

:deep(.el-menu-item:hover) {
  color: white;
  background: #193d32;
}

:deep(.el-menu-item.is-active) {
  color: #ffffff;
  background: #1d4d3d;
}

.sidebar-footer {
  position: absolute;
  right: 22px;
  bottom: 24px;
  left: 22px;
  display: flex;
  align-items: center;
  gap: 9px;
  color: #a6c7bc;
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ks-mint);
  box-shadow: 0 0 0 4px rgb(140 225 197 / 12%);
}

.header {
  height: 78px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: #ffffff;
  border-bottom: 1px solid var(--ks-border);
  box-shadow: 0 2px 10px rgb(20 47 38 / 4%);
}

.header p {
  margin: 0 0 3px;
  color: #536960;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.header h1 {
  margin: 0;
  color: var(--ks-ink);
  font-size: 20px;
}

.account {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #15372c;
  background: var(--ks-mint);
  font-weight: 800;
}

.account-name {
  color: #263e34;
  font-size: 14px;
  font-weight: 600;
}

.logout,
.language {
  margin-left: 8px;
  border-color: var(--ks-border);
  color: #344d43;
  background: #ffffff;
}

.content {
  padding: 28px;
}

@media (max-width: 760px) {
  .sidebar {
    width: 76px !important;
  }

  .brand {
    padding: 0 19px;
  }

  .brand span:last-child,
  .menu-caption,
  .sidebar-footer,
  :deep(.el-menu-item span) {
    display: none;
  }

  :deep(.el-menu-item) {
    justify-content: center;
    padding: 0;
  }

  .account-name {
    display: none;
  }
}
</style>
