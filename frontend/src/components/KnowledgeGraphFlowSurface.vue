<script setup>
import { computed } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import KnowledgeNode from './KnowledgeNode.vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  hasGraphData: {
    type: Boolean,
    default: false,
  },
  isTeacherMode: {
    type: Boolean,
    default: true,
  },
  teacherRelationMode: {
    type: Boolean,
    default: false,
  },
  flowRenderKey: {
    type: String,
    default: '',
  },
  nodes: {
    type: Array,
    default: () => [],
  },
  edges: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:nodes', 'update:edges', 'node-click', 'node-drag-stop', 'connect'])

const nodeTypes = {
  knowledge: KnowledgeNode,
}

const nodesModel = computed({
  get: () => props.nodes,
  set: (value) => emit('update:nodes', value),
})

const edgesModel = computed({
  get: () => props.edges,
  set: (value) => emit('update:edges', value),
})

function handleNodeClick(payload) {
  emit('node-click', payload)
}

function handleNodeDragStop(payload) {
  emit('node-drag-stop', payload)
}

function handleConnect(payload) {
  emit('connect', payload)
}
</script>

<template>
  <div v-loading="loading" :class="['graph-surface', { 'graph-surface--teacher': isTeacherMode } ]">
    <el-empty v-if="!loading && !hasGraphData" description="暂无图谱数据" />
    <VueFlow
      v-else
      :key="flowRenderKey"
      v-model:nodes="nodesModel"
      v-model:edges="edgesModel"
      :class="['graph-flow', { 'graph-flow--teacher': isTeacherMode }]"
      :node-types="nodeTypes"
      :fit-view-on-init="true"
      :nodes-connectable="isTeacherMode ? teacherRelationMode : false"
      :nodes-draggable="isTeacherMode ? teacherRelationMode : false"
      :elements-selectable="true"
      @node-click="handleNodeClick"
      @node-drag-stop="handleNodeDragStop"
      @connect="handleConnect"
    >
      <Background
        v-if="isTeacherMode ? teacherRelationMode : true"
        :gap="isTeacherMode ? 22 : 18"
        :size="1"
        :pattern-color="isTeacherMode ? 'rgba(15, 118, 110, 0.14)' : 'rgba(76, 110, 245, 0.22)'"
      />
      <Controls
        v-if="isTeacherMode ? teacherRelationMode : true"
        position="bottom-right"
      />
    </VueFlow>
  </div>
</template>

<style scoped>
.graph-surface {
  min-height: clamp(340px, 56vh, 700px);
  border: 1px solid rgba(15, 118, 110, 0.1);
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(15, 118, 110, 0.06), transparent 22%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 250, 0.94));
  overflow: hidden;
}

.graph-surface--teacher {
  min-height: clamp(420px, 68vh, 860px);
}

.graph-flow {
  width: 100%;
  height: clamp(320px, 54vh, 680px);
}

.graph-flow--teacher {
  height: clamp(400px, 66vh, 840px);
}
</style>
