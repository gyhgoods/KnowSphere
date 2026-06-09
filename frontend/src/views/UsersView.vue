<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from '@/composables/useI18n'
import { adminApi } from '@/services/admin'
import type { Role, User } from '@/types'

const { t } = useI18n()
const users = shallowRef<User[]>([])
const roles = shallowRef<Role[]>([])
const total = shallowRef(0)
const loading = shallowRef(false)
const dialogOpen = shallowRef(false)
const keyword = shallowRef('')
const form = reactive({
  username: '',
  email: '',
  display_name: '',
  password: '',
  role_ids: [] as number[],
})

async function load() {
  loading.value = true
  try {
    const [userPage, roleList] = await Promise.all([
      adminApi.users({ keyword: keyword.value || undefined }),
      adminApi.roles(),
    ])
    users.value = userPage.items
    total.value = userPage.total
    roles.value = roleList
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, { username: '', email: '', display_name: '', password: '', role_ids: [] })
  dialogOpen.value = true
}

async function create() {
  await adminApi.createUser(form)
  ElMessage.success(t('userCreated'))
  dialogOpen.value = false
  await load()
}

async function toggleStatus(user: User) {
  await adminApi.updateUser(user.id, {
    status: user.status === 'active' ? 'disabled' : 'active',
  })
  await load()
}

onMounted(load)
</script>

<template>
  <ElCard class="page-card">
    <div class="page-header">
      <h1 class="page-title">{{ t('userManagement') }}</h1>
      <ElButton type="primary" @click="openCreate">{{ t('createUser') }}</ElButton>
    </div>
    <ElForm inline @submit.prevent="load">
      <ElFormItem>
        <ElInput v-model="keyword" clearable :placeholder="t('userSearch')" />
      </ElFormItem>
      <ElButton @click="load">{{ t('query') }}</ElButton>
    </ElForm>
    <ElTable v-loading="loading" :data="users">
      <ElTableColumn prop="username" :label="t('username')" />
      <ElTableColumn prop="display_name" :label="t('displayName')" />
      <ElTableColumn prop="email" :label="t('email')" />
      <ElTableColumn :label="t('roles')">
        <template #default="{ row }: { row: User }">
          {{ row.roles.map((role) => role.name).join(', ') || '-' }}
        </template>
      </ElTableColumn>
      <ElTableColumn prop="status" :label="t('status')" />
      <ElTableColumn :label="t('actions')" width="120">
        <template #default="{ row }: { row: User }">
          <ElButton link type="primary" @click="toggleStatus(row)">
            {{ row.status === 'active' ? t('disabled') : t('enabled') }}
          </ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
    <div class="count">{{ t('userCount', { count: total }) }}</div>
  </ElCard>

  <ElDialog v-model="dialogOpen" :title="t('createUser')" width="520px">
    <ElForm label-width="110px">
      <ElFormItem :label="t('username')"><ElInput v-model="form.username" /></ElFormItem>
      <ElFormItem :label="t('displayName')"><ElInput v-model="form.display_name" /></ElFormItem>
      <ElFormItem :label="t('email')"><ElInput v-model="form.email" /></ElFormItem>
      <ElFormItem :label="t('initialPassword')">
        <ElInput v-model="form.password" type="password" />
      </ElFormItem>
      <ElFormItem :label="t('roles')">
        <ElSelect v-model="form.role_ids" multiple>
          <ElOption v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
        </ElSelect>
      </ElFormItem>
    </ElForm>
    <template #footer>
      <ElButton type="primary" @click="create">{{ t('create') }}</ElButton>
    </template>
  </ElDialog>
</template>

<style scoped>
.count {
  margin-top: 16px;
  color: #667085;
  font-size: 13px;
}
</style>
