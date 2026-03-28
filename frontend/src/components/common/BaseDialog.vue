<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

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
    type: String,
    default: '680px',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  empty: {
    type: Boolean,
    default: false,
  },
  emptyDescription: {
    type: String,
    default: '当前暂无可展示内容。',
  },
  errorText: {
    type: String,
    default: '',
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

const emit = defineEmits(['update:modelValue', 'cancel', 'beforeClose'])

const hasRendered = ref(false)
const isVisible = computed(() => Boolean(props.modelValue))
const shouldRender = computed(() => isVisible.value || (!props.destroyOnClose && hasRendered.value))
const showContent = computed(() => {
  if (props.errorText) {
    return 'error'
  }
  if (props.empty) {
    return 'empty'
  }
  return 'content'
})

function lockBodyScroll(locked) {
  if (typeof document === 'undefined') {
    return
  }
  document.body.style.overflow = locked ? 'hidden' : ''
}

function requestClose() {
  emit('beforeClose')
  emit('update:modelValue', false)
}

function handleOverlayClick() {
  if (props.loading || !props.closeOnClickModal) {
    return
  }
  requestClose()
}

function handleCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

function handleEscape(event) {
  if (event.key !== 'Escape' || !isVisible.value || props.loading) {
    return
  }
  requestClose()
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
    <Transition name="base-dialog-fade">
      <div
        v-if="shouldRender"
        v-show="isVisible"
        class="base-dialog-overlay"
        @click="handleOverlayClick"
      >
        <section
          class="base-dialog-panel"
          :style="{ '--base-dialog-width': width }"
          @click.stop
        >
          <header class="base-dialog-header">
            <div>
              <h3 class="base-dialog-title">{{ title }}</h3>
            </div>
            <button
              type="button"
              class="base-dialog-close"
              :disabled="loading"
              aria-label="关闭弹窗"
              @click="requestClose"
            >
              ×
            </button>
          </header>

          <div class="base-dialog-body" v-loading="loading">
            <div v-if="showContent === 'error'" class="base-dialog-empty">
              <strong>加载失败</strong>
              <p>{{ errorText }}</p>
            </div>
            <div v-else-if="showContent === 'empty'" class="base-dialog-empty">
              <strong>暂无内容</strong>
              <p>{{ emptyDescription }}</p>
            </div>
            <slot v-else />
          </div>

          <footer class="base-dialog-footer">
            <slot name="footer" :cancel="handleCancel" />
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.base-dialog-overlay {
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

.base-dialog-panel {
  width: min(var(--base-dialog-width, 680px), 100%);
  max-height: min(88vh, 960px);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  border-radius: 24px;
  background: var(--qb-gradient-primary-card);
  box-shadow: var(--qb-shadow-panel);
  overflow: hidden;
}

.base-dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px 12px;
}

.base-dialog-title {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 22px;
  line-height: 1.2;
}

.base-dialog-close {
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

.base-dialog-close:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.base-dialog-body {
  overflow: auto;
  padding: 8px 22px 18px;
}

.base-dialog-empty {
  display: grid;
  gap: 8px;
  justify-items: center;
  padding: 36px 12px;
  text-align: center;
}

.base-dialog-empty strong {
  color: var(--qb-text-heading);
  font-size: 18px;
}

.base-dialog-empty p {
  margin: 0;
  color: var(--qb-text-subtle-9);
  font-size: 14px;
  line-height: 1.7;
}

.base-dialog-footer {
  display: flex;
  justify-content: flex-end;
  padding: 0 22px 20px;
}

.base-dialog-fade-enter-active,
.base-dialog-fade-leave-active {
  transition: opacity 0.2s ease;
}

.base-dialog-fade-enter-from,
.base-dialog-fade-leave-to {
  opacity: 0;
}

.base-dialog-fade-enter-from .base-dialog-panel,
.base-dialog-fade-leave-to .base-dialog-panel {
  transform: translateY(12px) scale(0.98);
}

@media (max-width: 768px) {
  .base-dialog-overlay {
    padding: 12px;
  }

  .base-dialog-panel {
    max-height: 92vh;
    border-radius: 20px;
  }

  .base-dialog-header,
  .base-dialog-body,
  .base-dialog-footer {
    padding-left: 16px;
    padding-right: 16px;
  }

  .base-dialog-footer {
    padding-bottom: 16px;
  }
}
</style>
