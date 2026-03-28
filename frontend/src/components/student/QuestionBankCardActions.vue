<script setup>
defineProps({
  stackedOnMobile: {
    type: Boolean,
    default: true,
  },
})
</script>

<template>
  <div :class="['question-bank-card-actions', { 'question-bank-card-actions--stacked': stackedOnMobile }]">
    <slot />
  </div>
</template>

<style scoped>
.question-bank-card-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .question-bank-card-actions--stacked {
    flex-direction: column;
    align-items: stretch;
  }

  .question-bank-card-actions--stacked :deep(.el-button) {
    width: 100%;
  }
}
</style>
