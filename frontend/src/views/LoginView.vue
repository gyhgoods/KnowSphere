<script setup lang="ts">
import { reactive, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const submitting = shallowRef(false)
const form = reactive({ username: '', password: '' })

async function submit() {
  submitting.value = true
  try {
    await auth.login(form.username, form.password)
    await router.push(String(route.query.redirect ?? '/'))
  } catch {
    ElMessage.error('用户名或密码错误')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <ElCard class="login-card" shadow="always">
      <div class="identity">
        <h1>KnowSphere</h1>
        <p>企业 AI 知识库</p>
      </div>
      <ElForm label-position="top" @submit.prevent="submit">
        <ElFormItem label="用户名">
          <ElInput v-model="form.username" autocomplete="username" />
        </ElFormItem>
        <ElFormItem label="密码">
          <ElInput
            v-model="form.password"
            type="password"
            show-password
            autocomplete="current-password"
            @keyup.enter="submit"
          />
        </ElFormItem>
        <ElButton class="submit" type="primary" :loading="submitting" @click="submit">
          登录
        </ElButton>
      </ElForm>
    </ElCard>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #edf4ff, #f7f3ff);
}

.login-card {
  width: min(420px, 100%);
  border: 0;
  border-radius: 16px;
}

.identity {
  margin-bottom: 28px;
  text-align: center;
}

.identity h1 {
  margin: 0;
  font-size: 30px;
}

.identity p {
  margin: 8px 0 0;
  color: #667085;
}

.submit {
  width: 100%;
}
</style>

