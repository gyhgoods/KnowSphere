<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from '@/composables/useI18n'

const router = useRouter()
const { t } = useI18n()
</script>

<template>
  <main class="forbidden-page">
    <ElResult icon="warning" :title="t('forbidden')" :sub-title="t('forbiddenDescription')">
      <template #extra>
        <ElButton type="primary" @click="router.back()">{{ t('back') }}</ElButton>
      </template>
    </ElResult>
  </main>
</template>

<style scoped>
.forbidden-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
}
</style>
