<script setup>
/**
 * 页面定位：管理员 Dashboard。
 * 当前版本提供角色分区路由落地后的基础占位结构，后续可继续接入审核与配置模块。
 */
const stats = [
  { label: '待审核题目', value: 42 },
  { label: '权限变更待处理', value: 3 },
  { label: '系统告警', value: 1 },
]
</script>

<template>
  <!-- 中文说明：管理员页面采用 Grid 卡片布局，保证桌面和移动端都稳定显示。 -->
  <section class="dashboard-page">
    <header class="page-header">
      <h2>管理员控制台</h2>
      <p>你正在访问 /admin 分区，当前页面由真实路由承载。</p>
    </header>

    <section class="stat-grid">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <h4>{{ item.label }}</h4>
        <p>{{ item.value }}</p>
      </article>
    </section>
  </section>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 14px;
}

.page-header h2,
.page-header p {
  margin: 0;
}

.page-header p {
  color: var(--qb-text-subtle-1);
}

.stat-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--qb-border-subtle);
  background: var(--qb-bg-subtle);
}

.stat-card h4,
.stat-card p {
  margin: 0;
}

.stat-card p {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-color-primary);
}
</style>
