<script setup lang="ts">
import { useI18n } from '@/composables/useI18n'
import type { GraphRelation } from '@/types'

defineProps<{ relations: readonly GraphRelation[] }>()
const { t } = useI18n()
</script>

<template>
  <section class="relations">
    <h3>{{ t('relationships') }}</h3>
    <ElEmpty v-if="!relations.length" :description="t('emptyGraph')" />
    <article v-for="relation in relations" :key="relation.id" class="relation-card">
      <strong>{{ relation.source_name }} → {{ relation.target_name }}</strong>
      <p>{{ relation.relation_type }} · {{ relation.document_title }}</p>
      <span>{{ t('confidence') }} {{ Math.round(relation.confidence * 100) }}%</span>
    </article>
  </section>
</template>

<style scoped>
.relations {
  padding: 18px;
  border: 1px solid var(--ks-border);
  border-radius: 14px;
  background: #ffffff;
}

.relations h3 {
  margin: 0 0 14px;
}

.relation-card {
  padding: 12px 0;
  border-top: 1px solid #e1e9e5;
}

.relation-card p {
  margin: 6px 0;
  color: var(--ks-muted);
}

.relation-card span {
  color: var(--ks-primary);
  font-size: 12px;
  font-weight: 700;
}
</style>
