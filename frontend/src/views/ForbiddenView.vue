<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <main class="forbidden-page">
    <ElResult icon="warning" title="无权访问" sub-title="当前账号没有访问该页面所需的权限">
      <template #extra>
        <ElButton type="primary" @click="router.back()">返回</ElButton>
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
