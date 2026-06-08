<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { tokenStorage } from '@/services/http'

const auth = useAuthStore()
onMounted(() => {
  if (tokenStorage.accessToken) auth.fetchCurrentUser().catch(() => undefined)
})
</script>

<template>
  <RouterView />
</template>

