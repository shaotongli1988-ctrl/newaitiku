<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { knowledgeTree } from '../../api/services/questions'
import { listTeacherPaperClasses } from '../../api/services/papers'
import AiProgressBar from '../common/AiProgressBar.vue'
import BaseDialog from '../common/BaseDialog.vue'
import { useForm } from '../../composables/useForm'
import { useRequest } from '../../composables/useRequest'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  generating: {
    type: Boolean,
    default: false,
  },
  generationProgress: {
    type: Number,
    default: 0,
  },
  professionalOptions: {
    type: Array,
    default: () => [],
  },
  title: {
    type: String,
    default: 'AI 智能组卷参数配置',
  },
  width: {
    type: String,
    default: '680px',
  },
  loadingState: {
    type: Boolean,
    default: false,
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

const emit = defineEmits(['update:modelValue', 'start-generate', 'cancel', 'before-close', 'beforeClose'])

const classOptions = ref([])
const knowledgeOptions = ref([])
const professionalCascaderProps = {
  value: 'code',
  label: 'name',
  children: 'children',
  checkStrictly: true,
}
function createInitialAiForm() {
  return {
    scope_path: [],
    exam_category_code: '',
    joint_exam_group_code: '',
    subject_code: '',
    class_ids: [],
    total_count: 20,
    difficulty_level: 3,
    knowledge_scope: [],
  }
}

const { form: aiForm, resetForm } = useForm(createInitialAiForm)
const visible = computed({
  get() {
    return Boolean(props.modelValue)
  },
  set(value) {
    emit('update:modelValue', Boolean(value))
  },
})

function close() {
  visible.value = false
}

function handleCancel() {
  emit('cancel')
  close()
}

function handleBeforeClose() {
  emit('before-close')
  emit('beforeClose')
}

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function normalizeClassOptions(payload) {
  const rows = Array.isArray(payload) ? payload : []
  const options = []
  const seen = new Set()
  rows.forEach((item) => {
    const value = String(item?.value || item?.classId || item?.id || '').trim()
    if (!value || seen.has(value)) {
      return
    }
    seen.add(value)
    const label = String(item?.label || item?.className || item?.name || value).trim() || value
    options.push({ label, value })
  })
  return options.sort((left, right) => left.label.localeCompare(right.label, 'zh-Hans-CN'))
}

function normalizeKnowledgeTreeOptions(payload) {
  const source = payload && typeof payload === 'object' ? payload : {}
  const nodes = Array.isArray(source.nodes) ? source.nodes : []
  const links = Array.isArray(source.links) ? source.links : []
  const nodeMap = new Map()
  const childIdSet = new Set()

  nodes.forEach((item) => {
    const id = String(item?.id || '').trim()
    if (!id) {
      return
    }
    nodeMap.set(id, {
      value: id,
      label: String(item?.label || id).trim() || id,
      children: [],
    })
  })

  links.forEach((link) => {
    if (String(link?.type || '').trim() !== 'parent') {
      return
    }
    const parentId = String(link?.source || '').trim()
    const childId = String(link?.target || '').trim()
    if (!parentId || !childId || !nodeMap.has(parentId) || !nodeMap.has(childId) || parentId === childId) {
      return
    }
    nodeMap.get(parentId).children.push(nodeMap.get(childId))
    childIdSet.add(childId)
  })

  function sortTree(nodesTree) {
    return nodesTree
      .slice()
      .sort((left, right) => String(left.label || '').localeCompare(String(right.label || ''), 'zh-Hans-CN'))
      .map((item) => ({
        value: item.value,
        label: item.label,
        children: sortTree(item.children || []),
      }))
  }

  const roots = Array.from(nodeMap.values()).filter((node) => !childIdSet.has(node.value))
  const normalized = sortTree(roots)
  if (normalized.length) {
    return normalized
  }
  return sortTree(Array.from(nodeMap.values()))
}

async function loadClassOptions() {
  if (classOptions.value.length) {
    return
  }
  const response = await listTeacherPaperClasses()
  classOptions.value = normalizeClassOptions(unwrapData(response))
}

async function loadKnowledgeOptions() {
  if (knowledgeOptions.value.length) {
    return
  }
  const response = await knowledgeTree()
  knowledgeOptions.value = normalizeKnowledgeTreeOptions(unwrapData(response))
}

const { loading, run: loadFormOptions } = useRequest(
  async () => {
    await Promise.all([loadClassOptions(), loadKnowledgeOptions()])
  },
  {
    onError(error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || 'AI 参数配置项加载失败'))
    },
  },
)
const dialogBusy = computed(() => props.loading || props.loadingState || loading.value || props.generating)

function applyDefaultScopePathIfNeeded() {
  const options = Array.isArray(props.professionalOptions) ? props.professionalOptions : []
  const current_path = Array.isArray(aiForm.scope_path)
    ? aiForm.scope_path.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
    : []
  const current_scope_key = `${String(current_path[0] || '').trim()}::${String(current_path[1] || '').trim()}::${String(current_path[2] || '').trim()}`
  const scope_map = {}
  const group_scope_map = {}
  options.forEach((category_item) => {
    const category_code = String(category_item?.code || '').trim()
    ;(Array.isArray(category_item?.children) ? category_item.children : []).forEach((group_item) => {
      const group_code = String(group_item?.code || '').trim()
      if (category_code && group_code) {
        group_scope_map[`${category_code}::${group_code}`] = true
      }
      ;(Array.isArray(group_item?.children) ? group_item.children : []).forEach((subject_item) => {
        const subject_code = String(subject_item?.code || '').trim()
        if (!category_code || !group_code || !subject_code) {
          return
        }
        scope_map[`${category_code}::${group_code}::${subject_code}`] = true
      })
    })
  })
  const current_group_key = `${String(current_path[0] || '').trim()}::${String(current_path[1] || '').trim()}`
  if (current_path.length === 3 && scope_map[current_scope_key]) {
    return
  }
  if (current_path.length === 2 && group_scope_map[current_group_key]) {
    return
  }
  const first_category = options[0]
  const first_group = Array.isArray(first_category?.children) ? first_category.children[0] : null
  const default_scope_path = [
    String(first_category?.code || '').trim(),
    String(first_group?.code || '').trim(),
  ].filter((item) => Boolean(item))
  aiForm.scope_path = default_scope_path.length === 2 ? default_scope_path : []
}

function handleSubmit() {
  const scope_path = Array.isArray(aiForm.scope_path)
    ? aiForm.scope_path.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
    : []
  const [exam_category_code, joint_exam_group_code, subject_code] = scope_path.map((item) => String(item || '').trim())
  if (scope_path.length < 2 || !exam_category_code || !joint_exam_group_code) {
    ElMessage.warning('请先选择所属专业（学科门类 + 联考专业组）。')
    return
  }
  aiForm.exam_category_code = exam_category_code
  aiForm.joint_exam_group_code = joint_exam_group_code
  aiForm.subject_code = subject_code

  emit('start-generate', {
    scope_path,
    exam_category_code,
    joint_exam_group_code,
    subject_code,
    class_ids: Array.isArray(aiForm.class_ids)
      ? aiForm.class_ids.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
      : [],
    total_count: Number(aiForm.total_count || 0),
    difficulty_level: Number(aiForm.difficulty_level || 0),
    knowledge_scope: Array.isArray(aiForm.knowledge_scope)
      ? aiForm.knowledge_scope.map((item) => String(item || '').trim()).filter((item) => Boolean(item))
      : [],
  })
}

watch(
  () => visible.value,
  (nextVisible) => {
    if (nextVisible) {
      loadFormOptions()
      applyDefaultScopePathIfNeeded()
      return
    }
    if (!props.generating) {
      resetForm()
    }
  },
)

watch(
  () => props.professionalOptions,
  () => {
    applyDefaultScopePathIfNeeded()
  },
  { deep: true },
)
</script>

<template>
  <BaseDialog
    v-model="visible"
    :title="title"
    :width="width"
    :destroy-on-close="destroyOnClose"
    :close-on-click-modal="closeOnClickModal"
    :loading="dialogBusy"
    @cancel="handleCancel"
    @before-close="handleBeforeClose"
  >
    <slot
      :form="aiForm"
      :class-options="classOptions"
      :knowledge-options="knowledgeOptions"
      :loading="dialogBusy"
      :submit="handleSubmit"
    >
      <el-form label-width="122px" class="ai-form">
      <el-divider content-position="left">基础信息</el-divider>
      <el-form-item label="所属专业">
        <el-cascader
          v-model="aiForm.scope_path"
          :options="professionalOptions"
          :props="professionalCascaderProps"
          filterable
          clearable
          :teleported="false"
          expand-trigger="hover"
          :show-all-levels="false"
          :disabled="loading || generating"
          placeholder="请选择：学科门类 / 联考专业组，可继续下钻到考试科目"
        />
      </el-form-item>
      <el-form-item label="发布班级">
        <el-select
          v-model="aiForm.class_ids"
          multiple
          filterable
          clearable
          collapse-tags
          collapse-tags-tooltip
          :disabled="loading || generating"
          placeholder="请选择教师关联班级"
        >
          <el-option
            v-for="classItem in classOptions"
            :key="classItem.value"
            :label="classItem.label"
            :value="classItem.value"
          />
        </el-select>
      </el-form-item>

      <el-divider content-position="left">核心算法参数</el-divider>
      <el-form-item label="题量配置">
        <el-input-number
          v-model="aiForm.total_count"
          :min="10"
          :max="50"
          :step="1"
          :disabled="loading || generating"
          controls-position="right"
        />
      </el-form-item>
      <el-form-item label="知识点筛选">
        <el-tree-select
          v-model="aiForm.knowledge_scope"
          :data="knowledgeOptions"
          multiple
          show-checkbox
          check-strictly
          clearable
          collapse-tags
          collapse-tags-tooltip
          :render-after-expand="false"
          :disabled="loading || generating"
          placeholder="可勾选重点考察知识点（可选）"
        />
      </el-form-item>
      <el-form-item label="难度策略">
        <el-slider
          v-model="aiForm.difficulty_level"
          :min="1"
          :max="5"
          :step="1"
          :disabled="loading || generating"
          show-input
        />
        <p class="difficulty-hint">1-入门, 3-常规, 5-竞赛</p>
      </el-form-item>
      </el-form>
    </slot>

    <AiProgressBar
      v-if="generating"
      title="AI 组卷进度"
      :percentage="generationProgress"
      status-text="AI 正在根据大纲权重匹配最优题目..."
    />

    <template #footer>
      <slot name="footer" :cancel="handleCancel" :submit="handleSubmit" :loading="dialogBusy">
        <el-button :disabled="dialogBusy" @click="handleCancel">取消</el-button>
        <el-button type="success" :loading="props.generating" @click="handleSubmit">
          开始生成
        </el-button>
      </slot>
    </template>
  </BaseDialog>
</template>

<style scoped>
.ai-form {
  margin-top: 4px;
}

.difficulty-hint {
  margin: 6px 0 0;
  color: var(--qb-text-subtle-8);
  font-size: 12px;
}
</style>
