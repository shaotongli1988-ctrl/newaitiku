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
    <div class="water-ripples">
      <div class="ripple ripple-1"></div>
      <div class="ripple ripple-2"></div>
      <div class="ripple ripple-3"></div>
    </div>
    <div class="willow-tree willow-right">
      <div class="branch branch-1">
        <div class="leaf leaf-1"></div>
        <div class="leaf leaf-2"></div>
        <div class="leaf leaf-3"></div>
      </div>
      <div class="branch branch-2">
        <div class="leaf leaf-4"></div>
        <div class="leaf leaf-5"></div>
        <div class="leaf leaf-6"></div>
      </div>
      <div class="branch branch-3">
        <div class="leaf leaf-7"></div>
        <div class="leaf leaf-8"></div>
        <div class="leaf leaf-9"></div>
      </div>
    </div>
    <div class="willow-tree willow-left">
      <div class="branch branch-left-1">
        <div class="leaf leaf-left-1"></div>
        <div class="leaf leaf-left-2"></div>
        <div class="leaf leaf-left-3"></div>
        <div class="leaf leaf-left-4"></div>
      </div>
      <div class="branch branch-left-2">
        <div class="leaf leaf-left-5"></div>
        <div class="leaf leaf-left-6"></div>
        <div class="leaf leaf-left-7"></div>
        <div class="leaf leaf-left-8"></div>
      </div>
      <div class="branch branch-left-3">
        <div class="leaf leaf-left-9"></div>
        <div class="leaf leaf-left-10"></div>
        <div class="leaf leaf-left-11"></div>
        <div class="leaf leaf-left-12"></div>
      </div>
      <div class="branch branch-left-4">
        <div class="leaf leaf-left-13"></div>
        <div class="leaf leaf-left-14"></div>
        <div class="leaf leaf-left-15"></div>
        <div class="leaf leaf-left-16"></div>
      </div>
    </div>
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
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, var(--qb-primary-soft-bg) 0%, var(--qb-primary-soft-bg) 100%);
}

.water-ripples {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  overflow: hidden;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  border: 2px solid rgba(96, 165, 250, 0.15);
  animation: ripple-effect 4s infinite;
}

.ripple-1 {
  width: 400px;
  height: 400px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 0s;
}

.ripple-2 {
  width: 600px;
  height: 600px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 1s;
}

.ripple-3 {
  width: 800px;
  height: 800px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: 2s;
}

@keyframes ripple-effect {
  0% {
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 0.8;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}

.willow-tree {
  position: absolute;
  pointer-events: none;
  z-index: 0;
}

.willow-right {
  top: 0;
  right: 0;
  width: 400px;
  height: 500px;
}

.willow-left {
  top: 0;
  left: 0;
  width: 500px;
  height: 100%;
}

.branch {
  position: absolute;
  width: 3px;
  background: linear-gradient(180deg, #8B7355 0%, #A0926C 100%);
  border-radius: 2px;
  transform-origin: top center;
}

.branch-1 {
  top: 20px;
  right: 280px;
  height: 200px;
  transform: rotate(15deg);
  animation: branch-sway-1 4s ease-in-out infinite;
}

.branch-2 {
  top: 40px;
  right: 200px;
  height: 250px;
  transform: rotate(5deg);
  animation: branch-sway-2 5s ease-in-out infinite;
}

.branch-3 {
  top: 60px;
  right: 120px;
  height: 220px;
  transform: rotate(-5deg);
  animation: branch-sway-3 4.5s ease-in-out infinite;
}

.branch-left-1 {
  top: 80px;
  left: 100px;
  height: 280px;
  transform: rotate(-20deg);
  animation: branch-left-sway-1 5s ease-in-out infinite;
}

.branch-left-2 {
  top: 150px;
  left: 80px;
  height: 320px;
  transform: rotate(-10deg);
  animation: branch-left-sway-2 5.5s ease-in-out infinite;
}

.branch-left-3 {
  top: 220px;
  left: 60px;
  height: 260px;
  transform: rotate(5deg);
  animation: branch-left-sway-3 4.8s ease-in-out infinite;
}

.branch-left-4 {
  top: 300px;
  left: 90px;
  height: 200px;
  transform: rotate(15deg);
  animation: branch-left-sway-4 4.2s ease-in-out infinite;
}

@keyframes branch-sway-1 {
  0%, 100% {
    transform: rotate(15deg);
  }
  50% {
    transform: rotate(10deg);
  }
}

@keyframes branch-sway-2 {
  0%, 100% {
    transform: rotate(5deg);
  }
  50% {
    transform: rotate(0deg);
  }
}

@keyframes branch-sway-3 {
  0%, 100% {
    transform: rotate(-5deg);
  }
  50% {
    transform: rotate(-10deg);
  }
}

@keyframes branch-left-sway-1 {
  0%, 100% {
    transform: rotate(-20deg);
  }
  50% {
    transform: rotate(-15deg);
  }
}

@keyframes branch-left-sway-2 {
  0%, 100% {
    transform: rotate(-10deg);
  }
  50% {
    transform: rotate(-5deg);
  }
}

@keyframes branch-left-sway-3 {
  0%, 100% {
    transform: rotate(5deg);
  }
  50% {
    transform: rotate(10deg);
  }
}

@keyframes branch-left-sway-4 {
  0%, 100% {
    transform: rotate(15deg);
  }
  50% {
    transform: rotate(20deg);
  }
}

.leaf {
  position: absolute;
  width: 20px;
  height: 8px;
  background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
  border-radius: 50% 0 50% 50%;
  transform-origin: left center;
}

.leaf-1 {
  top: 50px;
  left: -8px;
  transform: rotate(-30deg);
  animation: leaf-sway-1 3s ease-in-out infinite;
}

.leaf-2 {
  top: 100px;
  left: -5px;
  transform: rotate(-45deg);
  animation: leaf-sway-2 3.5s ease-in-out infinite;
}

.leaf-3 {
  top: 150px;
  left: -10px;
  transform: rotate(-25deg);
  animation: leaf-sway-3 2.8s ease-in-out infinite;
}

.leaf-4 {
  top: 60px;
  left: -6px;
  transform: rotate(-35deg);
  animation: leaf-sway-1 3.2s ease-in-out infinite;
}

.leaf-5 {
  top: 120px;
  left: -8px;
  transform: rotate(-40deg);
  animation: leaf-sway-2 3.8s ease-in-out infinite;
}

.leaf-6 {
  top: 180px;
  left: -5px;
  transform: rotate(-30deg);
  animation: leaf-sway-3 3s ease-in-out infinite;
}

.leaf-7 {
  top: 70px;
  left: -7px;
  transform: rotate(-25deg);
  animation: leaf-sway-1 2.9s ease-in-out infinite;
}

.leaf-8 {
  top: 130px;
  left: -9px;
  transform: rotate(-35deg);
  animation: leaf-sway-2 3.3s ease-in-out infinite;
}

.leaf-9 {
  top: 170px;
  left: -6px;
  transform: rotate(-28deg);
  animation: leaf-sway-3 3.6s ease-in-out infinite;
}

.leaf-left-1 {
  top: 60px;
  right: -10px;
  transform: rotate(25deg);
  animation: leaf-left-sway-1 2.8s ease-in-out infinite;
}

.leaf-left-2 {
  top: 120px;
  right: -8px;
  transform: rotate(35deg);
  animation: leaf-left-sway-2 3.2s ease-in-out infinite;
}

.leaf-left-3 {
  top: 180px;
  right: -12px;
  transform: rotate(20deg);
  animation: leaf-left-sway-3 3s ease-in-out infinite;
}

.leaf-left-4 {
  top: 240px;
  right: -6px;
  transform: rotate(40deg);
  animation: leaf-left-sway-1 3.5s ease-in-out infinite;
}

.leaf-left-5 {
  top: 70px;
  right: -9px;
  transform: rotate(30deg);
  animation: leaf-left-sway-2 2.9s ease-in-out infinite;
}

.leaf-left-6 {
  top: 140px;
  right: -11px;
  transform: rotate(45deg);
  animation: leaf-left-sway-3 3.3s ease-in-out infinite;
}

.leaf-left-7 {
  top: 210px;
  right: -7px;
  transform: rotate(28deg);
  animation: leaf-left-sway-1 3.6s ease-in-out infinite;
}

.leaf-left-8 {
  top: 270px;
  right: -10px;
  transform: rotate(38deg);
  animation: leaf-left-sway-2 3.1s ease-in-out infinite;
}

.leaf-left-9 {
  top: 50px;
  right: -8px;
  transform: rotate(22deg);
  animation: leaf-left-sway-3 3.4s ease-in-out infinite;
}

.leaf-left-10 {
  top: 110px;
  right: -11px;
  transform: rotate(32deg);
  animation: leaf-left-sway-1 2.7s ease-in-out infinite;
}

.leaf-left-11 {
  top: 170px;
  right: -9px;
  transform: rotate(42deg);
  animation: leaf-left-sway-2 3.7s ease-in-out infinite;
}

.leaf-left-12 {
  top: 230px;
  right: -7px;
  transform: rotate(26deg);
  animation: leaf-left-sway-3 3.0s ease-in-out infinite;
}

.leaf-left-13 {
  top: 40px;
  right: -10px;
  transform: rotate(33deg);
  animation: leaf-left-sway-1 3.2s ease-in-out infinite;
}

.leaf-left-14 {
  top: 90px;
  right: -8px;
  transform: rotate(43deg);
  animation: leaf-left-sway-2 2.9s ease-in-out infinite;
}

.leaf-left-15 {
  top: 140px;
  right: -12px;
  transform: rotate(24deg);
  animation: leaf-left-sway-3 3.5s ease-in-out infinite;
}

.leaf-left-16 {
  top: 180px;
  right: -6px;
  transform: rotate(37deg);
  animation: leaf-left-sway-1 3.1s ease-in-out infinite;
}

@keyframes leaf-sway-1 {
  0%, 100% {
    transform: rotate(-30deg) translateX(0);
  }
  50% {
    transform: rotate(-25deg) translateX(5px);
  }
}

@keyframes leaf-sway-2 {
  0%, 100% {
    transform: rotate(-45deg) translateX(0);
  }
  50% {
    transform: rotate(-40deg) translateX(4px);
  }
}

@keyframes leaf-sway-3 {
  0%, 100% {
    transform: rotate(-25deg) translateX(0);
  }
  50% {
    transform: rotate(-20deg) translateX(6px);
  }
}

@keyframes leaf-left-sway-1 {
  0%, 100% {
    transform: rotate(25deg) translateX(0);
  }
  50% {
    transform: rotate(30deg) translateX(-5px);
  }
}

@keyframes leaf-left-sway-2 {
  0%, 100% {
    transform: rotate(35deg) translateX(0);
  }
  50% {
    transform: rotate(40deg) translateX(-4px);
  }
}

@keyframes leaf-left-sway-3 {
  0%, 100% {
    transform: rotate(20deg) translateX(0);
  }
  50% {
    transform: rotate(25deg) translateX(-6px);
  }
}

.login-card {
  width: min(540px, 100%);
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 14px;
  background: var(--qb-bg-card);
  padding: 18px;
  position: relative;
  z-index: 1;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
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
