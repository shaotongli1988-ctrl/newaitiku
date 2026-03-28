<script setup>
import { computed, inject, useSlots } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  name: {
    type: [String, Number],
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const slots = useSlots()
const collapseContext = inject('uiCollapseContext', computed(() => ({
  accordion: false,
  isActive: () => false,
  toggle: () => {},
})))

const itemName = computed(() => props.name === '' ? props.title : props.name)
const isActive = computed(() => collapseContext.value.isActive(itemName.value))

const itemClasses = computed(() => [
  'ui-collapse-item',
  'el-collapse-item',
  isActive.value ? 'is-active' : '',
  props.disabled ? 'is-disabled' : '',
])

function handleToggle() {
  if (props.disabled) {
    return
  }
  collapseContext.value.toggle(itemName.value)
}
</script>

<template>
  <section :class="itemClasses">
    <button
      type="button"
      class="ui-collapse-item__header el-collapse-item__header"
      :class="{ 'is-active': isActive }"
      :disabled="disabled"
      :aria-expanded="String(isActive)"
      @click="handleToggle"
    >
      <span class="ui-collapse-item__title">
        <slot name="title">
          {{ title }}
        </slot>
      </span>
      <span class="ui-collapse-item__arrow" :class="{ 'is-active': isActive }" aria-hidden="true">
        <svg viewBox="0 0 16 16" focusable="false">
          <path d="M4.47 6.97a.75.75 0 0 1 1.06 0L8 9.44l2.47-2.47a.75.75 0 1 1 1.06 1.06l-3 3a.75.75 0 0 1-1.06 0l-3-3a.75.75 0 0 1 0-1.06Z" />
        </svg>
      </span>
    </button>

    <Transition name="ui-collapse-panel">
      <div v-if="isActive" class="ui-collapse-item__wrap el-collapse-item__wrap" role="region">
        <div class="ui-collapse-item__content el-collapse-item__content">
          <slot />
        </div>
      </div>
    </Transition>
  </section>
</template>

<style scoped>
.ui-collapse-item {
  border-top: 1px solid color-mix(in srgb, var(--qb-border-subtle) 82%, white 18%);
}

.ui-collapse-item:first-child {
  border-top: none;
}

.ui-collapse-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 14px 2px;
  border: 0;
  background: transparent;
  color: var(--qb-text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.ui-collapse-item__header:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.ui-collapse-item__title {
  min-width: 0;
  display: inline-flex;
  align-items: center;
}

.ui-collapse-item__arrow {
  flex: 0 0 auto;
  display: inline-flex;
  width: 18px;
  height: 18px;
  color: var(--qb-text-secondary);
  transition: transform 180ms ease, color 180ms ease;
}

.ui-collapse-item__arrow svg {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

.ui-collapse-item__arrow.is-active {
  transform: rotate(180deg);
  color: var(--qb-primary-student);
}

.ui-collapse-item__wrap {
  overflow: hidden;
}

.ui-collapse-item__content {
  padding: 0 0 16px;
}

.ui-collapse-panel-enter-active,
.ui-collapse-panel-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.ui-collapse-panel-enter-from,
.ui-collapse-panel-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
