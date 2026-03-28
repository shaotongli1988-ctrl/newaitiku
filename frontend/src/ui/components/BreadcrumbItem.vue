<script setup>
import { computed, inject } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  to: {
    type: [String, Object],
    default: undefined,
  },
  replace: {
    type: Boolean,
    default: false,
  },
})

const router = useRouter()
const breadcrumbContext = inject('uiBreadcrumbContext', computed(() => ({
  separator: '/',
  separatorIcon: null,
})))

const separator = computed(() => breadcrumbContext.value?.separator || '/')
const separatorIcon = computed(() => breadcrumbContext.value?.separatorIcon || null)
const isLink = computed(() => props.to !== undefined && props.to !== null && props.to !== '')

async function handleNavigate() {
  if (!isLink.value) {
    return
  }

  if (props.replace) {
    await router.replace(props.to)
    return
  }

  await router.push(props.to)
}
</script>

<template>
  <li class="ui-breadcrumb-item el-breadcrumb__item">
    <component
      :is="isLink ? 'button' : 'span'"
      class="ui-breadcrumb-item__inner el-breadcrumb__inner"
      :type="isLink ? 'button' : undefined"
      @click="handleNavigate"
    >
      <slot />
    </component>

    <span class="ui-breadcrumb-item__separator el-breadcrumb__separator" role="presentation" aria-hidden="true">
      <component :is="separatorIcon" v-if="separatorIcon" />
      <template v-else>{{ separator }}</template>
    </span>
  </li>
</template>

<style scoped>
.ui-breadcrumb-item {
  display: inline-flex;
  align-items: center;
  min-width: 0;
}

.ui-breadcrumb-item:last-child .ui-breadcrumb-item__separator {
  display: none;
}

.ui-breadcrumb-item__inner {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  line-height: inherit;
  text-decoration: none;
}

button.ui-breadcrumb-item__inner {
  cursor: pointer;
}

button.ui-breadcrumb-item__inner:hover {
  color: var(--qb-primary-student);
}

.ui-breadcrumb-item__separator {
  display: inline-flex;
  align-items: center;
  margin: 0 8px;
  user-select: none;
}
</style>
