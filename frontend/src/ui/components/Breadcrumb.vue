<script setup>
import { computed, provide } from 'vue'

const props = defineProps({
  separator: {
    type: String,
    default: '/',
  },
  separatorIcon: {
    type: [String, Object, Function],
    default: null,
  },
})

const breadcrumbContext = computed(() => ({
  separator: String(props.separator || '/'),
  separatorIcon: props.separatorIcon,
}))

provide('uiBreadcrumbContext', breadcrumbContext)
</script>

<template>
  <nav class="ui-breadcrumb el-breadcrumb" aria-label="Breadcrumb">
    <ol class="ui-breadcrumb__list">
      <slot />
    </ol>
  </nav>
</template>

<style scoped>
.ui-breadcrumb {
  min-width: 0;
}

.ui-breadcrumb__list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}
</style>
