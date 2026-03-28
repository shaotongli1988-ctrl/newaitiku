<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRouter } from 'vue-router'
import { fetchStudentDashboard } from '../../api/services/student.js'
import QuestionBankActionGroup from '../../components/student/QuestionBankActionGroup.vue'
import QuestionBankEmptyState from '../../components/student/QuestionBankEmptyState.vue'
import QuestionBankPageHeader from '../../components/student/QuestionBankPageHeader.vue'
import QuestionBankSectionHeader from '../../components/student/QuestionBankSectionHeader.vue'
import StudentSyllabusMindmap from '../../components/student/StudentSyllabusMindmap.vue'
import { useRequest } from '../../composables/useRequest.js'
import { studentSyllabusCatalog } from '../../api/services/questionBank'
import { useUserStore } from '../../stores/userStore.js'
import {
  buildStudentSyllabusDisplayPlan,
  buildStudentSyllabusOverview,
  formatStudentSyllabusTimestamp,
  normalizeStudentCoreSubjects,
  normalizeStudentSyllabusCatalog,
} from '../../utils/studentSyllabusAtlas'

function unwrapData(response) {
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data
  }
  return response
}

function toText(value) {
  return String(value || '').trim()
}

const router = useRouter()
const userStore = useUserStore()
const catalog = ref(normalizeStudentSyllabusCatalog({}))
const coreSubjects = ref([])
const optionalSearchKeyword = ref('')

const displayPlan = computed(() => buildStudentSyllabusDisplayPlan(
  catalog.value,
  { coreSubjects: coreSubjects.value },
))
const requiredSubjects = computed(() => displayPlan.value.requiredSubjects)
const activeRequiredSubjectCode = ref('')
const activeOptionalSubjectCode = ref('')
const optionalSubjects = computed(() => {
  const keyword = toText(optionalSearchKeyword.value).toLowerCase()
  const rows = displayPlan.value.optionalSubjects
  if (!keyword) {
    return rows
  }
  return rows.filter((item) => [
    item.subjectName,
    item.subjectCode,
    item.examCategoryName,
    item.jointExamGroupName,
  ].map((value) => toText(value).toLowerCase()).some((value) => value.includes(keyword)))
})
const activeRequiredSubject = computed(() => {
  const activeCode = toText(activeRequiredSubjectCode.value)
  return requiredSubjects.value.find((item) => toText(item.subjectCode) === activeCode) || requiredSubjects.value[0] || null
})
const activeOptionalSubject = computed(() => {
  const activeCode = toText(activeOptionalSubjectCode.value)
  return optionalSubjects.value.find((item) => toText(item.subjectCode) === activeCode) || null
})

const overviewMetrics = computed(() => {
  const summary = buildStudentSyllabusOverview(catalog.value)
  return [
    { label: '考试科目', value: summary.subjectCount, helper: `覆盖 ${summary.examCategoryCount} 个考试门类` },
    { label: '大纲节点', value: summary.nodeCount, helper: `覆盖 ${summary.jointExamGroupCount} 个联考专业组` },
    { label: '当前必看', value: requiredSubjects.value.length, helper: '按当前报考范围完整展开' },
    { label: '折叠查阅', value: optionalSubjects.value.length, helper: '其余科目保留但默认收起' },
  ]
})

const scopeSummaryTitle = computed(() => {
  const examCategoryLabel = toText(
    requiredSubjects.value[0]?.examCategoryName
    || catalog.value.subjects.find((item) => toText(item.examCategoryCode) === toText(userStore.examCategoryCode))?.examCategoryName
    || userStore.examCategoryCode,
  )
  const jointExamGroupLabel = toText(
    requiredSubjects.value[0]?.jointExamGroupName
    || catalog.value.subjects.find((item) => toText(item.jointExamGroupCode) === toText(userStore.assignedJointGroupCode || userStore.jointExamGroupCode))?.jointExamGroupName
    || userStore.assignedJointGroupCode
    || userStore.jointExamGroupCode,
  )
  return [examCategoryLabel || '当前报考门类', jointExamGroupLabel || '当前专业组']
    .filter(Boolean)
    .join(' / ')
})

const scopeSummaryDescription = computed(() => {
  const subjectNames = requiredSubjects.value.map((item) => toText(item.subjectName)).filter(Boolean)
  if (!subjectNames.length) {
    return '系统会按你当前报考范围自动展开必看的考试大纲，并把其他科目保留为折叠查阅。先把必考范围看清，后面的刷题、积分和诊断才不会用力分散。'
  }
  return `当前默认完整展开 ${requiredSubjects.value.length} 门：${subjectNames.join('、')}。其余科目仍然保留，你可以按需展开补充查阅。先把高频必考范围看清，后面的练习积分才更容易刷在真正决定升本结果的点上。`
})

const syllabusHeaderDescription = computed(() => (
  '大纲不是只拿来阅读，它决定你接下来该把时间、刷题节奏和段位分优先压在哪些必考点上。'
))

const syllabusBridgeCopy = computed(() => {
  if (requiredSubjects.value.length) {
    return `先把当前报考范围内的 ${requiredSubjects.value.length} 门必考科目看清，再去刷题和看诊断，通常更容易把积分涨在真正影响升本结果的高频考点上。`
  }
  return '先把当前报考范围看清，再去刷题和看诊断，才能让后面的积分和训练更集中地落在关键考点上。'
})

const { loading, run: loadPage } = useRequest(
  async () => Promise.all([
    studentSyllabusCatalog(),
    fetchStudentDashboard().catch(() => null),
  ]),
  {
    onSuccess([catalogResponse, dashboardPayload]) {
      catalog.value = normalizeStudentSyllabusCatalog(unwrapData(catalogResponse) || {})
      coreSubjects.value = normalizeStudentCoreSubjects(dashboardPayload || {})
    },
    onError(error) {
      ElMessage.error(String(error?.response?.data?.message || error?.message || '考试大纲加载失败'))
    },
  },
)

function jumpToSubject(subjectCode) {
  selectRequiredSubject(subjectCode)
  const targetElement = document.getElementById('syllabus-required-panel')
  if (targetElement) {
    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function selectRequiredSubject(subjectCode) {
  const normalizedCode = toText(subjectCode)
  if (!normalizedCode) {
    return
  }
  const matched = requiredSubjects.value.find((item) => toText(item.subjectCode) === normalizedCode)
  if (matched) {
    activeRequiredSubjectCode.value = normalizedCode
  }
}

function toggleOptionalSubject(subjectCode) {
  const normalizedCode = toText(subjectCode)
  if (!normalizedCode) {
    return
  }
  activeOptionalSubjectCode.value = activeOptionalSubjectCode.value === normalizedCode ? '' : normalizedCode
}

async function openChallengePoints() {
  const subjectCode = toText(
    activeRequiredSubject.value?.subjectCode
    || requiredSubjects.value[0]?.subjectCode
    || coreSubjects.value[0]?.subjectCode,
  )
  await router.push({
    path: '/student/analysis/points',
    query: subjectCode ? { subjectCode } : {},
  })
}

watch(
  requiredSubjects,
  (subjects) => {
    const activeCode = toText(activeRequiredSubjectCode.value)
    if (!subjects.length) {
      activeRequiredSubjectCode.value = ''
      return
    }
    if (!subjects.some((item) => toText(item.subjectCode) === activeCode)) {
      activeRequiredSubjectCode.value = toText(subjects[0]?.subjectCode)
    }
  },
  { immediate: true },
)

watch(
  optionalSubjects,
  (subjects) => {
    const activeCode = toText(activeOptionalSubjectCode.value)
    if (!subjects.length) {
      activeOptionalSubjectCode.value = ''
      return
    }
    if (activeCode && !subjects.some((item) => toText(item.subjectCode) === activeCode)) {
      activeOptionalSubjectCode.value = ''
    }
  },
  { immediate: true },
)

loadPage()
</script>

<template>
  <section class="question-bank-syllabus-page" v-loading="loading">
    <section class="page-header-card">
      <QuestionBankPageHeader
        eyebrow="我的题库"
        title="考试大纲"
        :description="syllabusHeaderDescription"
      >
        <template #meta>
          <el-tag class="header-total-tag" effect="dark" type="primary">
            科目 {{ catalog.subjects.length }}
          </el-tag>
        </template>
        <template #actions>
          <QuestionBankActionGroup>
            <el-button plain @click="openChallengePoints">看刷题段位</el-button>
            <span v-if="catalog.generatedAt" class="header-meta">
              更新时间 {{ formatStudentSyllabusTimestamp(catalog.generatedAt) }}
            </span>
          </QuestionBankActionGroup>
        </template>
      </QuestionBankPageHeader>
    </section>

    <QuestionBankEmptyState
      v-if="!catalog.subjects.length"
      description="当前还没有可展示的考试大纲科目。"
    />

    <template v-else>
      <section class="scope-hero">
        <div class="scope-hero__copy">
          <span class="scope-hero__kicker">当前展开策略</span>
          <h3>{{ scopeSummaryTitle || '当前报考范围' }}</h3>
          <p>{{ scopeSummaryDescription }}</p>
          <div class="scope-hero__bridge">
            <strong>先看清考什么，再决定分往哪里刷</strong>
            <p>{{ syllabusBridgeCopy }}</p>
          </div>

          <div
            v-if="requiredSubjects.length"
            class="scope-hero__anchors"
            :class="{ 'scope-hero__anchors--quad': requiredSubjects.length === 4 }"
          >
            <button
              v-for="item in requiredSubjects"
              :key="item.subjectCode"
              type="button"
              class="scope-anchor"
              :class="{ 'scope-anchor--active': toText(activeRequiredSubject?.subjectCode) === toText(item.subjectCode) }"
              @click="jumpToSubject(item.subjectCode)"
            >
              <span>{{ item.subjectType === 'PUBLIC' ? '公共课' : '专业课' }}</span>
              <strong>{{ item.subjectName }}</strong>
            </button>
          </div>
        </div>

        <div class="overview-grid">
          <article
            v-for="item in overviewMetrics"
            :key="item.label"
            class="overview-card"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.helper }}</small>
          </article>
        </div>
      </section>

      <section class="featured-section">
        <QuestionBankSectionHeader
          kicker="平面切换"
          :title="`当前需要重点查看的 ${requiredSubjects.length} 门大纲`"
          description="必考科目集中放在同一个阅读平面里，通过切换器切换查看，避免上下反复滚动。"
        />

        <div v-if="requiredSubjects.length" class="featured-plane">
          <div
            class="featured-switcher"
            :class="{ 'featured-switcher--quad': requiredSubjects.length === 4 }"
            role="tablist"
            aria-label="必考大纲切换器"
          >
            <button
              v-for="item in requiredSubjects"
              :key="item.subjectCode"
              type="button"
              class="featured-switcher__button"
              :class="{ 'featured-switcher__button--active': toText(activeRequiredSubject?.subjectCode) === toText(item.subjectCode) }"
              :aria-selected="toText(activeRequiredSubject?.subjectCode) === toText(item.subjectCode)"
              @click="selectRequiredSubject(item.subjectCode)"
            >
              <span>{{ item.subjectType === 'PUBLIC' ? '公共课' : '专业课' }}</span>
              <strong>{{ item.subjectName }}</strong>
            </button>
          </div>

          <article
            v-if="activeRequiredSubject"
            id="syllabus-required-panel"
            :key="activeRequiredSubject.subjectCode"
            class="featured-plane__panel"
          >
            <StudentSyllabusMindmap
              :subject="activeRequiredSubject"
              featured
            />
          </article>
        </div>
      </section>

      <section class="optional-section">
        <div class="optional-section__header">
          <QuestionBankSectionHeader
            kicker="折叠保留"
            title="其他科目"
            description="其他科目也使用同一阅读平面，默认收起，点开后即可在下方切换查看，不打断当前主线。"
          />

          <div class="optional-section__toolbar">
            <el-input
              v-model="optionalSearchKeyword"
              class="optional-section__search"
              clearable
              placeholder="搜索其他科目"
            />
            <el-button
              v-if="activeOptionalSubject"
              plain
              @click="activeOptionalSubjectCode = ''"
            >
              收起大纲
            </el-button>
          </div>
        </div>

        <QuestionBankEmptyState
          v-if="!optionalSubjects.length"
          description="当前没有更多折叠科目可查阅。"
        />

        <template v-else>
          <div class="optional-switcher" role="tablist" aria-label="其他科目大纲切换器">
            <button
              v-for="item in optionalSubjects"
              :key="item.subjectCode"
              type="button"
              class="optional-switcher__button"
              :class="{ 'optional-switcher__button--active': toText(activeOptionalSubject?.subjectCode) === toText(item.subjectCode) }"
              :aria-selected="toText(activeOptionalSubject?.subjectCode) === toText(item.subjectCode)"
              @click="toggleOptionalSubject(item.subjectCode)"
            >
              <span>{{ item.subjectType === 'PUBLIC' ? '公共课' : '专业课' }}</span>
              <strong>{{ item.subjectName }}</strong>
              <small>{{ item.examCategoryName || item.examCategoryCode || '未分门类' }}</small>
            </button>
          </div>

          <QuestionBankEmptyState
            v-if="!activeOptionalSubject"
            description="大纲默认收起，点击上方任一科目即可展开查看。"
          />

          <article
            v-else
            :key="activeOptionalSubject.subjectCode"
            class="optional-plane__panel"
          >
            <StudentSyllabusMindmap :subject="activeOptionalSubject" />
          </article>
        </template>
      </section>
    </template>
  </section>
</template>

<style scoped>
.question-bank-syllabus-page {
  display: grid;
  gap: var(--qb-space-4-5);
}

.page-header-card,
.scope-hero,
.featured-section,
.optional-section {
  border: 1px solid var(--qb-border-primary-soft);
  border-radius: 28px;
  background: var(--qb-surface-strong);
  box-shadow: var(--qb-shadow-soft);
  padding: 24px;
}

.header-total-tag {
  border-radius: var(--qb-radius-pill);
  padding-inline: 14px;
  height: 34px;
}

.header-meta {
  color: var(--qb-text-copy);
  font-size: 12px;
}

.scope-hero {
  display: grid;
  gap: 22px;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  align-items: start;
  background:
    radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(243, 250, 249, 0.94));
}

.scope-hero__copy {
  display: grid;
  gap: 12px;
}

.scope-hero__bridge {
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(191, 219, 254, 0.52);
}

.scope-hero__bridge strong,
.scope-hero__bridge p {
  margin: 0;
}

.scope-hero__copy h3,
.scope-hero__copy p,
.overview-card span,
.overview-card small {
  margin: 0;
}

.scope-hero__kicker {
  display: inline-flex;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-subject-fallback-2) 10%, white 90%);
  color: var(--qb-subject-fallback-2);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.scope-hero__copy h3 {
  color: var(--qb-text-heading);
  font-size: 30px;
  line-height: 1.1;
}

.scope-hero__copy p {
  color: var(--qb-text-copy);
  font-size: 14px;
  line-height: 1.8;
  max-width: 760px;
}

.scope-hero__bridge p {
  line-height: 1.7;
  max-width: none;
}

.scope-hero__anchors {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.scope-hero__anchors--quad {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.scope-hero__anchors--quad .scope-anchor {
  min-width: 0;
}

.scope-anchor {
  display: grid;
  gap: 6px;
  min-width: 180px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--qb-subject-fallback-2) 16%, white 84%);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.scope-anchor:hover,
.scope-anchor:focus-visible {
  border-color: color-mix(in srgb, var(--qb-subject-fallback-2) 36%, white 64%);
  box-shadow: 0 14px 28px color-mix(in srgb, var(--qb-subject-fallback-2) 12%, transparent);
  transform: translateY(-2px);
  outline: none;
}

.scope-anchor--active {
  border-color: color-mix(in srgb, var(--qb-subject-fallback-2) 46%, white 54%);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), color-mix(in srgb, var(--qb-subject-fallback-2) 10%, white 90%));
  box-shadow: 0 16px 30px color-mix(in srgb, var(--qb-subject-fallback-2) 14%, transparent);
}

.scope-anchor span {
  color: var(--qb-subject-fallback-2);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.scope-anchor strong {
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.45;
}

.overview-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.overview-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid var(--qb-border-soft);
  background: rgba(255, 255, 255, 0.82);
}

.overview-card span,
.overview-card small {
  color: var(--qb-text-copy);
}

.overview-card strong {
  color: var(--qb-text-heading);
  font-size: 28px;
}

.featured-section,
.optional-section {
  display: grid;
  gap: 18px;
}

.featured-stack {
  display: grid;
  gap: 18px;
}

.featured-item {
  display: grid;
}

.featured-plane {
  display: grid;
  gap: 18px;
}

.featured-switcher {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.featured-switcher--quad {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.featured-switcher__button {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid var(--qb-border-soft);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.featured-switcher__button:hover,
.featured-switcher__button:focus-visible {
  border-color: color-mix(in srgb, var(--qb-subject-fallback-2) 32%, white 68%);
  transform: translateY(-1px);
  outline: none;
}

.featured-switcher__button--active {
  border-color: color-mix(in srgb, var(--qb-subject-fallback-2) 42%, white 58%);
  background:
    radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 54%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(243, 250, 249, 0.94));
  box-shadow: 0 16px 32px color-mix(in srgb, var(--qb-subject-fallback-2) 12%, transparent);
}

.featured-switcher__button span {
  color: var(--qb-subject-fallback-2);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.featured-switcher__button strong {
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.45;
}

.featured-plane__panel {
  display: grid;
}

.optional-section__header {
  display: grid;
  gap: 16px;
}

.optional-section__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.optional-section__search {
  width: min(360px, 100%);
}

.optional-switcher {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.optional-switcher__button {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid var(--qb-border-soft);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.optional-switcher__button:hover,
.optional-switcher__button:focus-visible {
  border-color: color-mix(in srgb, var(--qb-subject-fallback-1) 32%, white 68%);
  transform: translateY(-1px);
  outline: none;
}

.optional-switcher__button--active {
  border-color: color-mix(in srgb, var(--qb-subject-fallback-1) 42%, white 58%);
  background:
    radial-gradient(circle at top right, rgba(217, 119, 6, 0.1), transparent 52%),
    linear-gradient(180deg, rgba(255, 252, 245, 0.98), rgba(255, 247, 237, 0.94));
  box-shadow: 0 16px 32px color-mix(in srgb, var(--qb-subject-fallback-1) 12%, transparent);
}

.optional-switcher__button span {
  color: var(--qb-subject-fallback-1);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.optional-switcher__button strong,
.optional-switcher__button small {
  margin: 0;
}

.optional-switcher__button strong {
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.45;
}

.optional-switcher__button small {
  color: var(--qb-text-copy);
  font-size: 12px;
}

.optional-plane__panel {
  display: grid;
}

@media (max-width: 1100px) {
  .scope-hero {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-header-card,
  .scope-hero,
  .featured-section,
  .optional-section {
    padding: 18px;
  }

  .scope-hero__copy h3 {
    font-size: 24px;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .scope-anchor,
  .featured-switcher__button,
  .optional-switcher__button {
    min-width: 0;
    width: 100%;
  }

  .scope-hero__anchors--quad,
  .featured-switcher--quad {
    grid-template-columns: 1fr;
  }

  .optional-section__toolbar {
    align-items: stretch;
  }

  .optional-section__search {
    width: 100%;
  }
}
</style>
