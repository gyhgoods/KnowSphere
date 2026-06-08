<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/services/admin'
import type { Permission, Role } from '@/types'

const roles = shallowRef<Role[]>([])
const permissions = shallowRef<Permission[]>([])
const dialogOpen = shallowRef(false)
const editingId = shallowRef<number | null>(null)
const form = reactive({ code: '', name: '', description: '', permission_ids: [] as number[] })

async function load() {
  ;[roles.value, permissions.value] = await Promise.all([
    adminApi.roles(),
    adminApi.permissions(),
  ])
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { code: '', name: '', description: '', permission_ids: [] })
  dialogOpen.value = true
}

function openEdit(role: Role) {
  editingId.value = role.id
  Object.assign(form, {
    code: role.code,
    name: role.name,
    description: role.description ?? '',
    permission_ids: role.permissions.map((permission) => permission.id),
  })
  dialogOpen.value = true
}

async function save() {
  if (editingId.value) {
    await adminApi.updateRole(editingId.value, {
      name: form.name,
      description: form.description,
      permission_ids: form.permission_ids,
    })
  } else {
    await adminApi.createRole(form)
  }
  ElMessage.success('角色已保存')
  dialogOpen.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <ElCard class="page-card">
    <div class="page-header">
      <h1 class="page-title">角色权限</h1>
      <ElButton type="primary" @click="openCreate">新建角色</ElButton>
    </div>
    <ElTable :data="roles">
      <ElTableColumn prop="code" label="编码" />
      <ElTableColumn prop="name" label="名称" />
      <ElTableColumn label="权限">
        <template #default="{ row }: { row: Role }">
          {{ row.permissions.map((item) => item.name).join('、') || '-' }}
        </template>
      </ElTableColumn>
      <ElTableColumn label="操作" width="100">
        <template #default="{ row }: { row: Role }">
          <ElButton link type="primary" @click="openEdit(row)">编辑</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </ElCard>

  <ElDialog v-model="dialogOpen" title="角色配置" width="560px">
    <ElForm label-width="80px">
      <ElFormItem label="编码"><ElInput v-model="form.code" :disabled="Boolean(editingId)" /></ElFormItem>
      <ElFormItem label="名称"><ElInput v-model="form.name" /></ElFormItem>
      <ElFormItem label="说明"><ElInput v-model="form.description" type="textarea" /></ElFormItem>
      <ElFormItem label="权限">
        <ElSelect v-model="form.permission_ids" multiple filterable>
          <ElOption
            v-for="permission in permissions"
            :key="permission.id"
            :label="permission.name"
            :value="permission.id"
          />
        </ElSelect>
      </ElFormItem>
    </ElForm>
    <template #footer><ElButton type="primary" @click="save">保存</ElButton></template>
  </ElDialog>
</template>

