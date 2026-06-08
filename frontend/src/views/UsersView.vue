<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/services/admin'
import type { Role, User } from '@/types'

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
  ElMessage.success('用户已创建')
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
      <h1 class="page-title">用户管理</h1>
      <ElButton type="primary" @click="openCreate">新建用户</ElButton>
    </div>
    <ElForm inline @submit.prevent="load">
      <ElFormItem>
        <ElInput v-model="keyword" clearable placeholder="用户名、姓名或邮箱" />
      </ElFormItem>
      <ElButton @click="load">查询</ElButton>
    </ElForm>
    <ElTable v-loading="loading" :data="users">
      <ElTableColumn prop="username" label="用户名" />
      <ElTableColumn prop="display_name" label="姓名" />
      <ElTableColumn prop="email" label="邮箱" />
      <ElTableColumn label="角色">
        <template #default="{ row }: { row: User }">
          {{ row.roles.map((role) => role.name).join('、') || '-' }}
        </template>
      </ElTableColumn>
      <ElTableColumn prop="status" label="状态" />
      <ElTableColumn label="操作" width="120">
        <template #default="{ row }: { row: User }">
          <ElButton link type="primary" @click="toggleStatus(row)">
            {{ row.status === 'active' ? '停用' : '启用' }}
          </ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
    <div class="count">共 {{ total }} 个用户</div>
  </ElCard>

  <ElDialog v-model="dialogOpen" title="新建用户" width="520px">
    <ElForm label-width="90px">
      <ElFormItem label="用户名"><ElInput v-model="form.username" /></ElFormItem>
      <ElFormItem label="姓名"><ElInput v-model="form.display_name" /></ElFormItem>
      <ElFormItem label="邮箱"><ElInput v-model="form.email" /></ElFormItem>
      <ElFormItem label="初始密码"><ElInput v-model="form.password" type="password" /></ElFormItem>
      <ElFormItem label="角色">
        <ElSelect v-model="form.role_ids" multiple>
          <ElOption v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
        </ElSelect>
      </ElFormItem>
    </ElForm>
    <template #footer><ElButton type="primary" @click="create">创建</ElButton></template>
  </ElDialog>
</template>

<style scoped>
.count {
  margin-top: 16px;
  color: #667085;
  font-size: 13px;
}
</style>

