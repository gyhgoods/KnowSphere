<script setup lang="ts">
import { onMounted } from 'vue'
import en from 'element-plus/es/locale/lang/en'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { computed } from 'vue'
import { useI18n } from '@/composables/useI18n'
import { useAuthStore } from '@/stores/auth'
import { tokenStorage } from '@/services/http'

const auth = useAuthStore()
const { locale } = useI18n()
const elementLocale = computed(() => (locale.value === 'zh' ? zhCn : en))
onMounted(() => {
  if (tokenStorage.accessToken) auth.fetchCurrentUser().catch(() => undefined)
})
</script>

<template>
  <ElConfigProvider :locale="elementLocale">
    <RouterView />
  </ElConfigProvider>
</template>
