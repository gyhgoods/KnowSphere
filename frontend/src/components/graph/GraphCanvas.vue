<script setup lang="ts">
import { computed } from 'vue'
import type { GraphResponse } from '@/types'

const props = defineProps<{ graph: GraphResponse }>()

const nodes = computed(() => {
  const total = Math.max(props.graph.entities.length, 1)
  return props.graph.entities.map((entity, index) => {
    const angle = (Math.PI * 2 * index) / total
    return {
      ...entity,
      x: 360 + Math.cos(angle) * 250,
      y: 220 + Math.sin(angle) * 150,
    }
  })
})

const nodeMap = computed(() => new Map(nodes.value.map((node) => [node.id, node])))
</script>

<template>
  <svg class="graph-canvas" viewBox="0 0 720 440" role="img">
    <line
      v-for="relation in graph.relations"
      :key="relation.id"
      :x1="nodeMap.get(relation.source_entity_id)?.x"
      :y1="nodeMap.get(relation.source_entity_id)?.y"
      :x2="nodeMap.get(relation.target_entity_id)?.x"
      :y2="nodeMap.get(relation.target_entity_id)?.y"
      class="edge"
    />
    <g v-for="node in nodes" :key="node.id">
      <circle :cx="node.x" :cy="node.y" r="34" class="node" />
      <text :x="node.x" :y="node.y + 4" text-anchor="middle" class="node-label">
        {{ node.name.slice(0, 12) }}
      </text>
    </g>
  </svg>
</template>

<style scoped>
.graph-canvas {
  width: 100%;
  min-height: 420px;
  border: 1px solid var(--ks-border);
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 10px 26px rgb(16 42 33 / 7%);
}

.edge {
  stroke: #86a99c;
  stroke-width: 2;
  stroke-opacity: 0.65;
}

.node {
  fill: var(--ks-primary);
  stroke: #d6f3e8;
  stroke-width: 5;
}

.node-label {
  fill: #ffffff;
  font-size: 12px;
  font-weight: 700;
}
</style>
