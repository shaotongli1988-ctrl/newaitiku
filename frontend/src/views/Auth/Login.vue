<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../stores/userStore.js'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loginForm = reactive({
  phone: '',
  password: '',
})
const submitting = ref(false)
const currentPath = computed(() => String(route.path || ''))
const initialRedirectPath = ref('')

function resolveCurrentEntryType() {
  const loginRedirectPath = resolveLocationRedirectPath()
  if (loginRedirectPath.startsWith('/teacher') || loginRedirectPath.startsWith('/admin')) {
    return 'teacher'
  }
  if (loginRedirectPath.startsWith('/student')) {
    return 'student'
  }
  const normalized = String(window.__QB_ENTRY_TYPE__ || '').trim()
  if (normalized === 'student' || normalized === 'teacher') {
    return normalized
  }
  return ''
}

function shouldUseFullPageRedirect(targetPath, role) {
  const normalizedTargetPath = String(targetPath || '').trim()
  const entryType = resolveCurrentEntryType()
  const normalizedRole = String(role || '').trim()
  if (!normalizedTargetPath || !entryType) {
    return false
  }
  if (entryType === 'student' && normalizedRole !== 'student') {
    return true
  }
  if (entryType === 'teacher' && normalizedRole === 'student') {
    return true
  }
  return false
}

function resolvePostLoginPath() {
  const roleHomePath = String(userStore.homePath || '').trim() || '/student/home'
  const requestedRedirectPath = resolveRequestedRedirectPath()
  if (!requestedRedirectPath) {
    return roleHomePath
  }
  if (shouldUseFullPageRedirect(requestedRedirectPath, userStore.role)) {
    return roleHomePath
  }
  return requestedRedirectPath
}

function normalizeRedirectPath(rawRedirectPath) {
  const redirectPath = String(Array.isArray(rawRedirectPath) ? rawRedirectPath[0] : rawRedirectPath || '').trim()
  if (!redirectPath) {
    return ''
  }
  if (!redirectPath.startsWith('/') || redirectPath.startsWith('//')) {
    return ''
  }
  if (redirectPath.startsWith('/login')) {
    return ''
  }
  return redirectPath
}

function resolveLocationRedirectPath() {
  if (typeof window === 'undefined') {
    return ''
  }
  const params = new URLSearchParams(window.location.search)
  return normalizeRedirectPath(params.get('redirect'))
}

const redirectPath = computed(() => normalizeRedirectPath(route.query.redirect) || resolveLocationRedirectPath())
initialRedirectPath.value = redirectPath.value

function resolveRequestedRedirectPath() {
  const currentRedirectPath = String(redirectPath.value || '').trim()
  if (currentRedirectPath) {
    initialRedirectPath.value = currentRedirectPath
    return currentRedirectPath
  }
  return String(initialRedirectPath.value || '').trim()
}

async function submitLogin() {
  if (submitting.value) {
    return
  }
  const normalizedPhone = String(loginForm.phone || '').trim()
  const normalizedPassword = String(loginForm.password || '').trim()
  if (!normalizedPhone) {
    ElMessage.error('手机号不能为空。')
    return
  }
  if (normalizedPhone.length !== 11) {
    ElMessage.error('手机号长度必须为 11 位。')
    return
  }
  if (!normalizedPassword) {
    ElMessage.error('密码不能为空。')
    return
  }
  if (normalizedPassword.length < 6 || normalizedPassword.length > 64) {
    ElMessage.error('密码长度需在 6 到 64 位之间。')
    return
  }
  submitting.value = true
  try {
    const requestedRedirectPath = resolveRequestedRedirectPath()
    await userStore.login({
      phone: normalizedPhone,
      password: normalizedPassword,
      routePath: requestedRedirectPath || currentPath.value || '/login',
    })
    ElMessage.success('登录成功，正在跳转...')
    const nextPath = resolvePostLoginPath()
    if (requestedRedirectPath || shouldUseFullPageRedirect(nextPath, userStore.role)) {
      window.location.assign(nextPath)
      return
    }
    await router.replace(nextPath)
  } catch (error) {
    const message = String(error?.response?.data?.message || error?.message || '登录失败，请稍后重试。')
    if (!message.includes('字段 [') && !message.includes('角色不合法')) {
      ElMessage.error(message)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="login-shell">
    <article class="login-card">
      <header>
        <h2>账号登录</h2>
        <p>登录后会自动跳转到你请求的业务页面。</p>
      </header>

      <el-form label-position="top" @submit.prevent>
        <el-form-item label="手机号">
          <el-input
            v-model="loginForm.phone"
            maxlength="11"
            placeholder="请输入 11 位手机号"
            @keyup.enter="submitLogin"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="loginForm.password"
            type="password"
            show-password
            placeholder="请输入密码"
            @keyup.enter="submitLogin"
          />
        </el-form-item>
        <el-button type="primary" :loading="submitting" @click="submitLogin">登录并继续</el-button>
      </el-form>
    </article>

  </section>
</template>

<style scoped>
.login-shell {
  min-height: 100vh;
  padding: 24px;
  display: grid;
  gap: 16px;
  align-content: start;
  background: linear-gradient(180deg, var(--qb-primary-soft-bg) 0%, var(--qb-primary-soft-bg) 100%);
}

.login-card {
  width: min(540px, 100%);
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 14px;
  background: var(--qb-bg-card);
  padding: 18px;
}

.login-card h2,
.login-card p {
  margin: 0;
}

.login-card p {
  margin-top: 8px;
  color: var(--qb-text-subtle-7);
}
</style>
