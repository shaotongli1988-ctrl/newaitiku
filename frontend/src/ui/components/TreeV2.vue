<script setup>
import { computed, ref } from 'vue'
import {
  filterTreeNodes,
  resolveTreeConfig,
  resolveTreeDropType,
} from './treeShared'

const props = defineProps({
  allowDrop: {
    type: Function,
    default: undefined,
  },
  data: {
    type: Array,
    default: () => [],
  },
  draggable: {
    type: Boolean,
    default: false,
  },
  filterMethod: {
    type: Function,
    default: undefined,
  },
  height: {
    type: [String, Number],
    default: undefined,
  },
  highlightCurrent: {
    type: Boolean,
    default: false,
  },
  nodeKey: {
    type: String,
    default: '',
  },
  props: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['node-click', 'node-drop'])

const currentKey = ref('')
const keyword = ref('')
const draggingRowKey = ref('')
const dropState = ref({
  key: '',
  type: '',
})

const treeConfig = computed(() => resolveTreeConfig(props.props, props.nodeKey))
const visibleRows = computed(() => filterTreeNodes(
  props.data,
  keyword.value,
  props.filterMethod,
  { props: props.props, nodeKey: props.nodeKey },
))
const panelStyle = computed(() => ({
  '--ui-tree-height': typeof props.height === 'number' ? `${props.height}px` : String(props.height || 'auto'),
}))

function createNodeWrapper(row) {
  return {
    data: row.data,
    key: row.key,
  }
}

function setCurrentKey(nextKey) {
  currentKey.value = String(nextKey || '').trim()
}

function filter(nextKeyword) {
  keyword.value = String(nextKeyword || '').trim()
}

function handleNodeClick(row) {
  if (props.highlightCurrent) {
    currentKey.value = row.key
  }
  emit('node-click', row.data, createNodeWrapper(row))
}

function handleDragStart(row, event) {
  if (!props.draggable) {
    return
  }
  draggingRowKey.value = row.key
  event.dataTransfer.effectAllowed = 'move'
}

function handleDragEnd() {
  draggingRowKey.value = ''
  dropState.value = { key: '', type: '' }
}

function handleDragOver(row, event) {
  if (!props.draggable || !draggingRowKey.value || draggingRowKey.value === row.key) {
    return
  }

  const draggingRow = visibleRows.value.find((item) => item.key === draggingRowKey.value)
  if (!draggingRow) {
    return
  }
  const dropType = resolveTreeDropType(event)
  const allowed = typeof props.allowDrop === 'function'
    ? props.allowDrop(createNodeWrapper(draggingRow), createNodeWrapper(row), dropType)
    : true
  if (!allowed) {
    return
  }

  event.preventDefault()
  dropState.value = {
    key: row.key,
    type: dropType,
  }
}

function handleDrop(row, event) {
  if (!props.draggable || !draggingRowKey.value || draggingRowKey.value === row.key) {
    return
  }

  const draggingRow = visibleRows.value.find((item) => item.key === draggingRowKey.value)
  if (!draggingRow) {
    return
  }

  const dropType = resolveTreeDropType(event)
  const allowed = typeof props.allowDrop === 'function'
    ? props.allowDrop(createNodeWrapper(draggingRow), createNodeWrapper(row), dropType)
    : true

  if (!allowed) {
    return
  }

  event.preventDefault()
  emit('node-drop', createNodeWrapper(draggingRow), createNodeWrapper(row), dropType)
  handleDragEnd()
}

defineExpose({
  filter,
  setCurrentKey,
})
</script>

<template>
  <div class="ui-tree-v2 el-tree" :style="panelStyle">
    <div class="ui-tree-v2__body">
      <div
        v-for="row in visibleRows"
        :key="row.key"
        class="ui-tree-v2__row"
        :class="{
          'is-current': highlightCurrent && currentKey === row.key,
          'is-drop-before': dropState.key === row.key && dropState.type === 'before',
          'is-drop-after': dropState.key === row.key && dropState.type === 'after',
        }"
        :style="{ '--ui-tree-level': row.level }"
        :draggable="draggable"
        @click="handleNodeClick(row)"
        @dragstart="handleDragStart(row, $event)"
        @dragend="handleDragEnd"
        @dragover="handleDragOver(row, $event)"
        @drop="handleDrop(row, $event)"
      >
        <span class="ui-tree-v2__guide" />
        <span class="ui-tree-v2__label">{{ row.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ui-tree-v2 {
  width: 100%;
  min-height: 120px;
  max-height: var(--ui-tree-height, auto);
  overflow: auto;
  border: 1px solid var(--qb-border-muted);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
}

.ui-tree-v2__body {
  display: grid;
  gap: 2px;
  padding: 8px;
}

.ui-tree-v2__row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 36px;
  padding: 8px 12px 8px calc(12px + var(--ui-tree-level, 0) * 18px);
  border-radius: 12px;
  color: var(--qb-text-primary);
  cursor: pointer;
  user-select: none;
  transition: background-color 160ms ease, color 160ms ease;
}

.ui-tree-v2__row:hover {
  background: color-mix(in srgb, var(--qb-primary-student) 8%, white 92%);
}

.ui-tree-v2__row.is-current {
  background: color-mix(in srgb, var(--qb-primary-student) 14%, white 86%);
  color: var(--qb-primary-student);
  font-weight: 600;
}

.ui-tree-v2__row.is-drop-before::before,
.ui-tree-v2__row.is-drop-after::after {
  content: '';
  position: absolute;
  left: 10px;
  right: 10px;
  height: 2px;
  border-radius: 999px;
  background: var(--qb-primary-student);
}

.ui-tree-v2__row.is-drop-before::before {
  top: 0;
}

.ui-tree-v2__row.is-drop-after::after {
  bottom: 0;
}

.ui-tree-v2__guide {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-primary-student) 45%, white 55%);
  flex: 0 0 auto;
}

.ui-tree-v2__label {
  min-width: 0;
  word-break: break-all;
}
</style>
