<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from '@/composables/useI18n'
import { adminApi } from '@/services/admin'
import type { Department } from '@/types'

const { t } = useI18n()
const departments = shallowRef<Department[]>([])
const dialogOpen = shallowRef(false)
const form = reactive({ name: '', parent_id: null as number | null, sort: 0 })

async function load() {
  departments.value = await adminApi.departments()
}

function openCreate(parentId: number | null = null) {
  Object.assign(form, { name: '', parent_id: parentId, sort: 0 })
  dialogOpen.value = true
}

async function create() {
  await adminApi.createDepartment(form)
  ElMessage.success(t('departmentCreated'))
  dialogOpen.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <ElCard class="page-card">
    <div class="page-header">
      <h1 class="page-title">{{ t('departmentManagement') }}</h1>
      <ElButton type="primary" @click="openCreate()">{{ t('createDepartment') }}</ElButton>
    </div>
    <ElTable
      :data="departments"
      row-key="id"
      default-expand-all
      :tree-props="{ children: 'children' }"
    >
      <ElTableColumn prop="name" :label="t('departmentName')" />
      <ElTableColumn prop="sort" :label="t('sort')" width="100" />
      <ElTableColumn :label="t('status')" width="120">
        <template #default="{ row }: { row: Department }">
          <ElTag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? t('enabled') : t('disabled') }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('actions')" width="180">
        <template #default="{ row }: { row: Department }">
          <ElButton link type="primary" @click="openCreate(row.id)">
            {{ t('addChildDepartment') }}
          </ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </ElCard>

  <ElDialog v-model="dialogOpen" :title="t('createDepartment')" width="480px">
    <ElForm label-width="100px">
      <ElFormItem :label="t('name')"><ElInput v-model="form.name" /></ElFormItem>
      <ElFormItem :label="t('sort')">
        <ElInputNumber v-model="form.sort" :min="0" />
      </ElFormItem>
    </ElForm>
    <template #footer>
      <ElButton type="primary" @click="create">{{ t('create') }}</ElButton>
    </template>
  </ElDialog>
</template>
