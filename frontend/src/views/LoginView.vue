<script setup lang="ts">
import { computed, reactive, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Lock, Right, User } from '@element-plus/icons-vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const submitting = shallowRef(false)
const language = shallowRef<'zh' | 'en'>('zh')
const errorMessage = shallowRef('')
const form = reactive({ username: '', password: '' })

const copy = computed(() =>
  language.value === 'zh'
    ? {
        language: '中文',
        eyebrow: '企业知识操作系统',
        headline: '让企业的每一份知识，都清晰可发现',
        summary: '统一管理文档、权限、搜索与 AI 答案，打造可信、可追溯的知识工作空间。',
        features: [
          ['统一知识治理', '空间、版本与全生命周期管理'],
          ['可信 AI 答案', '每个答案都包含经过授权的引用来源'],
          ['企业级权限', '部门、项目与文档级访问控制'],
        ],
        signIn: '登录',
        register: '注册',
        welcome: '欢迎回来',
        subtitle: '登录以访问您的企业知识工作空间',
        username: '用户名',
        password: '密码',
        submit: '登录',
        noAccount: '初次使用？',
        demo: '演示账号：admin / ChangeMe123!',
        invalid: '用户名或密码错误',
        unavailable: '无法连接知识服务，请确认后端已启动',
      }
    : {
        language: 'EN',
        eyebrow: 'ENTERPRISE KNOWLEDGE OS',
        headline: 'Make every piece of enterprise knowledge discoverable',
        summary: 'Unify documents, permissions, search, and AI answers in one trusted workspace.',
        features: [
          ['Unified governance', 'Spaces, versions, and lifecycle management'],
          ['Trusted AI answers', 'Every answer includes authorized citations'],
          ['Enterprise permissions', 'Department, project, and document access control'],
        ],
        signIn: 'Sign in',
        register: 'Register',
        welcome: 'Welcome back',
        subtitle: 'Sign in to access your enterprise knowledge workspace',
        username: 'Username',
        password: 'Password',
        submit: 'Sign in',
        noAccount: 'New to the platform?',
        demo: 'Demo: admin / ChangeMe123!',
        invalid: 'Incorrect username or password',
        unavailable: 'Unable to connect to the knowledge service',
      },
)

async function submit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    await auth.login(form.username, form.password)
    await router.push(String(route.query.redirect ?? '/'))
  } catch (error) {
    errorMessage.value =
      axios.isAxiosError(error) && error.response ? copy.value.invalid : copy.value.unavailable
  } finally {
    submitting.value = false
  }
}

function toggleLanguage() {
  language.value = language.value === 'zh' ? 'en' : 'zh'
}
</script>

<template>
  <main class="login-page">
    <section class="story-panel">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32">
            <path d="M16 4l1.7 6.3L24 12l-6.3 1.7L16 20l-1.7-6.3L8 12l6.3-1.7L16 4Z" />
            <path d="M24.5 19l1 3.5 3.5 1-3.5 1-1 3.5-1-3.5-3.5-1 3.5-1 1-3.5Z" />
            <circle cx="7" cy="23" r="2" />
          </svg>
        </span>
        <strong>KnowSphere</strong>
      </div>

      <div class="story-content">
        <p class="eyebrow">{{ copy.eyebrow }}</p>
        <h1>{{ copy.headline }}</h1>
        <p class="story-summary">{{ copy.summary }}</p>

        <div class="feature-list">
          <article v-for="(feature, index) in copy.features" :key="feature[0]" class="feature">
            <span class="feature-icon" aria-hidden="true">
              <svg v-if="index === 0" viewBox="0 0 24 24">
                <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z" />
                <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z" />
              </svg>
              <svg v-else-if="index === 1" viewBox="0 0 24 24">
                <path d="M12 2l1.4 5.6L19 9l-5.6 1.4L12 16l-1.4-5.6L5 9l5.6-1.4L12 2Z" />
                <path d="M19 15l.8 3.2L23 19l-3.2.8L19 23l-.8-3.2L15 19l3.2-.8L19 15Z" />
              </svg>
              <svg v-else viewBox="0 0 24 24">
                <path d="m5 12 4 4L19 6" />
              </svg>
            </span>
            <span>
              <strong>{{ feature[0] }}</strong>
              <small>{{ feature[1] }}</small>
            </span>
          </article>
        </div>
      </div>
    </section>

    <section class="form-panel">
      <button class="language-button" type="button" @click="toggleLanguage">
        <span aria-hidden="true">文A</span>
        {{ copy.language }}
      </button>

      <div class="login-card">
        <div class="auth-tabs">
          <button class="auth-tab active" type="button">{{ copy.signIn }}</button>
          <button class="auth-tab" type="button" disabled>{{ copy.register }}</button>
        </div>

        <div class="form-content">
          <h2>{{ copy.welcome }}</h2>
          <p class="form-subtitle">{{ copy.subtitle }}</p>

          <ElForm label-position="top" @submit.prevent="submit">
            <ElFormItem :label="copy.username">
              <ElInput
                v-model="form.username"
                size="large"
                autocomplete="username"
                :prefix-icon="User"
                placeholder="admin"
              />
            </ElFormItem>
            <ElFormItem :label="copy.password">
              <ElInput
                v-model="form.password"
                size="large"
                type="password"
                show-password
                autocomplete="current-password"
                :prefix-icon="Lock"
                placeholder="••••••••"
                @keyup.enter="submit"
              />
            </ElFormItem>

            <div v-if="errorMessage" class="login-error" role="alert">
              {{ errorMessage }}
            </div>

            <ElButton
              class="submit"
              type="primary"
              size="large"
              :loading="submitting"
              @click="submit"
            >
              {{ copy.submit }}
              <ElIcon class="submit-icon"><Right /></ElIcon>
            </ElButton>
          </ElForm>

          <p class="register-hint">
            {{ copy.noAccount }}
            <span>{{ copy.register }}</span>
          </p>
          <p class="demo-account">{{ copy.demo }}</p>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(520px, 56%) minmax(480px, 44%);
  background: var(--ks-canvas);
}

.story-panel {
  min-height: 100vh;
  padding: 26px 44px;
  color: white;
  background:
    radial-gradient(circle at 76% 18%, rgb(50 132 106 / 16%), transparent 30%),
    #102a21;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 25px;
}

.brand-mark {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #17392e;
  background: var(--ks-mint);
}

.brand-mark svg {
  width: 30px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.story-content {
  width: min(650px, 80%);
  margin: clamp(120px, 17vh, 210px) auto 0;
}

.eyebrow {
  margin: 0 0 32px;
  color: var(--ks-mint);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.story-content h1 {
  margin: 0;
  font-size: clamp(46px, 4.1vw, 72px);
  line-height: 1.14;
  letter-spacing: -0.035em;
}

.story-summary {
  margin: 34px 0 0;
  color: #b7cec5;
  font-size: 19px;
  line-height: 1.8;
}

.feature-list {
  display: grid;
  gap: 22px;
  margin-top: 54px;
}

.feature {
  display: flex;
  align-items: center;
  gap: 15px;
}

.feature-icon {
  flex: 0 0 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border: 1px solid #315c4d;
  border-radius: 12px;
  color: var(--ks-mint);
  background: #17392e;
}

.feature-icon svg {
  width: 25px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.feature span:last-child {
  display: grid;
  gap: 5px;
}

.feature strong {
  font-size: 16px;
}

.feature small {
  color: #7eaa9b;
  font-size: 13px;
}

.form-panel {
  position: relative;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 80px 7vw;
  background:
    radial-gradient(circle at 52% 49%, rgb(181 205 195 / 32%), transparent 34%),
    #f1f5f2;
}

.language-button {
  position: absolute;
  top: 26px;
  right: 46px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 12px 16px;
  border: 1px solid #d2ddd7;
  border-radius: 11px;
  color: #42584f;
  background: rgb(255 255 255 / 78%);
  cursor: pointer;
}

.login-card {
  width: min(650px, 100%);
  overflow: hidden;
  border: 1px solid #dce4df;
  border-radius: 13px;
  background: white;
  box-shadow: 0 28px 70px rgb(19 52 41 / 16%);
}

.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 32px 38px 0;
}

.auth-tab {
  height: 58px;
  border: 0;
  border-bottom: 1px solid #dbe2de;
  color: #718078;
  background: transparent;
  font-size: 17px;
  font-weight: 700;
}

.auth-tab.active {
  border-bottom: 3px solid var(--ks-primary);
  color: var(--ks-ink);
}

.form-content {
  padding: 38px;
}

.form-content h2 {
  margin: 0;
  color: #10251e;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 34px;
}

.form-subtitle {
  margin: 12px 0 28px;
  color: var(--ks-muted);
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  color: #24372f;
  font-weight: 700;
}

:deep(.el-input__wrapper) {
  min-height: 58px;
  padding: 0 17px;
  border-radius: 11px;
  box-shadow: 0 0 0 1px #d7e0db inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--ks-primary) inset;
}

:deep(.el-input__prefix) {
  margin-right: 10px;
  color: #91a198;
  font-size: 21px;
}

.login-error {
  margin: -2px 0 22px;
  padding: 13px 15px;
  border-left: 3px solid var(--ks-danger);
  color: var(--ks-danger);
  background: #fff0ed;
  font-size: 13px;
}

.submit {
  width: 100%;
  height: 58px;
  margin-top: 2px;
  border-radius: 10px;
  font-size: 18px;
  font-weight: 800;
}

.submit-icon {
  margin-left: 10px;
}

.register-hint,
.demo-account {
  margin: 24px 0 0;
  text-align: center;
  color: #819087;
  font-size: 13px;
}

.register-hint span {
  margin-left: 5px;
  color: var(--ks-primary);
  font-weight: 800;
}

.demo-account {
  margin-top: 14px;
  color: #a1aba5;
}

@media (max-width: 1050px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .story-panel {
    min-height: auto;
    padding-bottom: 70px;
  }

  .story-content {
    width: min(720px, 92%);
    margin-top: 80px;
  }

  .form-panel {
    min-height: 760px;
  }
}

@media (max-width: 640px) {
  .story-panel {
    padding: 22px;
  }

  .story-content {
    width: 100%;
    margin-top: 70px;
  }

  .story-content h1 {
    font-size: 40px;
  }

  .form-panel {
    min-height: 700px;
    padding: 90px 18px 40px;
  }

  .language-button {
    right: 18px;
  }

  .auth-tabs {
    padding-inline: 24px;
  }

  .form-content {
    padding: 30px 24px;
  }
}
</style>
