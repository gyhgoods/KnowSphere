<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from '@/composables/useI18n'
import { adminApi } from '@/services/admin'
import type { Permission, Role } from '@/types'

const { t } = useI18n()
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
  ElMessage.success(t('roleSaved'))
  dialogOpen.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <ElCard class="page-card">
    <div class="page-header">
      <h1 class="page-title">{{ t('rolePermissions') }}</h1>
      <ElButton type="primary" @click="openCreate">{{ t('createRole') }}</ElButton>
    </div>
    <ElTable :data="roles">
      <ElTableColumn prop="code" :label="t('code')" />
      <ElTableColumn prop="name" :label="t('name')" />
      <ElTableColumn :label="t('permissions')">
        <template #default="{ row }: { row: Role }">
          {{ row.permissions.map((item) => item.name).join(', ') || '-' }}
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('actions')" width="100">
        <template #default="{ row }: { row: Role }">
          <ElButton link type="primary" @click="openEdit(row)">{{ t('edit') }}</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </ElCard>

  <ElDialog v-model="dialogOpen" :title="t('roleConfig')" width="560px">
    <ElForm label-width="100px">
      <ElFormItem :label="t('code')">
        <ElInput v-model="form.code" :disabled="Boolean(editingId)" />
      </ElFormItem>
      <ElFormItem :label="t('name')"><ElInput v-model="form.name" /></ElFormItem>
      <ElFormItem :label="t('description')">
        <ElInput v-model="form.description" type="textarea" />
      </ElFormItem>
      <ElFormItem :label="t('permissions')">
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
    <template #footer>
      <ElButton type="primary" @click="save">{{ t('save') }}</ElButton>
    </template>
  </ElDialog>
</template>
