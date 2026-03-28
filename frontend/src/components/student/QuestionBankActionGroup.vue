<template>
  <div :class="['question-bank-action-group', { 'question-bank-action-group--compact': compact }]">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  compact: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.question-bank-action-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.question-bank-action-group--compact {
  gap: 8px;
}
</style>
