<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from '@/composables/useI18n'
import { adminApi } from '@/services/admin'
import type { ResourceGrant } from '@/types'

const { t } = useI18n()
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
  ElMessage.success(t('grantAdded'))
  dialogOpen.value = false
  await load()
}

async function remove(grant: ResourceGrant) {
  await ElMessageBox.confirm(t('deleteGrantConfirm'), t('confirm'))
  await adminApi.deleteGrant(grant.id)
  await load()
}

onMounted(load)
</script>

<template>
  <ElCard class="page-card">
    <div class="page-header">
      <h1 class="page-title">{{ t('dataPermissions') }}</h1>
      <ElButton type="primary" @click="dialogOpen = true">{{ t('addGrant') }}</ElButton>
    </div>
    <ElTable :data="grants">
      <ElTableColumn prop="subject_type" :label="t('subjectType')" />
      <ElTableColumn prop="subject_id" :label="t('subjectId')" />
      <ElTableColumn prop="resource_type" :label="t('resourceType')" />
      <ElTableColumn prop="resource_id" :label="t('resourceId')" />
      <ElTableColumn prop="action" :label="t('action')" />
      <ElTableColumn prop="effect" :label="t('effect')" />
      <ElTableColumn :label="t('manage')" width="100">
        <template #default="{ row }: { row: ResourceGrant }">
          <ElButton link type="danger" @click="remove(row)">{{ t('delete') }}</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </ElCard>

  <ElDialog v-model="dialogOpen" :title="t('addDataGrant')" width="520px">
    <ElForm label-width="120px">
      <ElFormItem :label="t('subjectType')">
        <ElSelect v-model="form.subject_type">
          <ElOption :label="t('user')" value="user" />
          <ElOption :label="t('role')" value="role" />
          <ElOption :label="t('department')" value="department" />
        </ElSelect>
      </ElFormItem>
      <ElFormItem :label="t('subjectId')">
        <ElInputNumber v-model="form.subject_id" :min="1" />
      </ElFormItem>
      <ElFormItem :label="t('resourceType')">
        <ElSelect v-model="form.resource_type">
          <ElOption :label="t('space')" value="space" />
          <ElOption :label="t('project')" value="project" />
          <ElOption :label="t('document')" value="document" />
        </ElSelect>
      </ElFormItem>
      <ElFormItem :label="t('resourceId')"><ElInput v-model="form.resource_id" /></ElFormItem>
      <ElFormItem :label="t('action')"><ElInput v-model="form.action" /></ElFormItem>
      <ElFormItem :label="t('effect')">
        <ElRadioGroup v-model="form.effect">
          <ElRadio value="allow">{{ t('allow') }}</ElRadio>
          <ElRadio value="deny">{{ t('deny') }}</ElRadio>
        </ElRadioGroup>
      </ElFormItem>
    </ElForm>
    <template #footer>
      <ElButton type="primary" @click="create">{{ t('create') }}</ElButton>
    </template>
  </ElDialog>
</template>
