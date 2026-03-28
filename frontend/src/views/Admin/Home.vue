<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Setting, UserFilled } from '@/ui/icons'
import { ElMessage } from '@/ui/feedback'
import { fetchAdminConsoleData } from '../../api/services/questionBank'

const router = useRouter()

const loading = ref(true)
const refreshing = ref(false)
const summary = reactive({
  studentCount: 0,
  teacherCount: 0,
  disabledCount: 0,
  messageCount: 0,
  templateCount: 0,
})
const systemSettings = reactive({
  platformName: '',
  defaultExamMinutes: 0,
  aiDailyLimit: 0,
})
const managedUsersPreview = ref([])

const metricCards = computed(() => ([
  {
    key: 'studentCount',
    label: '学生账号',
    value: summary.studentCount,
    icon: UserFilled,
    tone: 'is-primary',
    hint: '来自超管账号目录中的学生总数。',
  },
  {
    key: 'teacherCount',
    label: '教师账号',
    value: summary.teacherCount,
    icon: UserFilled,
    tone: 'is-success',
    hint: '来自超管账号目录中的教师总数。',
  },
  {
    key: 'disabledCount',
    label: '停用账号',
    value: summary.disabledCount,
    icon: Setting,
    tone: 'is-warning',
    hint: '可进入系统控制台继续排查停用原因。',
  },
  {
    key: 'messageCount',
    label: '系统消息',
    value: summary.messageCount,
    icon: Bell,
    tone: 'is-danger',
    hint: '统计系统消息存量，可直接进入消息中心。',
  },
]))

const quickActions = [
  {
    key: 'control-center',
    title: '系统控制台',
    description: '继续处理系统参数、账号目录、考生导入导出。',
    path: '/admin/control-center',
  },
  {
    key: 'syllabus',
    title: '大纲仓库',
    description: '维护版本、目标权重和 AI 解析结果。',
    path: '/admin/syllabus',
  },
  {
    key: 'messages',
    title: '消息中心',
    description: '查看系统消息和跨角色消息收敛情况。',
    path: '/messages',
  },
]

function applyConsolePayload(payload) {
  const nextSummary = payload?.summary && typeof payload.summary === 'object' ? payload.summary : {}
  summary.studentCount = Number(nextSummary.studentCount || 0)
  summary.teacherCount = Number(nextSummary.teacherCount || 0)
  summary.disabledCount = Number(nextSummary.disabledCount || 0)
  summary.messageCount = Number(nextSummary.messageCount || 0)
  summary.templateCount = Number(nextSummary.templateCount || 0)

  const nextSettings = payload?.systemSettings && typeof payload.systemSettings === 'object' ? payload.systemSettings : {}
  systemSettings.platformName = String(nextSettings.platformName || '')
  systemSettings.defaultExamMinutes = Number(nextSettings.defaultExamMinutes || 0)
  systemSettings.aiDailyLimit = Number(nextSettings.aiDailyLimit || 0)

  managedUsersPreview.value = Array.isArray(payload?.managedUsers) ? payload.managedUsers.slice(0, 5) : []
}

async function loadAdminHome() {
  try {
    const payload = await fetchAdminConsoleData()
    applyConsolePayload(payload)
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '超管首页数据加载失败'))
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function refreshPage() {
  if (refreshing.value) {
    return
  }
  refreshing.value = true
  await loadAdminHome()
}

function goTo(path) {
  router.push(path)
}

onMounted(() => {
  loadAdminHome()
})
</script>

<template>
  <section class="page-shell" v-loading="loading">
    <header class="page-header">
      <div>
        <h3>管理驾驶舱</h3>
        <p>新版超管首页统一收口系统摘要、配置入口和高频治理动作。</p>
      </div>
      <el-button :loading="refreshing" @click="refreshPage">刷新概览</el-button>
    </header>

    <section class="card-grid">
      <article
        v-for="card in metricCards"
        :key="card.key"
        class="data-card"
        :class="card.tone"
      >
        <component :is="card.icon" class="card-icon" />
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <p>{{ card.hint }}</p>
      </article>
    </section>

    <section class="content-grid">
      <el-card shadow="never">
        <template #header>
          <div class="card-head">
            <span>系统基线</span>
            <el-tag type="info" effect="light">模板数 {{ summary.templateCount }}</el-tag>
          </div>
        </template>
        <div class="meta-grid">
          <article>
            <span>平台名称</span>
            <strong>{{ systemSettings.platformName || '未配置' }}</strong>
          </article>
          <article>
            <span>默认考试时长</span>
            <strong>{{ systemSettings.defaultExamMinutes || 0 }} 分钟</strong>
          </article>
          <article>
            <span>AI 每日额度</span>
            <strong>{{ systemSettings.aiDailyLimit || 0 }} 次</strong>
          </article>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="card-head">
            <span>快捷入口</span>
          </div>
        </template>
        <div class="action-grid">
          <button
            v-for="action in quickActions"
            :key="action.key"
            class="action-card"
            type="button"
            @click="goTo(action.path)"
          >
            <strong>{{ action.title }}</strong>
            <span>{{ action.description }}</span>
          </button>
        </div>
      </el-card>
    </section>

    <el-card shadow="never">
      <template #header>
        <div class="card-head">
          <span>最近账号预览</span>
        </div>
      </template>
      <el-empty v-if="!managedUsersPreview.length" description="暂无可展示账号" />
      <el-table v-else :data="managedUsersPreview" border>
        <el-table-column prop="userId" label="用户ID" min-width="140" />
        <el-table-column prop="role" label="角色" width="120" />
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column prop="mobile" label="手机号" width="150" />
      </el-table>
    </el-card>
  </section>
</template>

<style scoped>
.page-shell {
  display: grid;
  gap: 12px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.page-header h3,
.page-header p {
  margin: 0;
}

.page-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-6);
}

.card-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.data-card {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--qb-primary-soft-border);
  background: var(--qb-bg-card);
  display: grid;
  gap: 8px;
}

.card-icon {
  width: 20px;
  height: 20px;
}

.data-card strong {
  font-size: 28px;
}

.data-card p {
  margin: 0;
  font-size: 13px;
  color: var(--qb-text-subtle-5);
}

.is-primary {
  background: var(--qb-primary-soft-bg);
}

.is-success {
  background: var(--qb-success-soft-bg);
}

.is-warning {
  background: var(--qb-warning-soft-bg);
}

.is-danger {
  background: var(--qb-danger-soft-bg);
}

.content-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(280px, 1fr) minmax(320px, 1.2fr);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.meta-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.meta-grid article {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 10px;
  background: var(--qb-primary-soft-bg);
}

.meta-grid span {
  font-size: 12px;
  color: var(--qb-text-subtle-5);
}

.meta-grid strong {
  font-size: 18px;
}

.action-grid {
  display: grid;
  gap: 10px;
}

.action-card {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: var(--qb-bg-card);
  padding: 14px;
  text-align: left;
  display: grid;
  gap: 6px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.action-card:hover {
  transform: translateY(-1px);
  border-color: var(--el-color-primary);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.action-card strong {
  font-size: 16px;
}

.action-card span {
  font-size: 13px;
  color: var(--qb-text-subtle-5);
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
