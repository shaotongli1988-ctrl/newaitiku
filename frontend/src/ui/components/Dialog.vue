<script setup>
import { computed, onBeforeUnmount, onMounted, ref, useAttrs, useSlots, watch } from 'vue'
import { normalizeDialogWidth } from './dialogShared'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  width: {
    type: [String, Number],
    default: '680px',
  },
  showClose: {
    type: Boolean,
    default: true,
  },
  closeOnClickModal: {
    type: Boolean,
    default: true,
  },
  destroyOnClose: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'update:modelValue',
  'close',
  'closed',
  'before-close',
  'beforeClose',
])

const attrs = useAttrs()
const slots = useSlots()
const hasRendered = ref(false)
const isVisible = computed(() => Boolean(props.modelValue))
const shouldRender = computed(() => isVisible.value || (!props.destroyOnClose && hasRendered.value))
const hasFooter = computed(() => Boolean(slots.footer))
const hasHeaderSlot = computed(() => Boolean(slots.header))
const dialogWidth = computed(() => normalizeDialogWidth(props.width))

const rootAttrs = computed(() => ({
  class: attrs.class,
  style: attrs.style,
}))

const panelAttrs = computed(() => {
  const nextAttrs = {}
  Object.entries(attrs).forEach(([key, value]) => {
    if (key === 'class' || key === 'style') {
      return
    }
    nextAttrs[key] = value
  })
  return nextAttrs
})

function lockBodyScroll(locked) {
  if (typeof document === 'undefined') {
    return
  }
  document.body.style.overflow = locked ? 'hidden' : ''
}

function requestClose() {
  emit('before-close')
  emit('beforeClose')
  emit('close')
  emit('update:modelValue', false)
}

function handleOverlayClick() {
  if (!props.closeOnClickModal) {
    return
  }
  requestClose()
}

function handleEscape(event) {
  if (event.key !== 'Escape' || !isVisible.value) {
    return
  }
  requestClose()
}

function handleAfterLeave() {
  emit('closed')
}

watch(
  () => props.modelValue,
  (nextVisible) => {
    if (nextVisible) {
      hasRendered.value = true
    }
    lockBodyScroll(Boolean(nextVisible))
  },
  { immediate: true },
)

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  lockBodyScroll(false)
  window.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="ui-dialog-fade" @after-leave="handleAfterLeave">
      <div
        v-if="shouldRender"
        v-show="isVisible"
        v-bind="rootAttrs"
        class="ui-dialog-overlay el-overlay-dialog"
        @click="handleOverlayClick"
      >
        <div
          v-bind="panelAttrs"
          class="ui-dialog el-dialog"
          :style="{ '--ui-dialog-width': dialogWidth }"
          role="dialog"
          aria-modal="true"
          :aria-label="title || '对话框'"
          @click.stop
        >
          <header v-if="hasHeaderSlot || title || showClose" class="el-dialog__header">
            <slot name="header">
              <span class="el-dialog__title">{{ title }}</span>
            </slot>
            <button
              v-if="showClose"
              type="button"
              class="el-dialog__headerbtn"
              aria-label="关闭对话框"
              @click="requestClose"
            >
              <span class="el-dialog__close">×</span>
            </button>
          </header>

          <div class="el-dialog__body">
            <slot />
          </div>

          <footer v-if="hasFooter" class="el-dialog__footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.ui-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: color-mix(in srgb, var(--qb-overlay-scrim) 100%, transparent);
  backdrop-filter: blur(8px);
}

.ui-dialog {
  width: min(var(--ui-dialog-width, 680px), calc(100vw - 32px));
  max-height: min(88vh, 960px);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  border-radius: 24px;
  background: var(--qb-gradient-primary-card);
  box-shadow: var(--qb-shadow-panel);
  overflow: hidden;
}

.el-dialog__header {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px 12px;
}

.el-dialog__title {
  color: var(--qb-text-heading);
  font-size: 22px;
  line-height: 1.2;
  font-weight: 700;
}

.el-dialog__headerbtn {
  border: 0;
  border-radius: 999px;
  width: 36px;
  height: 36px;
  background: rgba(148, 163, 184, 0.12);
  color: var(--qb-text-secondary-strong);
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
}

.el-dialog__body {
  overflow: auto;
  padding: 8px 22px 18px;
}

.el-dialog__footer {
  display: flex;
  justify-content: flex-end;
  padding: 0 22px 20px;
}

.ui-dialog-fade-enter-active,
.ui-dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}

.ui-dialog-fade-enter-from,
.ui-dialog-fade-leave-to {
  opacity: 0;
}

.ui-dialog-fade-enter-from .ui-dialog,
.ui-dialog-fade-leave-to .ui-dialog {
  transform: translateY(12px) scale(0.98);
}
</style>
