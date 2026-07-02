<script setup lang="ts">
import { onMounted } from 'vue'
import GraphCanvas from '@/components/graph/GraphCanvas.vue'
import GraphRelationList from '@/components/graph/GraphRelationList.vue'
import { useI18n } from '@/composables/useI18n'
import { useKnowledgeGraph } from '@/composables/useKnowledgeGraph'

const graph = useKnowledgeGraph()
const { t } = useI18n()

onMounted(graph.initialize)
</script>

<template>
  <main class="graph-view">
    <header class="graph-header">
      <div>
        <p>KNOWLEDGE GRAPH</p>
        <h2>{{ t('knowledgeGraph') }}</h2>
        <span>{{ t('graphDescription') }}</span>
      </div>
      <div class="graph-filters">
        <ElSelect v-model="graph.selectedSpaceId.value" clearable :placeholder="t('allSpaces')">
          <ElOption
            v-for="space in graph.spaces.value"
            :key="space.id"
            :label="space.name"
            :value="space.id"
          />
        </ElSelect>
        <ElSelect v-model="graph.relationFilter.value">
          <ElOption :label="t('allRelationships')" value="all" />
          <ElOption :label="t('strongRelationships')" value="strong" />
        </ElSelect>
        <ElButton type="primary" :loading="graph.loading.value" @click="graph.loadGraph">
          {{ t('refresh') }}
        </ElButton>
      </div>
    </header>
    <ElSkeleton v-if="graph.loading.value" :rows="8" animated />
    <section v-else class="graph-grid">
      <GraphCanvas :graph="graph.graph.value" />
      <GraphRelationList :relations="graph.graph.value.relations" />
    </section>
  </main>
</template>

<style scoped>
.graph-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 20px;
}

.graph-header p {
  margin: 0 0 7px;
  color: var(--ks-primary);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.graph-header h2 {
  margin: 0;
}

.graph-header span {
  display: block;
  margin-top: 8px;
  color: var(--ks-muted);
}

.graph-filters {
  display: flex;
  gap: 10px;
}

.graph-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
}

@media (max-width: 1000px) {
  .graph-header,
  .graph-filters {
    flex-direction: column;
  }

  .graph-grid {
    grid-template-columns: 1fr;
  }
}
</style>
