<script setup>
import { computed, onBeforeUnmount, onMounted, ref, useAttrs, useSlots, watch } from 'vue'
import { normalizeOverlayDirection, resolveDrawerPanelStyle } from './dialogShared'

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
    type: [String, Number],
    default: '42%',
  },
  direction: {
    type: String,
    default: 'rtl',
  },
  withHeader: {
    type: Boolean,
    default: true,
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
const normalizedDirection = computed(() => normalizeOverlayDirection(props.direction))
const drawerStyle = computed(() => resolveDrawerPanelStyle(normalizedDirection.value, props.size))

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
    <Transition name="ui-drawer-fade" @after-leave="handleAfterLeave">
      <div
        v-if="shouldRender"
        v-show="isVisible"
        v-bind="rootAttrs"
        class="ui-drawer-overlay"
        :class="`is-${normalizedDirection}`"
        @click="handleOverlayClick"
      >
        <section
          v-bind="panelAttrs"
          class="ui-drawer el-drawer"
          :class="`is-${normalizedDirection}`"
          :style="drawerStyle"
          role="dialog"
          aria-modal="true"
          :aria-label="title || '抽屉面板'"
          @click.stop
        >
          <header
            v-if="withHeader && (hasHeaderSlot || title || showClose)"
            class="el-drawer__header"
          >
            <slot name="header">
              <span class="el-drawer__title">{{ title }}</span>
            </slot>
            <button
              v-if="showClose"
              type="button"
              class="el-drawer__close-btn"
              aria-label="关闭抽屉"
              @click="requestClose"
            >
              <span class="el-drawer__close">×</span>
            </button>
          </header>

          <div class="el-drawer__body">
            <slot />
          </div>

          <footer v-if="hasFooter" class="el-drawer__footer">
            <slot name="footer" />
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.ui-drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  background: rgba(15, 23, 42, 0.36);
  backdrop-filter: blur(8px);
}

.ui-drawer-overlay.is-rtl {
  justify-content: flex-end;
}

.ui-drawer-overlay.is-ltr {
  justify-content: flex-start;
}

.ui-drawer-overlay.is-ttb {
  align-items: flex-start;
}

.ui-drawer-overlay.is-btt {
  align-items: flex-end;
}

.ui-drawer {
  width: min(var(--ui-drawer-width, 42%), 100vw);
  max-width: 100vw;
  height: min(var(--ui-drawer-height, 100vh), 100vh);
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  background:
    linear-gradient(180deg, var(--qb-surface-strong), color-mix(in srgb, var(--qb-bg-body) 82%, white 18%));
  overflow: hidden;
}

.ui-drawer.is-rtl,
.ui-drawer.is-ltr {
  box-shadow: -24px 0 64px rgba(15, 23, 42, 0.18);
  border-left: 1px solid var(--qb-border-glass);
}

.ui-drawer.is-ltr {
  box-shadow: 24px 0 64px rgba(15, 23, 42, 0.18);
  border-left: 0;
  border-right: 1px solid var(--qb-border-glass);
}

.ui-drawer.is-ttb,
.ui-drawer.is-btt {
  width: 100vw;
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.18);
  border-top: 0;
  border-bottom: 1px solid var(--qb-border-glass);
}

.ui-drawer.is-btt {
  border-bottom: 0;
  border-top: 1px solid var(--qb-border-glass);
  box-shadow: 0 -24px 64px rgba(15, 23, 42, 0.18);
}

.el-drawer__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px 14px;
  border-bottom: 1px solid var(--qb-border-glass);
  background: rgba(255, 255, 255, 0.72);
}

.el-drawer__title {
  color: var(--qb-text-heading);
  font-size: 22px;
  line-height: 1.2;
  font-weight: 700;
}

.el-drawer__close-btn {
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

.el-drawer__body {
  overflow: auto;
  padding: 18px 22px 22px;
}

.el-drawer__footer {
  padding: 0 22px 22px;
  border-top: 1px solid color-mix(in srgb, var(--qb-border-glass) 72%, transparent);
  background: rgba(255, 255, 255, 0.72);
}

.ui-drawer-fade-enter-active,
.ui-drawer-fade-leave-active {
  transition: opacity 0.22s ease;
}

.ui-drawer-fade-enter-from,
.ui-drawer-fade-leave-to {
  opacity: 0;
}

.ui-drawer-fade-enter-from .ui-drawer.is-rtl,
.ui-drawer-fade-leave-to .ui-drawer.is-rtl {
  transform: translateX(28px);
}

.ui-drawer-fade-enter-from .ui-drawer.is-ltr,
.ui-drawer-fade-leave-to .ui-drawer.is-ltr {
  transform: translateX(-28px);
}

.ui-drawer-fade-enter-from .ui-drawer.is-ttb,
.ui-drawer-fade-leave-to .ui-drawer.is-ttb {
  transform: translateY(-24px);
}

.ui-drawer-fade-enter-from .ui-drawer.is-btt,
.ui-drawer-fade-leave-to .ui-drawer.is-btt {
  transform: translateY(24px);
}

@media (max-width: 900px) {
  .ui-drawer.is-rtl,
  .ui-drawer.is-ltr {
    width: min(max(var(--ui-drawer-width, 42%), 86vw), 100vw);
  }
}

@media (max-width: 640px) {
  .ui-drawer.is-rtl,
  .ui-drawer.is-ltr {
    width: 100vw;
  }

  .el-drawer__header,
  .el-drawer__body,
  .el-drawer__footer {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
