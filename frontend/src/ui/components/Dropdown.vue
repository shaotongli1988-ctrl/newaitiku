<script setup>
import { computed, onBeforeUnmount, provide, ref, useAttrs } from 'vue'
import {
  dropdownContextKey,
  normalizeDropdownTrigger,
  shouldCloseDropdownOnCommand,
} from './dropdownShared'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
  hideOnClick: {
    type: Boolean,
    default: true,
  },
  trigger: {
    type: String,
    default: 'hover',
  },
})

const emit = defineEmits(['command', 'visible-change'])

const attrs = useAttrs()
const rootRef = ref(null)
const isOpen = ref(false)

const normalizedTrigger = computed(() => normalizeDropdownTrigger(props.trigger))
const rootAttrs = computed(() => ({
  class: attrs.class,
  style: attrs.style,
}))

function updateVisible(visible) {
  if (isOpen.value === visible) {
    return
  }
  isOpen.value = visible
  emit('visible-change', visible)
}

function openMenu() {
  if (props.disabled) {
    return
  }
  updateVisible(true)
}

function closeMenu() {
  updateVisible(false)
}

function toggleMenu() {
  if (props.disabled) {
    return
  }
  updateVisible(!isOpen.value)
}

function handleItemCommand(command, disabled = false) {
  if (disabled) {
    return
  }
  emit('command', command)
  if (shouldCloseDropdownOnCommand({ hideOnClick: props.hideOnClick, disabled })) {
    closeMenu()
  }
}

function handleDocumentPointerDown(event) {
  if (!rootRef.value?.contains(event.target)) {
    closeMenu()
  }
}

function handleTriggerClick() {
  if (normalizedTrigger.value !== 'click') {
    return
  }
  toggleMenu()
}

provide(dropdownContextKey, {
  emitCommand: handleItemCommand,
})

if (typeof document !== 'undefined') {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
}

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('pointerdown', handleDocumentPointerDown)
  }
})
</script>

<template>
  <div
    ref="rootRef"
    v-bind="rootAttrs"
    class="ui-dropdown el-dropdown"
    @mouseenter="normalizedTrigger === 'hover' ? openMenu() : undefined"
    @mouseleave="normalizedTrigger === 'hover' ? closeMenu() : undefined"
  >
    <div class="ui-dropdown__trigger" @click.stop="handleTriggerClick">
      <slot />
    </div>

    <transition name="ui-dropdown-fade">
      <div v-if="isOpen" class="ui-dropdown__menu-panel">
        <slot name="dropdown" />
      </div>
    </transition>
  </div>
</template>

<style scoped>
.ui-dropdown {
  position: relative;
  display: inline-flex;
}

.ui-dropdown__trigger {
  display: inline-flex;
  align-items: center;
}

.ui-dropdown__menu-panel {
  position: absolute;
  z-index: 60;
  top: calc(100% + 8px);
  right: 0;
  min-width: 168px;
}

.ui-dropdown-fade-enter-active,
.ui-dropdown-fade-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.ui-dropdown-fade-enter-from,
.ui-dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
