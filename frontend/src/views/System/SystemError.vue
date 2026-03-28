<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function toHome() {
  router.push('/student/home')
}
</script>

<template>
  <section class="error-shell">
    <article class="error-card">
      <h2>系统暂时不可用</h2>
      <p>服务器出现异常，已自动拦截并跳转到系统错误页。请稍后重试或联系管理员。</p>
      <div class="actions">
        <el-button type="primary" @click="toHome">返回首页</el-button>
        <el-button @click="() => window.location.reload()">刷新页面</el-button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.error-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.error-card {
  width: min(560px, 100%);
  padding: 24px;
  border-radius: 16px;
  border: 1px solid rgba(226, 232, 240, 0.85);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
}

.error-card h2,
.error-card p {
  margin: 0;
}

.error-card p {
  margin-top: 10px;
  color: var(--qb-text-secondary);
  line-height: 1.7;
}

.actions {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
