<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '筛选器',
  },
  modelValue: {
    type: Object,
    default: null,
  },
  keyword: {
    type: String,
    default: '',
  },
  categoryId: {
    type: String,
    default: '',
  },
  categoryOptions: {
    type: Array,
    default: () => [],
  },
  examCategoryOptions: {
    type: Array,
    default: () => [],
  },
  jointExamGroupOptions: {
    type: Array,
    default: () => [],
  },
  subjectCodeOptions: {
    type: Array,
    default: () => [],
  },
  enableSubjectCode: {
    type: Boolean,
    default: false,
  },
  initiallyCollapsed: {
    type: Boolean,
    default: false,
  },
  keywordPlaceholder: {
    type: String,
    default: '输入关键词',
  },
  examCategoryPlaceholder: {
    type: String,
    default: '学科门类',
  },
  jointExamGroupPlaceholder: {
    type: String,
    default: '专业组',
  },
  subjectCodePlaceholder: {
    type: String,
    default: '考试科目',
  },
  searchText: {
    type: String,
    default: '查询',
  },
  resetText: {
    type: String,
    default: '重置',
  },
})

const emit = defineEmits([
  'update:modelValue',
  'update:keyword',
  'update:categoryId',
  'search',
  'reset',
])

const collapsed = ref(props.initiallyCollapsed)
const localFilters = reactive({
  keyword: '',
  examCategoryCode: '',
  jointExamGroupCode: '',
  subjectCode: '',
  categoryId: '',
})

const mergedExamCategoryOptions = computed(() => {
  if (Array.isArray(props.examCategoryOptions) && props.examCategoryOptions.length) {
    return props.examCategoryOptions
  }
  return (Array.isArray(props.categoryOptions) ? props.categoryOptions : []).map((item) => ({
    examCategoryCode: String(item?.examCategoryCode || item?.id || '').trim(),
    examCategoryName: String(item?.examCategoryName || item?.name || item?.id || '').trim(),
    jointExamGroups: Array.isArray(item?.jointExamGroups) ? item.jointExamGroups : [],
  }))
})

const jointExamGroupOptions = computed(() => {
  const matchedExamCategory = mergedExamCategoryOptions.value.find(
    (examCategoryItem) =>
      String(examCategoryItem?.examCategoryCode || '') === localFilters.examCategoryCode,
  )
  return Array.isArray(matchedExamCategory?.jointExamGroups)
    ? matchedExamCategory.jointExamGroups
    : []
})

const filteredSubjectCodeOptions = computed(() => {
  const selectedExamCategoryCode = String(localFilters.examCategoryCode || '').trim()
  const selectedJointExamGroupCode = String(localFilters.jointExamGroupCode || '').trim()

  const uniqueBySubjectCode = new Map()
  ;(Array.isArray(props.subjectCodeOptions) ? props.subjectCodeOptions : []).forEach((subjectItem) => {
    const subjectCode = String(subjectItem?.subjectCode || '').trim()
    if (!subjectCode) {
      return
    }

    const subjectExamCategoryCode = String(subjectItem?.examCategoryCode || '').trim()
    const subjectJointExamGroupCode = String(subjectItem?.jointExamGroupCode || '').trim()
    const subjectType = String(subjectItem?.subjectType || '').trim()

    if (selectedExamCategoryCode && subjectExamCategoryCode && subjectExamCategoryCode !== selectedExamCategoryCode) {
      return
    }

    if (
      selectedJointExamGroupCode
      && subjectType !== 'PUBLIC'
      && subjectJointExamGroupCode
      && subjectJointExamGroupCode !== selectedJointExamGroupCode
    ) {
      return
    }

    if (!uniqueBySubjectCode.has(subjectCode)) {
      uniqueBySubjectCode.set(subjectCode, {
        subjectCode,
        subjectName: String(subjectItem?.subjectName || subjectCode),
      })
    }
  })

  return Array.from(uniqueBySubjectCode.values())
})

function syncLocalFilters() {
  const source = props.modelValue && typeof props.modelValue === 'object'
    ? props.modelValue
    : {
      keyword: props.keyword,
      categoryId: props.categoryId,
    }
  localFilters.keyword = String(source?.keyword || '')
  localFilters.examCategoryCode = String(source?.examCategoryCode || source?.categoryId || '')
  localFilters.jointExamGroupCode = String(source?.jointExamGroupCode || '')
  localFilters.subjectCode = String(source?.subjectCode || '')
  localFilters.categoryId = String(source?.categoryId || source?.examCategoryCode || '')
}

watch(
  () => props.modelValue,
  () => {
    syncLocalFilters()
  },
  { immediate: true, deep: true },
)

watch(
  () => [props.keyword, props.categoryId],
  () => {
    if (!props.modelValue) {
      syncLocalFilters()
    }
  },
)

watch(
  () => localFilters.examCategoryCode,
  () => {
    localFilters.categoryId = localFilters.examCategoryCode
    const hasCurrentJointExamGroup = jointExamGroupOptions.value.some(
      (jointExamGroupItem) =>
        String(jointExamGroupItem?.jointExamGroupCode || '') === localFilters.jointExamGroupCode,
    )
    if (!hasCurrentJointExamGroup) {
      localFilters.jointExamGroupCode = ''
    }

    const hasCurrentSubjectCode = filteredSubjectCodeOptions.value.some(
      (subjectItem) => subjectItem.subjectCode === localFilters.subjectCode,
    )
    if (!hasCurrentSubjectCode) {
      localFilters.subjectCode = ''
    }
  },
)

watch(
  () => localFilters.jointExamGroupCode,
  () => {
    const hasCurrentSubjectCode = filteredSubjectCodeOptions.value.some(
      (subjectItem) => subjectItem.subjectCode === localFilters.subjectCode,
    )
    if (!hasCurrentSubjectCode) {
      localFilters.subjectCode = ''
    }
  },
)

function emitFilterModel() {
  const payload = {
    keyword: localFilters.keyword,
    examCategoryCode: localFilters.examCategoryCode,
    jointExamGroupCode: localFilters.jointExamGroupCode,
    subjectCode: localFilters.subjectCode,
    categoryId: localFilters.categoryId || localFilters.examCategoryCode,
  }
  emit('update:modelValue', payload)
  emit('update:keyword', payload.keyword)
  emit('update:categoryId', payload.categoryId)
  return payload
}

function handleSearch() {
  emit('search', emitFilterModel())
}

function handleReset() {
  localFilters.keyword = ''
  localFilters.examCategoryCode = ''
  localFilters.jointExamGroupCode = ''
  localFilters.subjectCode = ''
  localFilters.categoryId = ''
  emitFilterModel()
  emit('reset')
}

function togglePanel() {
  collapsed.value = !collapsed.value
}
</script>

<template>
  <section class="filter-panel">
    <header class="panel-header">
      <h3>{{ title }}</h3>
      <el-button text @click="togglePanel">
        {{ collapsed ? '展开筛选' : '收起筛选' }}
      </el-button>
    </header>

    <el-collapse-transition>
      <div v-show="!collapsed" class="panel-body">
        <div class="filter-grid">
          <slot
            name="fields"
            :filters="localFilters"
            :exam-category-options="mergedExamCategoryOptions"
            :joint-exam-group-options="jointExamGroupOptions"
            :subject-code-options="filteredSubjectCodeOptions"
          >
            <el-input
              v-model="localFilters.keyword"
              clearable
              :placeholder="keywordPlaceholder"
            />

            <el-select
              v-model="localFilters.examCategoryCode"
              clearable
              filterable
              :placeholder="examCategoryPlaceholder"
            >
              <el-option
                v-for="option in mergedExamCategoryOptions"
                :key="option.examCategoryCode"
                :label="option.examCategoryName"
                :value="option.examCategoryCode"
              />
            </el-select>

            <el-select
              v-model="localFilters.jointExamGroupCode"
              clearable
              filterable
              :disabled="!localFilters.examCategoryCode"
              :placeholder="jointExamGroupPlaceholder"
            >
              <el-option
                v-for="option in jointExamGroupOptions"
                :key="option.jointExamGroupCode"
                :label="option.jointExamGroupName"
                :value="option.jointExamGroupCode"
              />
            </el-select>

            <el-select
              v-if="enableSubjectCode"
              v-model="localFilters.subjectCode"
              clearable
              filterable
              :placeholder="subjectCodePlaceholder"
            >
              <el-option
                v-for="option in filteredSubjectCodeOptions"
                :key="option.subjectCode"
                :label="option.subjectName"
                :value="option.subjectCode"
              />
            </el-select>
          </slot>
        </div>

        <slot name="advanced" :filters="localFilters" />

        <div class="panel-actions">
          <slot name="actions" :search="handleSearch" :reset="handleReset">
            <el-button type="primary" @click="handleSearch">{{ searchText }}</el-button>
            <el-button @click="handleReset">{{ resetText }}</el-button>
          </slot>
        </div>
      </div>
    </el-collapse-transition>
  </section>
</template>

<style scoped>
.filter-panel {
  border: 1px solid var(--qb-primary-soft-border);
  border-radius: 12px;
  background: linear-gradient(180deg, var(--qb-bg-card) 0%, var(--qb-primary-soft-bg) 100%);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px dashed var(--qb-primary-soft-border);
}

.panel-header h3 {
  margin: 0;
  font-size: 15px;
  color: var(--qb-text-emphasis);
}

.panel-body {
  padding: 12px 14px 14px;
  display: grid;
  gap: 12px;
}

.filter-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(4, minmax(140px, 1fr));
}

.panel-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
