<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { hasBackendErrorCode, resolveApiErrorMessage } from '../../api/request'
import { fetchKnowledgeTree, moveKnowledgeNode } from '../../api/services/questionBank'

const props = defineProps({
  selectedKnowledgeId: {
    type: String,
    default: '',
  },
  status: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:selectedKnowledgeId', 'node-selected'])

const treeRef = ref(null)
const keyword = ref('')
const loading = ref(false)
const treeData = ref([])

const treeProps = {
  value: 'id',
  label: 'name',
  children: 'children',
}

const allNodeCount = computed(() => {
  const queue = [...treeData.value]
  let count = 0
  while (queue.length) {
    const node = queue.shift()
    if (!node) {
      continue
    }
    count += 1
    const children = Array.isArray(node.children) ? node.children : []
    children.forEach((child) => queue.push(child))
  }
  return count
})

function filterNode(keywordValue, data) {
  if (!keywordValue) {
    return true
  }
  const normalizedKeyword = String(keywordValue || '').trim()
  if (!normalizedKeyword) {
    return true
  }
  const text = `${data?.id || ''} ${data?.name || ''}`
  return text.includes(normalizedKeyword)
}

function findParentAndSiblings(nodes, targetId, parentId = '') {
  for (let index = 0; index < nodes.length; index += 1) {
    const item = nodes[index]
    if (String(item.id) === String(targetId)) {
      return { parentId, siblings: nodes, index }
    }
    const children = Array.isArray(item.children) ? item.children : []
    if (!children.length) {
      continue
    }
    const found = findParentAndSiblings(children, targetId, String(item.id || ''))
    if (found) {
      return found
    }
  }
  return null
}

async function reloadTree() {
  loading.value = true
  try {
    treeData.value = await fetchKnowledgeTree(props.status)
    await nextTick()
    if (treeRef.value && props.selectedKnowledgeId) {
      treeRef.value.setCurrentKey(props.selectedKnowledgeId)
    }
  } catch (error) {
    treeData.value = []
    if (hasBackendErrorCode(error, 'QUESTION_FORBIDDEN')) {
      ElMessage.error('当前账号暂无知识点树访问权限。')
      return
    }
    ElMessage.error(resolveApiErrorMessage(error, '知识点树加载失败'))
  } finally {
    loading.value = false
  }
}

function handleNodeClick(nodeData) {
  const nodeId = String(nodeData?.id || '')
  emit('update:selectedKnowledgeId', nodeId)
  emit('node-selected', nodeData)
}

function allowDrop(draggingNode, dropNode, type) {
  if (!draggingNode?.data || !dropNode?.data) {
    return false
  }
  if (type === 'inner') {
    return false
  }
  const draggingMeta = findParentAndSiblings(treeData.value, draggingNode.data.id)
  const dropMeta = findParentAndSiblings(treeData.value, dropNode.data.id)
  if (!draggingMeta || !dropMeta) {
    return false
  }
  return String(draggingMeta.parentId || '') === String(dropMeta.parentId || '')
}

async function moveByDelta(knowledgeId, delta) {
  if (!delta) {
    return
  }
  const direction = delta > 0 ? 'down' : 'up'
  const stepCount = Math.abs(delta)
  for (let step = 0; step < stepCount; step += 1) {
    await moveKnowledgeNode(knowledgeId, direction)
  }
}

async function handleNodeDrop(draggingNode, dropNode, dropType) {
  if (!draggingNode?.data || !dropNode?.data) {
    return
  }
  const draggingMeta = findParentAndSiblings(treeData.value, draggingNode.data.id)
  const dropMeta = findParentAndSiblings(treeData.value, dropNode.data.id)
  if (!draggingMeta || !dropMeta) {
    return
  }
  if (String(draggingMeta.parentId || '') !== String(dropMeta.parentId || '')) {
    ElMessage.warning('当前仅支持同级拖拽排序')
    await reloadTree()
    return
  }

  const sourceIndex = Number(draggingMeta.index)
  let targetIndex = Number(dropMeta.index)
  if (dropType === 'after') {
    targetIndex += 1
  }
  if (sourceIndex < targetIndex) {
    targetIndex -= 1
  }
  const delta = targetIndex - sourceIndex
  if (!delta) {
    return
  }

  loading.value = true
  try {
    await moveByDelta(String(draggingNode.data.id), delta)
    ElMessage.success('知识点顺序已更新')
  } catch (error) {
    if (hasBackendErrorCode(error, 'QUESTION_INVALID_STATUS')) {
      ElMessage.error('当前知识点状态不允许拖拽排序。')
    } else {
      ElMessage.error(resolveApiErrorMessage(error, '知识点拖拽失败'))
    }
  } finally {
    loading.value = false
    await reloadTree()
  }
}

watch(keyword, async (value) => {
  await nextTick()
  treeRef.value?.filter(String(value || '').trim())
})

watch(
  () => props.selectedKnowledgeId,
  async (value) => {
    await nextTick()
    if (value) {
      treeRef.value?.setCurrentKey(value)
    }
  },
)

onMounted(() => {
  reloadTree()
})

defineExpose({
  reloadTree,
})
</script>

<template>
  <section class="knowledge-tree-panel">
    <header class="tree-header">
      <h3>动态知识点树</h3>
      <el-tag effect="plain" size="small">节点 {{ allNodeCount }}</el-tag>
    </header>

    <el-input
      v-model="keyword"
      clearable
      placeholder="搜索知识点名称或 ID"
    />

    <el-skeleton
      v-if="loading"
      :rows="8"
      animated
    />
    <el-tree-v2
      v-else
      ref="treeRef"
      :data="treeData"
      :props="treeProps"
      :height="500"
      node-key="id"
      highlight-current
      :draggable="true"
      :allow-drop="allowDrop"
      :filter-method="filterNode"
      @node-click="handleNodeClick"
      @node-drop="handleNodeDrop"
    />
  </section>
</template>

<style scoped>
.knowledge-tree-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: linear-gradient(180deg, var(--qb-bg-card), var(--qb-primary-soft-bg));
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.tree-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--qb-text-heading);
}
</style>
