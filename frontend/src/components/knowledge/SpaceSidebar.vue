<script setup lang="ts">
import { computed, reactive, shallowRef } from 'vue'
import { Delete, Edit, FolderAdd, MoreFilled, Plus } from '@element-plus/icons-vue'
import { useI18n } from '@/composables/useI18n'
import type { Category, KnowledgeSpace } from '@/types'

const props = defineProps<{
  spaces: readonly KnowledgeSpace[]
  categories: readonly Category[]
  selectedSpaceId: number | null
  selectedCategoryId: number | null
}>()

const emit = defineEmits<{
  selectSpace: [spaceId: number]
  selectCategory: [categoryId: number | null]
  createSpace: [payload: Record<string, unknown>]
  updateSpace: [space: KnowledgeSpace, payload: Record<string, unknown>]
  deleteSpace: [space: KnowledgeSpace]
  createCategory: [payload: Record<string, unknown>]
  updateCategory: [category: Category, payload: Record<string, unknown>]
  deleteCategory: [category: Category]
}>()

const { t } = useI18n()
const spaceDialog = shallowRef(false)
const categoryDialog = shallowRef(false)
const editingSpace = shallowRef<KnowledgeSpace | null>(null)
const editingCategory = shallowRef<Category | null>(null)
const spaceForm = reactive({
  name: '',
  code: '',
  description: '',
  visibility: 'private',
})
const categoryForm = reactive({ name: '', parent_id: null as number | null, sort: 0 })
const hasSpace = computed(() => Boolean(props.selectedSpaceId))

function submitSpace() {
  if (editingSpace.value) {
    emit('updateSpace', editingSpace.value, {
      name: spaceForm.name,
      description: spaceForm.description,
      visibility: spaceForm.visibility,
    })
  } else {
    emit('createSpace', { ...spaceForm })
  }
  spaceDialog.value = false
  editingSpace.value = null
  Object.assign(spaceForm, { name: '', code: '', description: '', visibility: 'private' })
}

function openSpace(space: KnowledgeSpace | null = null) {
  editingSpace.value = space
  Object.assign(spaceForm, {
    name: space?.name ?? '',
    code: space?.code ?? '',
    description: space?.description ?? '',
    visibility: space?.visibility ?? 'private',
  })
  spaceDialog.value = true
}

function openCategory(parentId: number | null = null) {
  editingCategory.value = null
  Object.assign(categoryForm, { name: '', parent_id: parentId, sort: 0 })
  categoryDialog.value = true
}

function editCategory(category: Category) {
  editingCategory.value = category
  Object.assign(categoryForm, {
    name: category.name,
    parent_id: category.parent_id,
    sort: category.sort,
  })
  categoryDialog.value = true
}

function submitCategory() {
  if (editingCategory.value) {
    emit('updateCategory', editingCategory.value, { ...categoryForm })
  } else {
    emit('createCategory', { ...categoryForm })
  }
  categoryDialog.value = false
  editingCategory.value = null
}
</script>

<template>
  <aside class="knowledge-sidebar">
    <div class="section-header">
      <span>{{ t('spaces') }}</span>
      <ElButton circle text :icon="Plus" :title="t('createSpace')" @click="openSpace()" />
    </div>
    <div class="space-list">
      <button
        v-for="space in spaces"
        :key="space.id"
        class="space-item"
        :class="{ active: space.id === selectedSpaceId }"
        type="button"
        @click="emit('selectSpace', space.id)"
      >
        <span class="space-dot"></span>
        <span class="space-copy">
          <strong>{{ space.name }}</strong>
          <small>{{ space.code }}</small>
        </span>
        <ElDropdown trigger="click" @click.stop>
          <ElButton class="space-menu" circle text :icon="MoreFilled" />
          <template #dropdown>
            <ElDropdownMenu>
              <ElDropdownItem :icon="Edit" @click="openSpace(space)">{{ t('edit') }}</ElDropdownItem>
              <ElDropdownItem :icon="Delete" divided @click="emit('deleteSpace', space)">
                {{ t('delete') }}
              </ElDropdownItem>
            </ElDropdownMenu>
          </template>
        </ElDropdown>
      </button>
      <ElEmpty v-if="!spaces.length" :image-size="54" :description="t('noSpaces')" />
    </div>

    <div class="section-header category-heading">
      <span>{{ t('categories') }}</span>
      <ElButton
        circle
        text
        :disabled="!hasSpace"
        :icon="FolderAdd"
        :title="t('createCategory')"
        @click="openCategory()"
      />
    </div>
    <button
      class="all-documents"
      :class="{ active: selectedCategoryId === null }"
      type="button"
      @click="emit('selectCategory', null)"
    >
      {{ t('allDocuments') }}
    </button>
    <ElTree
      class="category-tree"
      :data="categories"
      node-key="id"
      default-expand-all
      highlight-current
      :current-node-key="selectedCategoryId ?? undefined"
      :props="{ label: 'name', children: 'children' }"
      @node-click="(node: Category) => emit('selectCategory', node.id)"
    >
      <template #default="{ data }: { data: Category }">
        <span class="tree-node">
          <span>{{ data.name }}</span>
          <ElButton
            class="child-button"
            circle
            text
            :icon="Plus"
            :title="t('addChildCategory')"
            @click.stop="openCategory(data.id)"
          />
          <ElButton
            class="child-button"
            circle
            text
            :icon="Edit"
            :title="t('editCategory')"
            @click.stop="editCategory(data)"
          />
          <ElButton
            class="child-button"
            circle
            text
            type="danger"
            :icon="Delete"
            :title="t('deleteCategory')"
            @click.stop="emit('deleteCategory', data)"
          />
        </span>
      </template>
    </ElTree>

    <ElDialog
      v-model="spaceDialog"
      :title="editingSpace ? t('editSpace') : t('createSpace')"
      width="500px"
    >
      <ElForm label-position="top">
        <ElFormItem :label="t('spaceName')"><ElInput v-model="spaceForm.name" /></ElFormItem>
        <ElFormItem :label="t('spaceCode')">
          <ElInput v-model="spaceForm.code" :disabled="Boolean(editingSpace)" />
        </ElFormItem>
        <ElFormItem :label="t('description')">
          <ElInput v-model="spaceForm.description" type="textarea" :rows="3" />
        </ElFormItem>
        <ElFormItem :label="t('visibility')">
          <ElRadioGroup v-model="spaceForm.visibility">
            <ElRadio value="private">{{ t('private') }}</ElRadio>
            <ElRadio value="department">{{ t('department') }}</ElRadio>
            <ElRadio value="public">{{ t('public') }}</ElRadio>
          </ElRadioGroup>
        </ElFormItem>
      </ElForm>
      <template #footer><ElButton type="primary" @click="submitSpace">{{ t('save') }}</ElButton></template>
    </ElDialog>

    <ElDialog
      v-model="categoryDialog"
      :title="editingCategory ? t('editCategory') : t('createCategory')"
      width="460px"
    >
      <ElForm label-position="top">
        <ElFormItem :label="t('name')"><ElInput v-model="categoryForm.name" /></ElFormItem>
        <ElFormItem :label="t('sort')"><ElInputNumber v-model="categoryForm.sort" :min="0" /></ElFormItem>
      </ElForm>
      <template #footer><ElButton type="primary" @click="submitCategory">{{ t('save') }}</ElButton></template>
    </ElDialog>
  </aside>
</template>

<style scoped>
.knowledge-sidebar {
  min-height: calc(100vh - 134px);
  padding: 18px 14px;
  border-right: 1px solid var(--ks-border);
  background: #f5f8f6;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px 10px;
  color: #4f655b;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.category-heading {
  margin-top: 24px;
}

.space-list {
  display: grid;
  gap: 6px;
}

.space-item,
.all-documents {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 12px;
  border: 0;
  border-radius: 10px;
  color: #2f493e;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.space-item:hover,
.space-item.active,
.all-documents:hover,
.all-documents.active {
  color: #0b5d47;
  background: #dff1ea;
}

.space-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--ks-primary);
  box-shadow: 0 0 0 4px rgb(8 127 97 / 10%);
}

.space-copy {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 2px;
}

.space-menu {
  flex: 0 0 auto;
  opacity: 0;
}

.space-item:hover .space-menu,
.space-item.active .space-menu {
  opacity: 1;
}

.space-item small {
  color: #687c72;
}

.all-documents {
  margin-bottom: 5px;
  font-weight: 600;
}

.category-tree {
  color: #304a3f;
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: 38px;
  border-radius: 8px;
}

:deep(.el-tree-node__content:hover),
:deep(.el-tree--highlight-current .el-tree-node.is-current > .el-tree-node__content) {
  color: #0b5d47;
  background: #dff1ea;
}

.tree-node {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tree-node > span:first-child {
  flex: 1;
}

.child-button {
  opacity: 0;
}

.tree-node:hover .child-button {
  opacity: 1;
}
</style>
