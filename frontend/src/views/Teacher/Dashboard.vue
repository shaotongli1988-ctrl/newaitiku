<script setup>
import { computed, defineAsyncComponent, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import KnowledgeTree from '../../components/core/KnowledgeTree.vue'
import QuestionCard from '../../components/core/QuestionCard.vue'
import { fetchAnalyticsSummary } from '../../api/services/student'
import {
  fetchContentBaseline,
  fetchQuestionList,
} from '../../api/services/questionBank'
import { useUserStore } from '../../stores/userStore.js'
import {
  filterJointExamGroupOptions,
  filterSubjectCodeOptions,
  normalizeContentBaseline,
} from '../../utils/contentBaseline'

const AnalyticsCharts = defineAsyncComponent(() => import('../../components/core/AnalyticsCharts.vue'))

const userStore = useUserStore()
const treeRef = ref(null)
const loadingQuestions = ref(false)
const loadingSummary = ref(false)
const selectedKnowledgeId = ref('')
const questionRows = ref([])
const page = ref(1)
const size = ref(8)
const total = ref(0)
const analyticsSummary = ref({})

const dictionaryState = reactive({
  examCategoryOptions: [],
  jointExamGroupOptions: [],
  subjectCodeOptions: [],
})

const filters = reactive({
  examCategoryCode: '',
  jointExamGroupCode: '',
  subjectCode: '',
  status: '',
  type: '',
  keyword: '',
})

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'DRAFT', label: '草稿' },
  { value: 'QA_IN_PROGRESS', label: 'QA 互审中' },
  { value: 'REVIEW_PENDING', label: '待终审' },
  { value: 'PUBLISHED', label: '已发布' },
  { value: 'REJECTED', label: '已驳回' },
]

const typeOptions = [
  { value: '', label: '全部题型' },
  { value: 'single_choice', label: '单选题' },
  { value: 'multiple_choice', label: '多选题' },
  { value: 'judge', label: '判断题' },
  { value: 'subjective', label: '主观题' },
]

const canViewAnalytics = computed(() => userStore.hasPermission('analytics:view'))
const totalPage = computed(() => Math.max(1, Math.ceil(total.value / size.value)))

const filteredJointExamGroupOptions = computed(() =>
  filterJointExamGroupOptions(dictionaryState.jointExamGroupOptions, filters.examCategoryCode),
)

const filteredSubjectCodeOptions = computed(() =>
  filterSubjectCodeOptions(
    dictionaryState.subjectCodeOptions,
    filters.examCategoryCode,
    filters.jointExamGroupCode,
  ),
)

async function loadDictionary() {
  try {
    const baseline = await fetchContentBaseline()
    const normalized = normalizeContentBaseline(baseline?.data || baseline)
    dictionaryState.examCategoryOptions = normalized.examCategoryOptions
    dictionaryState.jointExamGroupOptions = normalized.jointExamGroupOptions
    dictionaryState.subjectCodeOptions = normalized.subjectCodeOptions
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '内容字典加载失败')
  }
}

async function loadQuestions() {
  loadingQuestions.value = true
  try {
    const pageData = await fetchQuestionList({
      page: page.value,
      size: size.value,
      keyword: filters.keyword,
      status: filters.status,
      type: filters.type,
      knowledgeId: selectedKnowledgeId.value,
      examCategoryCode: filters.examCategoryCode,
      jointExamGroupCode: filters.jointExamGroupCode,
      subjectCode: filters.subjectCode,
    })
    questionRows.value = pageData.items
    total.value = pageData.total
  } catch (error) {
    questionRows.value = []
    total.value = 0
    ElMessage.error(error?.response?.data?.message || error?.message || '题目列表加载失败')
  } finally {
    loadingQuestions.value = false
  }
}

async function loadAnalyticsSummary() {
  if (!canViewAnalytics.value) {
    return
  }
  loadingSummary.value = true
  try {
    analyticsSummary.value = await fetchAnalyticsSummary({
      keyword: filters.keyword,
      examCategoryCode: filters.examCategoryCode,
      jointExamGroupCode: filters.jointExamGroupCode,
      subjectCode: filters.subjectCode,
    })
  } catch (error) {
    analyticsSummary.value = {}
    ElMessage.error(error?.response?.data?.message || error?.message || '学情摘要加载失败')
  } finally {
    loadingSummary.value = false
  }
}

async function reloadByFilter() {
  page.value = 1
  await loadQuestions()
  await loadAnalyticsSummary()
}

function handleKnowledgeNodeSelected(nodeData) {
  selectedKnowledgeId.value = String(nodeData?.id || '')
  reloadByFilter()
}

function handleQuestionStatusUpdated() {
  loadQuestions()
}

function resetFilters() {
  filters.examCategoryCode = ''
  filters.jointExamGroupCode = ''
  filters.subjectCode = ''
  filters.status = ''
  filters.type = ''
  filters.keyword = ''
  selectedKnowledgeId.value = ''
  treeRef.value?.reloadTree?.()
  reloadByFilter()
}

watch(
  () => filters.examCategoryCode,
  () => {
    if (
      !filteredJointExamGroupOptions.value.some(
        (optionItem) => optionItem.jointExamGroupCode === filters.jointExamGroupCode,
      )
    ) {
      filters.jointExamGroupCode = ''
    }
    if (
      !filteredSubjectCodeOptions.value.some(
        (optionItem) => optionItem.subjectCode === filters.subjectCode,
      )
    ) {
      filters.subjectCode = ''
    }
  },
)

watch(
  () => filters.jointExamGroupCode,
  () => {
    if (
      !filteredSubjectCodeOptions.value.some(
        (optionItem) => optionItem.subjectCode === filters.subjectCode,
      )
    ) {
      filters.subjectCode = ''
    }
  },
)

onMounted(async () => {
  userStore.bootstrapFromStorage()
  await loadDictionary()
  await reloadByFilter()
})
</script>

<template>
  <section class="teacher-dashboard">
    <el-card class="filter-card" shadow="never">
      <template #header>
        <div class="card-header">
          <h3>题目筛选（字典化）</h3>
          <div class="header-actions">
            <el-button @click="resetFilters">重置</el-button>
            <el-button type="primary" @click="reloadByFilter">查询</el-button>
          </div>
        </div>
      </template>

      <div class="filter-grid">
        <el-select v-model="filters.examCategoryCode" clearable placeholder="学科门类">
          <el-option
            v-for="examCategoryItem in dictionaryState.examCategoryOptions"
            :key="examCategoryItem.examCategoryCode"
            :label="examCategoryItem.examCategoryName"
            :value="examCategoryItem.examCategoryCode"
          />
        </el-select>

        <el-select v-model="filters.jointExamGroupCode" clearable placeholder="联考专业组">
          <el-option
            v-for="jointExamGroupItem in filteredJointExamGroupOptions"
            :key="jointExamGroupItem.jointExamGroupCode"
            :label="jointExamGroupItem.jointExamGroupName"
            :value="jointExamGroupItem.jointExamGroupCode"
          />
        </el-select>

        <el-select v-model="filters.subjectCode" clearable placeholder="考试科目">
          <el-option
            v-for="subjectItem in filteredSubjectCodeOptions"
            :key="subjectItem.subjectCode"
            :label="subjectItem.subjectName"
            :value="subjectItem.subjectCode"
          />
        </el-select>

        <el-select v-model="filters.status" placeholder="题目状态">
          <el-option
            v-for="statusItem in statusOptions"
            :key="statusItem.value || 'status-all'"
            :label="statusItem.label"
            :value="statusItem.value"
          />
        </el-select>

        <el-select v-model="filters.type" placeholder="题目类型">
          <el-option
            v-for="typeItem in typeOptions"
            :key="typeItem.value || 'type-all'"
            :label="typeItem.label"
            :value="typeItem.value"
          />
        </el-select>

        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="关键词（题干/解析/知识点）"
        />
      </div>
    </el-card>

    <section class="workbench">
      <KnowledgeTree
        ref="treeRef"
        v-model:selectedKnowledgeId="selectedKnowledgeId"
        class="tree-column"
        @node-selected="handleKnowledgeNodeSelected"
      />

      <el-card class="question-column" shadow="never">
        <template #header>
          <div class="card-header">
            <h3>万能题目卡片</h3>
            <span>第 {{ page }} / {{ totalPage }} 页，共 {{ total }} 题</span>
          </div>
        </template>

        <el-skeleton v-if="loadingQuestions" :rows="7" animated />
        <el-empty v-else-if="!questionRows.length" description="当前筛选条件下暂无题目" />
        <div v-else class="question-grid">
          <QuestionCard
            v-for="questionItem in questionRows"
            :key="questionItem.id"
            :question="questionItem"
            :current-user-id="userStore.userId"
            @status-updated="handleQuestionStatusUpdated"
          />
        </div>

        <footer class="pagination-footer">
          <el-button :disabled="page <= 1" @click="page -= 1; loadQuestions()">上一页</el-button>
          <el-button :disabled="page >= totalPage" @click="page += 1; loadQuestions()">下一页</el-button>
        </footer>
      </el-card>
    </section>

    <el-card
      v-if="canViewAnalytics"
      class="analytics-card"
      shadow="never"
    >
      <template #header>
        <div class="card-header">
          <h3>数据可视化看板</h3>
          <el-button text :loading="loadingSummary" @click="loadAnalyticsSummary">刷新看板</el-button>
        </div>
      </template>
      <AnalyticsCharts :summary="analyticsSummary" />
    </el-card>
  </section>
</template>

<style scoped>
.teacher-dashboard {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.card-header h3 {
  margin: 0;
  color: var(--qb-text-heading);
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.workbench {
  display: grid;
  grid-template-columns: minmax(290px, 340px) minmax(0, 1fr);
  gap: 12px;
}

.question-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
}

.pagination-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1100px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workbench {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 700px) {
  .filter-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
