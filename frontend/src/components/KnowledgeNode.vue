<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const BASE_SIZE = 20

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

function normalizeMastery(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue)) {
    return 0
  }
  return Math.max(0, Math.min(1, numericValue))
}

function normalizeQuestionCount(value) {
  const numericValue = Number(value || 0)
  if (!Number.isFinite(numericValue) || numericValue < 0) {
    return 0
  }
  return Math.floor(numericValue)
}

function withAlpha(color, alpha) {
  const normalizedAlpha = Math.max(0, Math.min(1, Number(alpha || 0)))
  const hexMatch = String(color).trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i)
  if (!hexMatch) {
    return color
  }
  let hex = hexMatch[1]
  if (hex.length === 3) {
    hex = hex
      .split('')
      .map((segment) => `${segment}${segment}`)
      .join('')
  }
  const red = parseInt(hex.slice(0, 2), 16)
  const green = parseInt(hex.slice(2, 4), 16)
  const blue = parseInt(hex.slice(4, 6), 16)
  return `rgba(${red}, ${green}, ${blue}, ${normalizedAlpha})`
}

function resolveBaseColor() {
  const rootStyle = getComputedStyle(document.documentElement)
  const color = String(rootStyle.getPropertyValue('--qb-primary-student') || '').trim()
  return color || 'var(--qb-primary-student)'
}

const label = computed(() => String(props.data?.label || props.data?.id || '未命名知识点'))
const mastery = computed(() => normalizeMastery(props.data?.mastery))
const questionCount = computed(() => normalizeQuestionCount(props.data?.questionCount))
const level = computed(() => Number(props.data?.level || 0))
const isUnpracticedLeafNode = computed(() => level.value >= 5 && mastery.value <= 0)
const isWeakNode = computed(() => mastery.value < 0.6)
const isHighlighted = computed(() => Boolean(props.data?.isHighlighted))
const isActive = computed(() => Boolean(props.data?.isActive))
const showHandles = computed(() => Boolean(props.data?.showHandles))
const emphasisMode = computed(() => String(props.data?.emphasisMode || 'student').trim())
const nodeRole = computed(() => String(props.data?.nodeRole || '').trim())
const branchColor = computed(() => String(props.data?.branchColor || '').trim())

const symbolSize = computed(() => {
  const encodedSize = Number(props.data?.size)
  if (Number.isFinite(encodedSize) && encodedSize > 0) {
    return Math.round(encodedSize)
  }
  return Math.round(BASE_SIZE + (Math.log(questionCount.value + 1) * 10))
})

const nodeDiameter = computed(() => Math.max(92, (symbolSize.value * 2) + 8))
const teacherNodeWidth = computed(() => {
  const textLength = String(label.value || '').length
  if (nodeRole.value === 'subject') {
    return Math.max(240, Math.min(340, 150 + (textLength * 11)))
  }
  if (nodeRole.value === 'focus') {
    return Math.max(180, Math.min(260, 108 + (textLength * 9)))
  }
  if (nodeRole.value === 'branch') {
    return Math.max(140, Math.min(220, 84 + (textLength * 8)))
  }
  return Math.max(102, Math.min(152, 60 + (textLength * 6)))
})

const nodeStyle = computed(() => {
  if (emphasisMode.value === 'teacher') {
    const baseColor = resolveBaseColor()
    const isSubject = nodeRole.value === 'subject'
    const isFocus = nodeRole.value === 'focus'
    const isBranch = nodeRole.value === 'branch'
    const accentColor = branchColor.value || baseColor
    return {
      width: `${teacherNodeWidth.value}px`,
      minHeight: isSubject ? '70px' : (isFocus ? '56px' : (nodeRole.value === 'leaf' ? '34px' : '44px')),
      padding: isSubject ? '16px 26px' : (nodeRole.value === 'leaf' ? '6px 9px' : '10px 14px'),
      borderRadius: isSubject ? '26px' : '16px',
      borderColor: (props.selected || isActive.value)
        ? withAlpha(accentColor, 0.92)
        : (
          isFocus
            ? withAlpha(accentColor, 0.34)
            : (isBranch ? withAlpha(accentColor, 0.22) : 'rgba(120, 131, 155, 0.18)')
        ),
      boxShadow: props.selected || isActive.value
        ? `0 10px 28px ${withAlpha(accentColor, 0.14)}`
        : (nodeRole.value === 'leaf' ? '0 3px 10px rgba(15, 23, 42, 0.04)' : '0 6px 18px rgba(15, 23, 42, 0.06)'),
      background: isSubject
        ? `linear-gradient(135deg, ${withAlpha(baseColor, 0.28)}, ${withAlpha(baseColor, 0.12)})`
        : isWeakNode.value
          ? 'linear-gradient(135deg, rgba(255, 243, 224, 0.98), rgba(255, 224, 178, 0.96))'
          : (
            isFocus
              ? `linear-gradient(135deg, ${withAlpha(accentColor, 0.18)}, rgba(255, 255, 255, 0.98))`
              : (isBranch
                ? `linear-gradient(135deg, ${withAlpha(accentColor, 0.12)}, rgba(255, 255, 255, 0.98))`
                : 'linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(249, 250, 251, 0.94))')
          ),
      color: 'var(--qb-text-heading)',
    }
  }
  if (isUnpracticedLeafNode.value) {
    return {
      width: `${nodeDiameter.value}px`,
      minHeight: `${nodeDiameter.value}px`,
      borderColor: props.selected ? 'rgba(126, 134, 148, 0.92)' : 'rgba(126, 134, 148, 0.68)',
      boxShadow: props.selected ? '0 0 0 3px rgba(126, 134, 148, 0.22)' : (isHighlighted.value ? '0 0 0 4px rgba(255, 159, 67, 0.3)' : 'none'),
      background: 'linear-gradient(140deg, rgba(187, 193, 205, 0.9), rgba(137, 145, 159, 0.95))',
    }
  }
  const baseColor = resolveBaseColor()
  const startAlpha = 0.38 + (mastery.value * 0.35)
  const endAlpha = 0.82 + (mastery.value * 0.16)
  const borderColor = isWeakNode.value ? 'rgba(255, 159, 67, 0.74)' : withAlpha(baseColor, 0.78)
  const weakStart = 'rgba(255, 188, 115, 0.82)'
  const weakEnd = 'rgba(255, 132, 76, 0.96)'
  return {
    width: `${nodeDiameter.value}px`,
    minHeight: `${nodeDiameter.value}px`,
    borderColor: (props.selected || isActive.value) ? withAlpha(baseColor, 1) : borderColor,
    boxShadow: props.selected
      ? `0 0 0 3px ${withAlpha(baseColor, 0.26)}`
      : (
        isActive.value
          ? '0 0 0 4px rgba(15, 118, 110, 0.18)'
          : (isHighlighted.value ? '0 0 0 4px rgba(255, 159, 67, 0.32)' : 'none')
      ),
    background: isWeakNode.value
      ? `linear-gradient(140deg, ${weakStart}, ${weakEnd})`
      : `linear-gradient(140deg, ${withAlpha(baseColor, startAlpha)}, ${withAlpha(baseColor, endAlpha)})`,
  }
})

function onNodeContextMenu() {
  const context_handler = props.data?.onContextMenu
  if (typeof context_handler !== 'function') {
    return
  }
  context_handler({
    id: String(props.data?.id || ''),
    label: String(props.data?.label || props.data?.id || ''),
    mastery: mastery.value,
  })
}
</script>

<template>
  <div
    class="knowledge-node"
    :class="{
      'is-weak': isWeakNode,
      'is-unpracticed': isUnpracticedLeafNode,
      'is-highlighted': isHighlighted,
      'is-active': isActive,
      'is-teacher': emphasisMode === 'teacher',
      'is-subject': nodeRole === 'subject',
      'is-focus': nodeRole === 'focus',
      'is-branch': nodeRole === 'branch',
      'is-leaf': nodeRole === 'leaf',
    }"
    :style="nodeStyle"
    @contextmenu.prevent="onNodeContextMenu"
  >
    <Handle v-if="showHandles" type="target" :position="Position.Left" class="node-handle" />
    <div class="node-content">
      <p class="node-title">{{ label }}</p>
      <template v-if="emphasisMode !== 'teacher'">
        <p class="node-meta">掌握度 {{ Math.round(mastery * 100) }}%</p>
        <p class="node-meta">关联题数 {{ questionCount }}</p>
      </template>
    </div>
    <Handle v-if="showHandles" type="source" :position="Position.Right" class="node-handle" />
  </div>
</template>

<style scoped>
.knowledge-node {
  border: 1.5px solid transparent;
  border-radius: 999px;
  color: var(--qb-bg-card);
  display: grid;
  place-items: center;
  padding: 12px;
  text-align: center;
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

.knowledge-node:hover {
  transform: translateY(-1px);
}

.knowledge-node.is-active {
  transform: translateY(-1px);
}

.knowledge-node.is-highlighted {
  animation: pulse-highlight 1.4s ease-in-out infinite;
}

.knowledge-node.is-weak,
.knowledge-node.is-unpracticed {
  color: var(--qb-bg-card);
}

.knowledge-node.is-teacher {
  text-align: left;
  place-items: stretch;
}

.knowledge-node.is-teacher .node-content {
  gap: 2px;
  justify-items: start;
}

.node-content {
  display: grid;
  gap: 4px;
}

.node-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.knowledge-node.is-teacher .node-title {
  font-size: 13px;
  font-weight: 650;
}

.knowledge-node.is-teacher .node-content > * {
  max-width: 100%;
}

.knowledge-node.is-teacher {
  line-height: 1.2;
}

.knowledge-node.is-teacher:is(.is-active) .node-title {
  font-size: 15px;
}

.knowledge-node.is-teacher.is-subject .node-title {
  font-size: 17px;
  letter-spacing: 0.01em;
}

.knowledge-node.is-teacher.is-focus .node-title {
  font-size: 14px;
}

.knowledge-node.is-teacher.is-leaf .node-title {
  font-size: 12px;
  font-weight: 600;
}

.knowledge-node.is-teacher[style*='70px'] .node-title {
  font-size: 17px;
  letter-spacing: 0.01em;
}

.node-meta {
  margin: 0;
  font-size: 11px;
  line-height: 1.2;
  opacity: 0.95;
}

.node-handle {
  width: 10px;
  height: 10px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.84);
}

@keyframes pulse-highlight {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}
</style>
