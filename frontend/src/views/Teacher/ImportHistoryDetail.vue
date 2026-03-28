<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QuestionBatchTaskDetail from '../../components/questions/QuestionBatchTaskDetail.vue'

const route = useRoute()
const router = useRouter()

const taskId = computed(() => String(route.params.taskId || '').trim())
</script>

<template>
  <section class="import-history-page">
    <header class="page-header">
      <div>
        <h3>批量导入任务详情</h3>
        <p>支持查看解析结果、异常列表、回滚候选，并恢复到录题预览区。</p>
      </div>
      <el-button plain @click="router.push({ name: 'teacherQuestions', hash: '#import-history' })">返回题库管理</el-button>
    </header>

    <QuestionBatchTaskDetail :task-id="taskId" />
  </section>
</template>

<style scoped>
.import-history-page {
  display: grid;
  gap: 14px;
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
  color: var(--qb-text-subtle-8);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
