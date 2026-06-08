<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '@/services/admin'
import type { ResourceGrant } from '@/types'

const grants = shallowRef<ResourceGrant[]>([])
const dialogOpen = shallowRef(false)
const form = reactive({
  subject_type: 'role',
  subject_id: 0,
  resource_type: 'space',
  resource_id: '*',
  action: 'view',
  effect: 'allow',
})

async function load() {
  grants.value = await adminApi.grants()
}

async function create() {
  await adminApi.createGrant(form)
  ElMessage.success('数据权限已添加')
  dialogOpen.value = false
  await load()
}

async function remove(grant: ResourceGrant) {
  await ElMessageBox.confirm('确定删除该数据权限吗？', '确认')
  await adminApi.deleteGrant(grant.id)
  await load()
}

onMounted(load)
</script>

<template>
  <ElCard class="page-card">
    <div class="page-header">
      <h1 class="page-title">数据权限</h1>
      <ElButton type="primary" @click="dialogOpen = true">添加授权</ElButton>
    </div>
    <ElTable :data="grants">
      <ElTableColumn prop="subject_type" label="主体类型" />
      <ElTableColumn prop="subject_id" label="主体 ID" />
      <ElTableColumn prop="resource_type" label="资源类型" />
      <ElTableColumn prop="resource_id" label="资源 ID" />
      <ElTableColumn prop="action" label="操作" />
      <ElTableColumn prop="effect" label="效果" />
      <ElTableColumn label="管理" width="100">
        <template #default="{ row }: { row: ResourceGrant }">
          <ElButton link type="danger" @click="remove(row)">删除</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </ElCard>

  <ElDialog v-model="dialogOpen" title="添加数据授权" width="520px">
    <ElForm label-width="100px">
      <ElFormItem label="主体类型">
        <ElSelect v-model="form.subject_type">
          <ElOption label="用户" value="user" />
          <ElOption label="角色" value="role" />
          <ElOption label="部门" value="department" />
        </ElSelect>
      </ElFormItem>
      <ElFormItem label="主体 ID"><ElInputNumber v-model="form.subject_id" :min="1" /></ElFormItem>
      <ElFormItem label="资源类型">
        <ElSelect v-model="form.resource_type">
          <ElOption label="知识空间" value="space" />
          <ElOption label="项目" value="project" />
          <ElOption label="文档" value="document" />
        </ElSelect>
      </ElFormItem>
      <ElFormItem label="资源 ID"><ElInput v-model="form.resource_id" /></ElFormItem>
      <ElFormItem label="动作"><ElInput v-model="form.action" /></ElFormItem>
      <ElFormItem label="效果">
        <ElRadioGroup v-model="form.effect">
          <ElRadio value="allow">允许</ElRadio>
          <ElRadio value="deny">拒绝</ElRadio>
        </ElRadioGroup>
      </ElFormItem>
    </ElForm>
    <template #footer><ElButton type="primary" @click="create">添加</ElButton></template>
  </ElDialog>
</template>

