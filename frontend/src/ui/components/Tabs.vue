<script setup>
import { computed, provide, ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: undefined,
  },
  stretch: {
    type: Boolean,
    default: false,
  },
  tabPosition: {
    type: String,
    default: 'top',
  },
})

const emit = defineEmits(['update:modelValue', 'tab-click', 'tab-change', 'change'])

const panes = ref([])

function resolvePaneValue(source, fallback = '') {
  if (source && typeof source === 'object' && 'value' in source) {
    return source.value ?? fallback
  }
  return source ?? fallback
}

function getPaneName(pane, index = 0) {
  const explicitName = resolvePaneValue(pane?.name, undefined)
  if (explicitName !== undefined && explicitName !== null && explicitName !== '') {
    return explicitName
  }
  return String(index)
}

function isPaneDisabled(pane) {
  return Boolean(resolvePaneValue(pane?.disabled, false))
}

function registerPane(pane) {
  if (!pane || panes.value.some((entry) => entry.uid === pane.uid)) {
    return
  }
  panes.value = [...panes.value, pane]
}

function unregisterPane(uid) {
  panes.value = panes.value.filter((pane) => pane.uid !== uid)
}

const activeName = computed(() => props.modelValue)

function activatePane(name, pane) {
  if (isPaneDisabled(pane)) {
    return
  }
  emit('tab-click', { paneName: name, pane })
  if (activeName.value === name) {
    return
  }
  emit('update:modelValue', name)
  emit('tab-change', name)
  emit('change', name)
}

function getPaneLabelComponent(pane) {
  return pane?.labelComponent ?? null
}

watch(
  () => panes.value.map((pane, index) => getPaneName(pane, index)),
  (names) => {
    if (!names.length) {
      return
    }

    const current = activeName.value
    if (names.includes(current)) {
      return
    }

    const fallbackPane = panes.value.find((pane) => !isPaneDisabled(pane)) || panes.value[0]
    const fallbackName = getPaneName(fallbackPane, 0)
    if (fallbackName === undefined || fallbackName === null || fallbackName === '') {
      return
    }

    emit('update:modelValue', fallbackName)
    emit('tab-change', fallbackName)
    emit('change', fallbackName)
  },
  { immediate: true },
)

provide('uiTabsContext', {
  activeName,
  registerPane,
  unregisterPane,
})

const tabsClasses = computed(() => [
  'ui-tabs',
  'el-tabs',
  props.stretch ? 'is-stretch' : '',
  props.tabPosition === 'left' ? 'el-tabs--left' : '',
  props.tabPosition === 'right' ? 'el-tabs--right' : '',
  props.tabPosition === 'bottom' ? 'el-tabs--bottom' : '',
])
</script>

<template>
  <section :class="tabsClasses">
    <div class="el-tabs__header" role="tablist" :aria-orientation="tabPosition === 'left' || tabPosition === 'right' ? 'vertical' : 'horizontal'">
      <div class="el-tabs__nav-wrap">
        <div class="el-tabs__nav-scroll">
          <div class="el-tabs__nav" :class="{ 'is-stretch': stretch }">
            <button
              v-for="(pane, index) in panes"
              :id="pane.tabId"
              :key="pane.uid"
              type="button"
              class="el-tabs__item"
              :class="{
                'is-active': activeName === getPaneName(pane, index),
                'is-disabled': isPaneDisabled(pane),
              }"
              role="tab"
              :tabindex="activeName === getPaneName(pane, index) ? 0 : -1"
              :aria-selected="String(activeName === getPaneName(pane, index))"
              :aria-controls="pane.panelId"
              :disabled="isPaneDisabled(pane)"
              @click="activatePane(getPaneName(pane, index), pane)"
            >
              <component :is="getPaneLabelComponent(pane)" />
            </button>
            <div class="el-tabs__active-bar" aria-hidden="true" />
          </div>
        </div>
      </div>
    </div>

    <div class="el-tabs__content">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.ui-tabs {
  width: 100%;
}

.el-tabs__header {
  margin-bottom: 14px;
}

.el-tabs__nav-wrap {
  overflow-x: auto;
  scrollbar-width: none;
}

.el-tabs__nav-wrap::-webkit-scrollbar {
  display: none;
}

.el-tabs__nav-scroll {
  min-width: 100%;
}

.el-tabs__nav {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 100%;
}

.el-tabs__nav.is-stretch {
  display: flex;
}

.el-tabs__item {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 0 14px;
  border: 0;
  background: transparent;
  color: var(--qb-text-secondary);
  font: inherit;
  white-space: nowrap;
  cursor: pointer;
  transition: color 180ms ease, opacity 180ms ease;
}

.el-tabs__nav.is-stretch .el-tabs__item {
  flex: 1 1 0;
}

.el-tabs__item:hover {
  color: var(--qb-text-primary);
}

.el-tabs__item.is-active {
  color: var(--qb-text-primary);
}

.el-tabs__item.is-disabled {
  cursor: not-allowed;
  opacity: 0.48;
}

.el-tabs__active-bar {
  pointer-events: none;
}

.el-tabs__content {
  min-width: 0;
}
</style>
