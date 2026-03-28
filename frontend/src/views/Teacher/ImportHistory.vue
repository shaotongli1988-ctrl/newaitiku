<script setup>
import QuestionBatchTaskCenter from '../../components/questions/QuestionBatchTaskCenter.vue'
</script>

<template>
  <section class="import-history-page">
    <header class="page-header">
      <h3>批量导入历史</h3>
      <p>集中查看 Word 批量解析任务、恢复历史结果，并查看回滚候选题目。</p>
    </header>

    <QuestionBatchTaskCenter />
  </section>
</template>

<style scoped>
.import-history-page {
  display: grid;
  gap: 14px;
}

.page-header h3,
.page-header p {
  margin: 0;
}

.page-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-8);
}
</style>
