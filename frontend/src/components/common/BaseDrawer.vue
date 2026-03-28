<script setup>
import { computed, onBeforeUnmount, onMounted, ref, useAttrs, useSlots, watch } from 'vue'

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
  size: {
    type: String,
    default: '42%',
  },
  loading: {
    type: Boolean,
    default: false,
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

const attrs = useAttrs()
const slots = useSlots()
const hasRendered = ref(false)
const isVisible = computed(() => Boolean(props.modelValue))
const shouldRender = computed(() => isVisible.value || (!props.destroyOnClose && hasRendered.value))
const hasFooter = computed(() => Boolean(slots.footer))

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
    <Transition name="base-drawer-fade">
      <div
        v-if="shouldRender"
        v-show="isVisible"
        class="base-drawer-overlay"
        @click="handleOverlayClick"
      >
        <section
          v-bind="attrs"
          class="base-drawer-panel"
          :style="{ '--base-drawer-size': size }"
          role="dialog"
          aria-modal="true"
          :aria-label="title || '抽屉面板'"
          @click.stop
        >
          <header class="base-drawer-header">
            <div class="base-drawer-title-wrap">
              <h3 class="base-drawer-title">{{ title }}</h3>
            </div>
            <button
              type="button"
              class="base-drawer-close"
              :disabled="loading"
              aria-label="关闭抽屉"
              @click="requestClose"
            >
              ×
            </button>
          </header>

          <div class="base-drawer-body" v-loading="loading">
            <slot />
          </div>

          <footer v-if="hasFooter" class="base-drawer-footer">
            <slot name="footer" :cancel="handleCancel" />
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.base-drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.36);
  backdrop-filter: blur(8px);
}

.base-drawer-panel {
  width: min(var(--base-drawer-size, 42%), 100vw);
  max-width: 100vw;
  height: 100vh;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  background:
    linear-gradient(180deg, var(--qb-surface-strong), color-mix(in srgb, var(--qb-bg-body) 82%, white 18%));
  box-shadow: -24px 0 64px rgba(15, 23, 42, 0.18);
  border-left: 1px solid var(--qb-border-glass);
  overflow: hidden;
}

.base-drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px 14px;
  border-bottom: 1px solid var(--qb-border-glass);
  background: rgba(255, 255, 255, 0.72);
}

.base-drawer-title-wrap {
  min-width: 0;
}

.base-drawer-title {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 22px;
  line-height: 1.2;
}

.base-drawer-close {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-text-subtle-8) 12%, white 88%);
  color: var(--qb-text-secondary-strong);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.base-drawer-close:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.base-drawer-body {
  overflow: auto;
  padding: 18px 22px 22px;
}

.base-drawer-footer {
  padding: 0 22px 22px;
  border-top: 1px solid color-mix(in srgb, var(--qb-border-glass) 72%, transparent);
  background: rgba(255, 255, 255, 0.72);
}

.base-drawer-fade-enter-active,
.base-drawer-fade-leave-active {
  transition: opacity 0.22s ease;
}

.base-drawer-fade-enter-from,
.base-drawer-fade-leave-to {
  opacity: 0;
}

.base-drawer-fade-enter-from .base-drawer-panel,
.base-drawer-fade-leave-to .base-drawer-panel {
  transform: translateX(28px);
}

@media (max-width: 900px) {
  .base-drawer-panel {
    width: min(max(var(--base-drawer-size, 42%), 86vw), 100vw);
  }
}

@media (max-width: 640px) {
  .base-drawer-panel {
    width: 100vw;
  }

  .base-drawer-header,
  .base-drawer-body,
  .base-drawer-footer {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
