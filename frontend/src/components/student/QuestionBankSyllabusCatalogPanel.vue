<script setup>
import { computed } from 'vue'
import QuestionBankActionGroup from './QuestionBankActionGroup.vue'
import QuestionBankEmptyState from './QuestionBankEmptyState.vue'

const props = defineProps({
  searchKeyword: {
    type: String,
    default: '',
  },
  subjectTypeFilter: {
    type: String,
    default: 'ALL',
  },
  examCategoryFilter: {
    type: String,
    default: '',
  },
  subjectTypeOptions: {
    type: Array,
    default: () => [],
  },
  examCategoryOptions: {
    type: Array,
    default: () => [],
  },
  filteredSubjects: {
    type: Array,
    default: () => [],
  },
  activeSubjectCode: {
    type: String,
    default: '',
  },
  totalSubjectCount: {
    type: Number,
    default: 0,
  },
  hiddenSelectionLabel: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'update:searchKeyword',
  'update:subjectTypeFilter',
  'update:examCategoryFilter',
  'select-subject',
  'reset-filters',
  'clear-hidden-filters',
])

const resultSummary = computed(() => (
  `当前显示 ${props.filteredSubjects.length} / ${props.totalSubjectCount} 个科目`
))

function isActiveSubject(subjectCode) {
  return String(props.activeSubjectCode || '').trim() === String(subjectCode || '').trim()
}
</script>

<template>
  <section class="syllabus-catalog-panel">
    <header class="syllabus-catalog-panel__header">
      <div>
        <span class="syllabus-catalog-panel__kicker">查阅入口</span>
        <h4>全部考试科目</h4>
        <p>先定位目标科目，再在右侧查看对应大纲结构。页面保持全科总览定位，不跟随当前练习科目切换。</p>
      </div>
      <span class="syllabus-catalog-panel__summary">{{ resultSummary }}</span>
    </header>

    <div class="syllabus-catalog-panel__toolbar">
      <el-input
        :model-value="searchKeyword"
        clearable
        class="syllabus-catalog-panel__search"
        placeholder="搜索科目名称 / 科目编码 / 门类 / 专业组"
        @update:model-value="emit('update:searchKeyword', $event)"
      />
      <el-select
        :model-value="subjectTypeFilter"
        class="syllabus-catalog-panel__select"
        @update:model-value="emit('update:subjectTypeFilter', $event)"
      >
        <el-option
          v-for="item in subjectTypeOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select
        :model-value="examCategoryFilter"
        class="syllabus-catalog-panel__select"
        @update:model-value="emit('update:examCategoryFilter', $event)"
      >
        <el-option
          v-for="item in examCategoryOptions"
          :key="item.value || 'ALL'"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
    </div>

    <div v-if="hiddenSelectionLabel" class="syllabus-catalog-panel__hidden-tip">
      <div>
        <strong>{{ hiddenSelectionLabel }}</strong>
        <p>当前科目已被筛选隐藏，你仍在查看它的详情。清除筛选后可重新回到目录中。</p>
      </div>
      <el-button plain @click="emit('clear-hidden-filters')">清除筛选</el-button>
    </div>

    <div v-if="filteredSubjects.length" class="syllabus-catalog-panel__list">
      <button
        v-for="item in filteredSubjects"
        :key="item.subjectCode"
        type="button"
        class="catalog-subject-card"
        :class="{ 'catalog-subject-card--active': isActiveSubject(item.subjectCode) }"
        @click="emit('select-subject', item.subjectCode)"
      >
        <div class="catalog-subject-card__topline">
          <span class="catalog-subject-card__type">
            {{ item.subjectType === 'PUBLIC' ? '公共课' : '专业课' }}
          </span>
          <span v-if="item.nodeCount" class="catalog-subject-card__count">{{ item.nodeCount }} 节点</span>
        </div>
        <strong>{{ item.subjectName }}</strong>
        <small>{{ item.examCategoryName || item.examCategoryCode || '未分考试门类' }}</small>
        <small>{{ item.jointExamGroupName || item.jointExamGroupCode || '全局共享' }}</small>
      </button>
    </div>

    <QuestionBankEmptyState
      v-else
      description="当前筛选条件下没有匹配的考试科目"
    >
      <template #actions>
        <QuestionBankActionGroup compact>
          <el-button plain @click="emit('reset-filters')">重置筛选</el-button>
        </QuestionBankActionGroup>
      </template>
    </QuestionBankEmptyState>
  </section>
</template>

<style scoped>
.syllabus-catalog-panel {
  display: grid;
  gap: 18px;
}

.syllabus-catalog-panel__header {
  display: grid;
  gap: 14px;
}

.syllabus-catalog-panel__header h4,
.syllabus-catalog-panel__header p,
.syllabus-catalog-panel__hidden-tip p,
.catalog-subject-card strong,
.catalog-subject-card small {
  margin: 0;
}

.syllabus-catalog-panel__kicker {
  display: inline-flex;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  color: var(--qb-primary-student);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.syllabus-catalog-panel__header h4 {
  margin-top: 10px;
  color: var(--qb-text-heading);
  font-size: 24px;
  line-height: 1.2;
}

.syllabus-catalog-panel__header p {
  margin-top: 8px;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.75;
}

.syllabus-catalog-panel__summary {
  color: var(--qb-text-meta);
  font-size: 12px;
  font-weight: 700;
}

.syllabus-catalog-panel__toolbar {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1.4fr) repeat(2, minmax(140px, 0.8fr));
}

.syllabus-catalog-panel__search,
.syllabus-catalog-panel__select {
  width: 100%;
}

.syllabus-catalog-panel__hidden-tip {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--qb-warning) 26%, white 74%);
  border-radius: 18px;
  background: color-mix(in srgb, var(--qb-warning) 8%, white 92%);
}

.syllabus-catalog-panel__hidden-tip strong {
  color: var(--qb-text-heading);
  font-size: 13px;
}

.syllabus-catalog-panel__hidden-tip p {
  margin-top: 6px;
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.65;
}

.syllabus-catalog-panel__list {
  display: grid;
  gap: 12px;
}

.catalog-subject-card {
  display: grid;
  gap: 8px;
  min-width: 0;
  padding: 16px 18px;
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--qb-primary-student) 10%, white 90%), transparent 30%),
    linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 255, 0.95));
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.catalog-subject-card:hover,
.catalog-subject-card:focus-visible,
.catalog-subject-card--active {
  border-color: color-mix(in srgb, var(--qb-primary-student) 42%, white 58%);
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.12);
  transform: translateY(-2px);
}

.catalog-subject-card:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--qb-primary-student) 45%, white 55%);
  outline-offset: 2px;
}

.catalog-subject-card__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.catalog-subject-card__type,
.catalog-subject-card__count {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.catalog-subject-card__type {
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  color: var(--qb-primary-student);
}

.catalog-subject-card__count {
  background: color-mix(in srgb, var(--qb-success) 10%, white 90%);
  color: color-mix(in srgb, var(--qb-success) 82%, black 18%);
}

.catalog-subject-card strong {
  color: var(--qb-text-heading);
  font-size: 16px;
  line-height: 1.55;
}

.catalog-subject-card small {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 980px) {
  .syllabus-catalog-panel__toolbar {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .syllabus-catalog-panel__hidden-tip {
    flex-direction: column;
  }

  .syllabus-catalog-panel__hidden-tip :deep(.el-button) {
    width: 100%;
  }
}
</style>
