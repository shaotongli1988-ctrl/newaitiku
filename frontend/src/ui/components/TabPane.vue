<script setup>
import { computed, getCurrentInstance, inject, onBeforeUnmount, onMounted, ref, useSlots, watch } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  name: {
    type: [String, Number],
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  lazy: {
    type: Boolean,
    default: false,
  },
})

const instance = getCurrentInstance()
const slots = useSlots()
const tabsContext = inject('uiTabsContext', null)
const hasBeenActive = ref(false)

const uid = `ui-tab-pane-${instance?.uid ?? Math.random().toString(36).slice(2)}`
const paneName = computed(() => {
  if (props.name !== undefined && props.name !== null && props.name !== '') {
    return props.name
  }
  return uid
})
const panelId = `${uid}-panel`
const tabId = `${uid}-tab`

const isActive = computed(() => tabsContext?.activeName?.value === paneName.value)
const shouldRender = computed(() => !props.lazy || hasBeenActive.value || isActive.value)

watch(
  isActive,
  (active) => {
    if (active) {
      hasBeenActive.value = true
    }
  },
  { immediate: true },
)

onMounted(() => {
  tabsContext?.registerPane?.({
    uid,
    name: paneName,
    disabled: computed(() => props.disabled),
    panelId,
    tabId,
    labelComponent: {
      render: () => slots.label?.() ?? props.label,
    },
  })
})

onBeforeUnmount(() => {
  tabsContext?.unregisterPane?.(uid)
})
</script>

<template>
  <div
    v-show="isActive"
    :id="panelId"
    class="ui-tab-pane el-tab-pane"
    :class="{ 'is-active': isActive }"
    role="tabpanel"
    :aria-labelledby="tabId"
  >
    <slot v-if="shouldRender" />
  </div>
</template>

<style scoped>
.ui-tab-pane {
  min-width: 0;
}
</style>
