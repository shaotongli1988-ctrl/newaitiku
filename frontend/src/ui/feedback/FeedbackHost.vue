<template>
  <Teleport to="body">
    <TransitionGroup name="feedback-toast" tag="div" class="feedback-toast-stack">
      <article
        v-for="toast in feedbackState.toasts"
        :key="toast.id"
        class="feedback-toast"
        :class="`feedback-toast--${toast.type || 'info'}`"
      >
        <div class="feedback-toast__accent" />
        <div class="feedback-toast__body">
          <p class="feedback-toast__message">{{ toast.message }}</p>
        </div>
        <button
          v-if="toast.showClose"
          type="button"
          class="feedback-toast__close"
          @click="closeToast(toast.id)"
        >
          关闭
        </button>
      </article>
    </TransitionGroup>

    <Transition name="feedback-dialog">
      <div
        v-if="feedbackState.dialog.visible"
        class="feedback-dialog__overlay"
        @click="handleOverlayClick"
      >
        <section
          class="feedback-dialog"
          :class="`feedback-dialog--${feedbackState.dialog.type || 'info'}`"
          @click.stop
        >
          <header class="feedback-dialog__header">
            <p class="feedback-dialog__eyebrow">操作提示</p>
            <h3 class="feedback-dialog__title">{{ feedbackState.dialog.title }}</h3>
          </header>

          <p class="feedback-dialog__message">{{ feedbackState.dialog.message }}</p>

          <div v-if="feedbackState.dialog.mode === 'prompt'" class="feedback-dialog__input-wrap">
            <input
              ref="promptInputRef"
              class="feedback-dialog__input"
              :placeholder="feedbackState.dialog.inputPlaceholder || '请输入内容'"
              :value="feedbackState.dialog.inputValue"
              @input="handleInput"
              @keydown.enter.prevent="validatePromptBeforeResolve"
            >
            <p v-if="feedbackState.dialog.inputError" class="feedback-dialog__error">
              {{ feedbackState.dialog.inputError }}
            </p>
          </div>

          <footer class="feedback-dialog__footer">
            <button
              v-if="feedbackState.dialog.mode !== 'alert'"
              type="button"
              class="feedback-dialog__button feedback-dialog__button--ghost"
              @click="rejectDialog('cancel')"
            >
              {{ feedbackState.dialog.cancelButtonText || '取消' }}
            </button>
            <button
              type="button"
              class="feedback-dialog__button feedback-dialog__button--solid"
              @click="handleConfirm"
            >
              {{ feedbackState.dialog.confirmButtonText || '确定' }}
            </button>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  closeToast,
  feedbackState,
  rejectDialog,
  resolveDialog,
  syncDialogInput,
  validatePromptBeforeResolve,
} from './service'

const promptInputRef = ref(null)

function handleConfirm() {
  if (feedbackState.dialog.mode === 'prompt') {
    validatePromptBeforeResolve()
    return
  }
  resolveDialog()
}

function handleOverlayClick() {
  if (feedbackState.dialog.closeOnClickModal) {
    rejectDialog('close')
  }
}

function handleInput(event) {
  syncDialogInput(event?.target?.value || '')
}

function handleEscape(event) {
  if (event.key !== 'Escape' || !feedbackState.dialog.visible || !feedbackState.dialog.closeOnPressEscape) {
    return
  }
  rejectDialog('close')
}

watch(
  () => feedbackState.dialog.visible,
  async (visible) => {
    if (!visible || feedbackState.dialog.mode !== 'prompt') {
      return
    }
    await nextTick()
    promptInputRef.value?.focus()
    promptInputRef.value?.select?.()
  },
)

onMounted(() => {
  window.addEventListener('keydown', handleEscape)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
.feedback-toast-stack {
  position: fixed;
  top: 20px;
  left: 50%;
  z-index: 3200;
  display: grid;
  gap: 12px;
  width: min(460px, calc(100vw - 24px));
  transform: translateX(-50%);
  pointer-events: none;
}

.feedback-toast {
  display: grid;
  grid-template-columns: 6px 1fr auto;
  align-items: stretch;
  min-height: 58px;
  border: 1px solid var(--qb-border-glass);
  border-radius: 18px;
  overflow: hidden;
  background: var(--qb-gradient-primary-card);
  box-shadow: var(--qb-shadow-modal);
  pointer-events: auto;
  --feedback-toast-accent: var(--qb-primary-600);
}

.feedback-toast__accent {
  background: var(--feedback-toast-accent);
}

.feedback-toast--success {
  --feedback-toast-accent: var(--qb-success-500);
}

.feedback-toast--warning {
  --feedback-toast-accent: var(--qb-warning-600);
}

.feedback-toast--error {
  --feedback-toast-accent: var(--qb-danger-600);
}

.feedback-toast__body {
  display: flex;
  align-items: center;
  padding: 14px 16px;
}

.feedback-toast__message {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-line;
}

.feedback-toast__close {
  border: 0;
  padding: 0 16px;
  background: transparent;
  color: var(--qb-text-subtle-9);
  cursor: pointer;
  font-size: 12px;
}

.feedback-dialog__overlay {
  position: fixed;
  inset: 0;
  z-index: 3300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: color-mix(in srgb, var(--qb-overlay-scrim) 100%, transparent);
  backdrop-filter: blur(10px);
}

.feedback-dialog {
  width: min(480px, 100%);
  border: 1px solid var(--qb-border-glass);
  border-radius: 28px;
  padding: 24px;
  background: var(--qb-gradient-info-card);
  box-shadow: var(--qb-shadow-panel);
}

.feedback-dialog--warning {
  background: var(--qb-gradient-warning-card);
}

.feedback-dialog--error {
  background: var(--qb-gradient-danger-card);
}

.feedback-dialog--success {
  background: var(--qb-gradient-success-card);
}

.feedback-dialog__header {
  margin-bottom: 12px;
}

.feedback-dialog__eyebrow {
  margin: 0 0 6px;
  color: var(--qb-text-subtle-9);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.feedback-dialog__title {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 22px;
  line-height: 1.2;
}

.feedback-dialog__message {
  margin: 0;
  color: var(--qb-text-secondary-strong);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-line;
}

.feedback-dialog__input-wrap {
  margin-top: 16px;
}

.feedback-dialog__input {
  width: 100%;
  border: 1px solid var(--qb-border-strong);
  border-radius: 16px;
  padding: 12px 14px;
  background: var(--qb-surface-strong);
  color: var(--qb-text-heading);
  font-size: 14px;
  outline: none;
}

.feedback-dialog__input:focus {
  border-color: var(--qb-primary-600);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--qb-primary-600) 14%, transparent);
}

.feedback-dialog__error {
  margin: 8px 0 0;
  color: var(--qb-danger-600);
  font-size: 12px;
}

.feedback-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 22px;
}

.feedback-dialog__button {
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 14px;
  cursor: pointer;
}

.feedback-dialog__button--ghost {
  border: 1px solid var(--qb-border-strong);
  background: var(--qb-surface-glass);
  color: var(--qb-text-secondary-strong);
}

.feedback-dialog__button--solid {
  border: 1px solid transparent;
  background: var(--qb-text-heading);
  color: var(--qb-text-inverse);
}

.feedback-toast-enter-active,
.feedback-toast-leave-active,
.feedback-dialog-enter-active,
.feedback-dialog-leave-active {
  transition: all 0.2s ease;
}

.feedback-toast-enter-from,
.feedback-toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.feedback-dialog-enter-from,
.feedback-dialog-leave-to {
  opacity: 0;
}

.feedback-dialog-enter-from .feedback-dialog,
.feedback-dialog-leave-to .feedback-dialog {
  transform: translateY(12px) scale(0.98);
}

@media (max-width: 640px) {
  .feedback-toast-stack {
    top: 14px;
    width: calc(100vw - 20px);
  }

  .feedback-dialog {
    padding: 20px;
    border-radius: 22px;
  }

  .feedback-dialog__footer {
    flex-direction: column-reverse;
  }

  .feedback-dialog__button {
    width: 100%;
  }
}
</style>
