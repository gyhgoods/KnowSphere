<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/services/admin'
import type { Department } from '@/types'

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
  ElMessage.success('部门已创建')
  dialogOpen.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <ElCard class="page-card">
    <div class="page-header">
      <h1 class="page-title">部门管理</h1>
      <ElButton type="primary" @click="openCreate()">新建部门</ElButton>
    </div>
    <ElTable
      :data="departments"
      row-key="id"
      default-expand-all
      :tree-props="{ children: 'children' }"
    >
      <ElTableColumn prop="name" label="部门名称" />
      <ElTableColumn prop="sort" label="排序" width="100" />
      <ElTableColumn label="状态" width="120">
        <template #default="{ row }: { row: Department }">
          <ElTag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '停用' }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn label="操作" width="140">
        <template #default="{ row }: { row: Department }">
          <ElButton link type="primary" @click="openCreate(row.id)">添加子部门</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </ElCard>

  <ElDialog v-model="dialogOpen" title="新建部门" width="480px">
    <ElForm label-width="80px">
      <ElFormItem label="名称"><ElInput v-model="form.name" /></ElFormItem>
      <ElFormItem label="排序"><ElInputNumber v-model="form.sort" :min="0" /></ElFormItem>
    </ElForm>
    <template #footer><ElButton type="primary" @click="create">创建</ElButton></template>
  </ElDialog>
</template>

