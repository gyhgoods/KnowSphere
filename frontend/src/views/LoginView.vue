<script setup lang="ts">
import { computed, reactive, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Lock, Right, User } from '@element-plus/icons-vue'
import axios from 'axios'
import { useI18n } from '@/composables/useI18n'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { locale: language, t, toggleLocale } = useI18n()
const submitting = shallowRef(false)
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
  toggleLocale()
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
        <strong>{{ t('brandName') }}</strong>
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
        <svg class="language-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 5h10M9 3v2m3 0c-1 4-3.2 7-6.5 9M7 9c1.3 2 3 3.7 5.3 5" />
          <path d="m14 21 3.2-8 3.3 8m-5.3-3h4.1" />
        </svg>
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
  min-height: 100dvh;
  display: grid;
  grid-template-columns: minmax(0, 56%) minmax(420px, 44%);
  background: #edf3ef;
}

.story-panel {
  min-width: 0;
  min-height: 100vh;
  min-height: 100dvh;
  padding: clamp(22px, 2.3vw, 34px) clamp(28px, 3.5vw, 54px);
  overflow-x: hidden;
  overflow-y: auto;
  color: white;
  background: #112b22;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(22px, 1.7vw, 28px);
}

.brand-mark {
  width: clamp(46px, 3.1vw, 52px);
  height: clamp(46px, 3.1vw, 52px);
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
  width: auto;
  max-width: 650px;
  margin: clamp(72px, 11vh, 132px) 0 48px clamp(42px, 8.5vw, 126px);
}

.eyebrow {
  margin: 0 0 clamp(20px, 3vh, 32px);
  color: var(--ks-mint);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.story-content h1 {
  margin: 0;
  font-size: clamp(40px, 4vw, 68px);
  line-height: 1.14;
  letter-spacing: -0.035em;
}

.story-summary {
  margin: clamp(22px, 3.5vh, 34px) 0 0;
  color: #c5d8d0;
  font-size: clamp(16px, 1.25vw, 19px);
  line-height: 1.8;
}

.feature-list {
  display: grid;
  gap: clamp(14px, 2vh, 22px);
  margin-top: clamp(30px, 5vh, 54px);
}

.feature {
  display: flex;
  align-items: center;
  gap: 15px;
}

.feature-icon {
  flex: 0 0 clamp(44px, 3vw, 50px);
  height: clamp(44px, 3vw, 50px);
  display: grid;
  place-items: center;
  border: 1px solid #386657;
  border-radius: 12px;
  color: var(--ks-mint);
  background: #183c30;
}

.feature-icon svg {
  width: 24px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.9;
}

.feature span:last-child {
  display: grid;
  gap: 5px;
}

.feature strong {
  font-size: 16px;
}

.feature small {
  color: #95b9ac;
  font-size: 13px;
}

.form-panel {
  position: relative;
  min-width: 0;
  min-height: 100vh;
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: clamp(84px, 10vh, 112px) clamp(28px, 6vw, 94px) 48px;
  background: #edf3ef;
}

.language-button {
  position: absolute;
  top: clamp(20px, 2.5vw, 28px);
  right: clamp(22px, 3.8vw, 50px);
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 12px 16px;
  border: 1px solid #c8d4ce;
  border-radius: 11px;
  color: #30483e;
  background: #ffffff;
  box-shadow: 0 2px 8px rgb(17 43 34 / 5%);
  cursor: pointer;
}

.language-icon {
  width: 21px;
  height: 21px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.login-card {
  width: min(650px, 100%);
  overflow: hidden;
  border: 1px solid #ccd7d1;
  border-radius: 13px;
  background: white;
  box-shadow: 0 22px 48px rgb(18 45 36 / 14%);
}

.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: clamp(24px, 3.5vh, 32px) clamp(26px, 3vw, 38px) 0;
}

.auth-tab {
  height: 58px;
  border: 0;
  border-bottom: 1px solid #d3ddd8;
  color: #62736b;
  background: transparent;
  font-size: 17px;
  font-weight: 700;
}

.auth-tab.active {
  border-bottom: 3px solid var(--ks-primary);
  color: var(--ks-ink);
}

.form-content {
  padding: clamp(28px, 4vh, 38px);
}

.form-content h2 {
  margin: 0;
  color: #10251e;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 34px;
}

.form-subtitle {
  margin: 12px 0 28px;
  color: #5d7067;
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
  background: #ffffff;
  box-shadow: 0 0 0 1px #cbd7d1 inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--ks-primary) inset;
}

:deep(.el-input__prefix) {
  margin-right: 10px;
  color: #74887e;
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
  color: #687a71;
  font-size: 13px;
}

.register-hint span {
  margin-left: 5px;
  color: var(--ks-primary);
  font-weight: 800;
}

.demo-account {
  margin-top: 14px;
  color: #7d8c84;
}

@media (max-width: 1120px) {
  .login-page {
    grid-template-columns: 1fr;
  }

  .story-panel {
    min-height: auto;
    padding-bottom: 56px;
  }

  .story-content {
    width: min(720px, 92%);
    margin: 56px auto 0;
  }

  .form-panel {
    min-height: min(760px, 100dvh);
    padding-inline: max(24px, 12vw);
  }
}

@media (max-width: 640px) {
  .story-panel {
    padding: 22px;
  }

  .story-content {
    width: 100%;
    margin: 52px 0 0;
  }

  .story-content h1 {
    font-size: clamp(34px, 10vw, 42px);
  }

  .form-panel {
    min-height: 680px;
    padding: 86px 16px 34px;
  }

  .language-button {
    right: 16px;
  }

  .auth-tabs {
    padding-inline: 24px;
  }

  .form-content {
    padding: 28px 22px;
  }
}

@media (max-height: 760px) and (min-width: 1121px) {
  .story-content {
    margin-top: 48px;
    margin-bottom: 30px;
  }

  .eyebrow {
    margin-bottom: 18px;
  }

  .story-summary {
    margin-top: 20px;
    line-height: 1.6;
  }

  .feature-list {
    gap: 12px;
    margin-top: 26px;
  }

  .form-panel {
    padding-top: 68px;
    padding-bottom: 24px;
  }

  .auth-tabs {
    padding-top: 20px;
  }

  .auth-tab {
    height: 50px;
  }

  .form-content {
    padding-top: 24px;
    padding-bottom: 24px;
  }

  :deep(.el-input__wrapper),
  .submit {
    min-height: 52px;
    height: 52px;
  }
}
</style>
