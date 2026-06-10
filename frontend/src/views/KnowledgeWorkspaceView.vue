<script setup lang="ts">
import { onMounted, reactive, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import { DocumentAdd, Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DocumentEditorDialog from '@/components/knowledge/DocumentEditorDialog.vue'
import DocumentTable from '@/components/knowledge/DocumentTable.vue'
import DocumentVersionsDialog from '@/components/knowledge/DocumentVersionsDialog.vue'
import FilePanel from '@/components/knowledge/FilePanel.vue'
import SpaceSidebar from '@/components/knowledge/SpaceSidebar.vue'
import { useI18n } from '@/composables/useI18n'
import { useKnowledgeWorkspace } from '@/composables/useKnowledgeWorkspace'
import { knowledgeApi } from '@/services/knowledge'
import type { Category, KnowledgeDocument, KnowledgeSpace } from '@/types'

const workspace = useKnowledgeWorkspace()
const route = useRoute()
const { t } = useI18n()
const editorOpen = shallowRef(false)
const filesOpen = shallowRef(false)
const versionsOpen = shallowRef(false)
const tagDialog = shallowRef(false)
const editingDocument = shallowRef<KnowledgeDocument | null>(null)
const activeDocument = shallowRef<KnowledgeDocument | null>(null)
const tagForm = reactive({ name: '', color: '#087f61' })

onMounted(() =>
  workspace.initialize({
    spaceId: Number(route.query.space_id) || null,
    categoryId: Number(route.query.category_id) || null,
    keyword: typeof route.query.keyword === 'string' ? route.query.keyword : '',
  }),
)

function openCreateDocument() {
  editingDocument.value = null
  editorOpen.value = true
}

async function openEdit(document: KnowledgeDocument) {
  editingDocument.value = await knowledgeApi.document(document.id)
  editorOpen.value = true
}

async function saveDocument(payload: Record<string, unknown>, id: number | null) {
  if (id) {
    await knowledgeApi.updateDocument(id, payload)
    ElMessage.success(t('documentSaved'))
  } else {
    await knowledgeApi.createDocument(payload)
    ElMessage.success(t('draftCreated'))
  }
  editorOpen.value = false
  await workspace.loadDocuments()
}

async function createSpace(payload: Record<string, unknown>) {
  const space = await knowledgeApi.createSpace(payload)
  await workspace.refreshSpaces()
  await workspace.selectSpace(space.id)
  ElMessage.success(t('spaceCreated'))
}

async function updateSpace(space: KnowledgeSpace, payload: Record<string, unknown>) {
  await knowledgeApi.updateSpace(space.id, payload)
  await workspace.refreshSpaces()
  ElMessage.success(t('spaceUpdated'))
}

async function deleteSpace(space: KnowledgeSpace) {
  await ElMessageBox.confirm(t('deleteWarning'), `${t('deleteSpace')}: ${space.name}`, {
    type: 'warning',
    confirmButtonText: t('delete'),
    cancelButtonText: t('cancel'),
  })
  await knowledgeApi.deleteSpace(space.id)
  await workspace.refreshSpaces()
  ElMessage.success(t('spaceDeleted'))
}

async function createCategory(payload: Record<string, unknown>) {
  if (!workspace.selectedSpaceId.value) return
  await knowledgeApi.createCategory(workspace.selectedSpaceId.value, payload)
  await workspace.refreshCategories()
  ElMessage.success(t('categoryCreated'))
}

async function updateCategory(category: Category, payload: Record<string, unknown>) {
  await knowledgeApi.updateCategory(category.id, payload)
  await workspace.refreshCategories()
  ElMessage.success(t('categoryUpdated'))
}

async function deleteCategory(category: Category) {
  await ElMessageBox.confirm(t('deleteWarning'), `${t('deleteCategory')}: ${category.name}`, {
    type: 'warning',
    confirmButtonText: t('delete'),
    cancelButtonText: t('cancel'),
  })
  await knowledgeApi.deleteCategory(category.id)
  if (workspace.selectedCategoryId.value === category.id) {
    await workspace.selectCategory(null)
  }
  await workspace.refreshCategories()
  await workspace.loadDocuments()
  ElMessage.success(t('categoryDeleted'))
}

async function createTag() {
  await knowledgeApi.createTag(tagForm)
  await workspace.refreshTags()
  tagDialog.value = false
  Object.assign(tagForm, { name: '', color: '#087f61' })
  ElMessage.success(t('tagCreated'))
}

async function removeDocument(document: KnowledgeDocument) {
  await ElMessageBox.confirm(`${t('delete')} "${document.title}"?`, t('deleteDocument'), {
    type: 'warning',
  })
  await knowledgeApi.deleteDocument(document.id)
  await workspace.loadDocuments()
}

async function submitDocument(document: KnowledgeDocument) {
  await knowledgeApi.submitDocument(document.id)
  ElMessage.success(t('documentSubmitted'))
  await workspace.loadDocuments()
}

async function reviewDocument(document: KnowledgeDocument) {
  const action = await ElMessageBox.confirm(t('reviewDocument'), t('reviewDocument'), {
    confirmButtonText: t('approve'),
    cancelButtonText: t('reject'),
    distinguishCancelAndClose: true,
    type: 'warning',
  })
    .then(() => 'approve' as const)
    .catch((reason) => {
      if (reason === 'cancel') return 'reject' as const
      return null
    })
  if (!action) return
  let comment = ''
  if (action === 'reject') {
    const result = await ElMessageBox.prompt(t('rejectReason'), t('reject'), {
      inputPattern: /\S+/,
      inputErrorMessage: t('rejectReason'),
    })
    comment = result.value
  }
  await knowledgeApi.reviewDocument(document.id, action, comment)
  ElMessage.success(action === 'approve' ? t('documentPublished') : t('documentRejected'))
  await workspace.loadDocuments()
}

async function archiveDocument(document: KnowledgeDocument) {
  await ElMessageBox.confirm(`${t('archive')} "${document.title}"?`, t('archiveDocument'))
  await knowledgeApi.archiveDocument(document.id)
  await workspace.loadDocuments()
}

function openFiles(document: KnowledgeDocument) {
  activeDocument.value = document
  filesOpen.value = true
}

function openVersions(document: KnowledgeDocument) {
  activeDocument.value = document
  versionsOpen.value = true
}
</script>

<template>
  <section class="workspace-card">
    <SpaceSidebar
      :spaces="workspace.spaces.value"
      :categories="workspace.categories.value"
      :selected-space-id="workspace.selectedSpaceId.value"
      :selected-category-id="workspace.selectedCategoryId.value"
      @select-space="workspace.selectSpace"
      @select-category="workspace.selectCategory"
      @create-space="createSpace"
      @update-space="updateSpace"
      @delete-space="deleteSpace"
      @create-category="createCategory"
      @update-category="updateCategory"
      @delete-category="deleteCategory"
    />

    <main class="document-area">
      <header class="workspace-header">
        <div>
          <p class="eyebrow">KNOWLEDGE WORKSPACE</p>
          <h2>{{ workspace.selectedSpace.value?.name ?? t('knowledgeWorkspace') }}</h2>
          <p class="description">
            {{ workspace.selectedSpace.value?.description ?? t('knowledgeDescription') }}
          </p>
        </div>
        <div class="header-actions">
          <ElButton :icon="Plus" @click="tagDialog = true">{{ t('createTag') }}</ElButton>
          <ElButton
            type="primary"
            :icon="DocumentAdd"
            :disabled="!workspace.selectedSpaceId.value"
            @click="openCreateDocument"
          >
            {{ t('createDocument') }}
          </ElButton>
        </div>
      </header>

      <div class="toolbar">
        <ElInput
          v-model="workspace.keyword.value"
          clearable
          :prefix-icon="Search"
          :placeholder="t('searchDocuments')"
          @keyup.enter="workspace.loadDocuments"
          @clear="workspace.loadDocuments"
        />
        <ElButton @click="workspace.loadDocuments">{{ t('search') }}</ElButton>
        <span class="document-count">{{ t('documentCount', { count: workspace.total.value }) }}</span>
      </div>

      <DocumentTable
        :documents="workspace.documents.value"
        :loading="workspace.loading.value"
        @edit="openEdit"
        @remove="removeDocument"
        @submit="submitDocument"
        @review="reviewDocument"
        @archive="archiveDocument"
        @files="openFiles"
        @versions="openVersions"
      />
    </main>
  </section>

  <DocumentEditorDialog
    v-model="editorOpen"
    :document="editingDocument"
    :spaces="workspace.spaces.value"
    :categories="workspace.categories.value"
    :tags="workspace.tags.value"
    :default-space-id="workspace.selectedSpaceId.value"
    :default-category-id="workspace.selectedCategoryId.value"
    @save="saveDocument"
  />
  <FilePanel v-model="filesOpen" :document="activeDocument" />
  <DocumentVersionsDialog
    v-model="versionsOpen"
    :document="activeDocument"
    @restored="workspace.loadDocuments"
  />

  <ElDialog v-model="tagDialog" :title="t('createTag')" width="440px">
    <ElForm label-position="top">
      <ElFormItem :label="t('name')"><ElInput v-model="tagForm.name" /></ElFormItem>
      <ElFormItem label="Color"><ElColorPicker v-model="tagForm.color" /></ElFormItem>
    </ElForm>
    <template #footer><ElButton type="primary" @click="createTag">{{ t('create') }}</ElButton></template>
  </ElDialog>
</template>

<style scoped>
.workspace-card {
  min-height: calc(100vh - 134px);
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  overflow: hidden;
  border: 1px solid var(--ks-border);
  border-radius: 14px;
  background: white;
  box-shadow: 0 12px 32px rgb(16 42 33 / 10%);
}

.document-area {
  min-width: 0;
  padding: 26px;
}

.workspace-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 22px;
  border-bottom: 1px solid #dce4e0;
}

.eyebrow {
  margin: 0 0 7px;
  color: var(--ks-primary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.workspace-header h2 {
  margin: 0;
  color: var(--ks-ink);
  font-size: 25px;
}

.description {
  margin: 8px 0 0;
  color: #556a61;
}

.header-actions,
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar {
  padding: 20px 0;
}

.toolbar :deep(.el-input) {
  width: min(380px, 45vw);
}

.document-count {
  margin-left: auto;
  color: #60736a;
  font-size: 13px;
}

@media (max-width: 900px) {
  .workspace-card {
    grid-template-columns: 210px minmax(0, 1fr);
  }

  .workspace-header {
    flex-direction: column;
  }
}
</style>
