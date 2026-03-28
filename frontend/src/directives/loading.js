const LOADING_DIRECTIVE_KEY = Symbol('qbLoadingDirective')
const LOADING_STYLE_ID = 'qb-loading-directive-style'

function ensureLoadingStyles() {
  if (typeof document === 'undefined' || document.getElementById(LOADING_STYLE_ID)) {
    return
  }

  const styleElement = document.createElement('style')
  styleElement.id = LOADING_STYLE_ID
  styleElement.textContent = `
    .qb-loading-host {
      overflow: hidden;
    }

    .qb-loading-mask {
      position: absolute;
      inset: 0;
      z-index: 12;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(248, 250, 252, 0.74);
      backdrop-filter: blur(3px);
      border-radius: inherit;
      pointer-events: auto;
    }

    .qb-loading-mask__inner {
      display: grid;
      justify-items: center;
      gap: 10px;
      padding: 14px 18px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.92);
      box-shadow: 0 20px 36px rgba(15, 23, 42, 0.08);
    }

    .qb-loading-mask__spinner {
      width: 28px;
      height: 28px;
      border-radius: 999px;
      border: 3px solid rgba(148, 163, 184, 0.28);
      border-top-color: #0f172a;
      animation: qb-loading-spin 0.8s linear infinite;
    }

    .qb-loading-mask__text {
      color: #475569;
      font-size: 12px;
      letter-spacing: 0.04em;
    }

    @keyframes qb-loading-spin {
      to {
        transform: rotate(360deg);
      }
    }
  `
  document.head.appendChild(styleElement)
}

function createOverlayElement() {
  const overlayElement = document.createElement('div')
  overlayElement.className = 'qb-loading-mask'
  overlayElement.innerHTML = `
    <div class="qb-loading-mask__inner" aria-live="polite" aria-busy="true">
      <span class="qb-loading-mask__spinner" />
      <span class="qb-loading-mask__text">加载中</span>
    </div>
  `
  return overlayElement
}

function ensureDirectiveContext(el) {
  if (el[LOADING_DIRECTIVE_KEY]) {
    return el[LOADING_DIRECTIVE_KEY]
  }

  const computedStyle = window.getComputedStyle(el)
  const shouldPatchPosition = computedStyle.position === 'static'
  const context = {
    overlayElement: createOverlayElement(),
    patchedPosition: shouldPatchPosition,
    originalPosition: el.style.position,
  }

  if (shouldPatchPosition) {
    el.style.position = 'relative'
  }

  el[LOADING_DIRECTIVE_KEY] = context
  return context
}

function applyLoadingState(el, value) {
  const context = ensureDirectiveContext(el)
  const visible = Boolean(value)

  if (visible) {
    if (!context.overlayElement.parentNode) {
      el.appendChild(context.overlayElement)
    }
    el.classList.add('qb-loading-host')
    el.setAttribute('aria-busy', 'true')
    return
  }

  if (context.overlayElement.parentNode === el) {
    el.removeChild(context.overlayElement)
  }
  el.classList.remove('qb-loading-host')
  el.removeAttribute('aria-busy')
}

export function createLoadingDirective() {
  return {
    mounted(el, binding) {
      ensureLoadingStyles()
      applyLoadingState(el, binding.value)
    },
    updated(el, binding) {
      if (binding.value === binding.oldValue) {
        return
      }
      applyLoadingState(el, binding.value)
    },
    unmounted(el) {
      const context = el[LOADING_DIRECTIVE_KEY]
      if (!context) {
        return
      }

      if (context.overlayElement.parentNode === el) {
        el.removeChild(context.overlayElement)
      }
      if (context.patchedPosition) {
        el.style.position = context.originalPosition
      }
      el.classList.remove('qb-loading-host')
      el.removeAttribute('aria-busy')
      delete el[LOADING_DIRECTIVE_KEY]
    },
  }
}

export default createLoadingDirective
