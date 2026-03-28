<script setup>
import { computed } from 'vue'
import KnowledgeGraphFlowSurface from '../KnowledgeGraphFlowSurface.vue'
import { buildStudentSyllabusGraphPayload } from '../../utils/studentSyllabusAtlas'
import {
  buildKnowledgeDisplayLabel,
  buildTeacherAutoLayout,
  buildTeacherContentOutlineTree,
  buildTeacherExamSectionSummary,
  buildTeacherKnowledgeIndex,
  resolveTeacherSpecialSections,
} from '../../utils/knowledgeGraphTeacher'

defineOptions({
  name: 'StudentSyllabusMindmap',
})

const props = defineProps({
  subject: {
    type: Object,
    default: () => ({}),
  },
  featured: {
    type: Boolean,
    default: false,
  },
})

function toText(value) {
  return String(value || '').trim()
}

function resolveNodeRole(nodeId, level, specialSections) {
  if (nodeId === toText(specialSections?.subjectRootId)) {
    return 'subject'
  }
  if (nodeId === toText(specialSections?.contentNodeId)) {
    return 'focus'
  }
  if (Number(level || 0) >= 5) {
    return 'leaf'
  }
  return 'branch'
}

const branchPalette = [
  'var(--qb-branch-color-1)',
  'var(--qb-branch-color-2)',
  'var(--qb-branch-color-3)',
  'var(--qb-branch-color-4)',
  'var(--qb-branch-color-5)',
  'var(--qb-branch-color-6)',
]

const graphPayload = computed(() => buildStudentSyllabusGraphPayload(props.subject || {}))
const teacherIndex = computed(() => buildTeacherKnowledgeIndex(graphPayload.value))
const specialSections = computed(() => resolveTeacherSpecialSections(teacherIndex.value))
const examSummary = computed(() => buildTeacherExamSectionSummary(teacherIndex.value))
const contentOutline = computed(() => buildTeacherContentOutlineTree(teacherIndex.value))
const allNodeIds = computed(() =>
  teacherIndex.value.allNodes.map((item) => toText(item?.id)).filter(Boolean),
)
const layoutMap = computed(() => buildTeacherAutoLayout(
  teacherIndex.value,
  allNodeIds.value,
  {
    xStart: 120,
    yStart: 110,
    xGap: 240,
    yGap: 90,
  },
))
const rootBranchIds = computed(() => (
  teacherIndex.value.childrenByParent.get(toText(specialSections.value.subjectRootId)) || []
))

function resolveBranchColor(nodeId) {
  const normalizedNodeId = toText(nodeId)
  if (!normalizedNodeId || !rootBranchIds.value.length) {
    return ''
  }
  if (rootBranchIds.value.includes(normalizedNodeId)) {
    return branchPalette[rootBranchIds.value.indexOf(normalizedNodeId) % branchPalette.length]
  }
  let currentId = normalizedNodeId
  while (currentId) {
    const parentId = toText(teacherIndex.value.parentByChild.get(currentId))
    if (!parentId) {
      break
    }
    if (rootBranchIds.value.includes(parentId)) {
      return branchPalette[rootBranchIds.value.indexOf(parentId) % branchPalette.length]
    }
    currentId = parentId
  }
  return ''
}

const nodes = computed(() => graphPayload.value.nodes.map((item, index) => {
  const id = toText(item?.id)
  const level = Number(item?.level || 0)
  return {
    id,
    type: 'knowledge',
    position: layoutMap.value.get(id) || {
      x: 120 + ((index % 4) * 220),
      y: 110 + (Math.floor(index / 4) * 88),
    },
    data: {
      id,
      label: buildKnowledgeDisplayLabel(item?.label || id, level <= 2 ? 18 : 14),
      fullLabel: toText(item?.label || id),
      level,
      mastery: 1,
      questionCount: 0,
      size: level <= 1 ? 46 : (level === 2 ? 34 : (level === 3 ? 26 : 18)),
      isActive: id === toText(specialSections.value.contentNodeId),
      isHighlighted: false,
      showHandles: false,
      emphasisMode: 'teacher',
      nodeRole: resolveNodeRole(id, level, specialSections.value),
      branchColor: resolveBranchColor(id),
    },
  }
}))

const edges = computed(() => graphPayload.value.links.map((item) => {
  const source = toText(item?.source)
  const target = toText(item?.target)
  const branchColor = resolveBranchColor(target) || resolveBranchColor(source)
  const sourceLevel = Number(teacherIndex.value.nodesById.get(source)?.level || 0)
  const targetLevel = Number(teacherIndex.value.nodesById.get(target)?.level || 0)

  return {
    id: `parent:${source}->${target}`,
    source,
    target,
    type: 'smoothstep',
    pathOptions: {
      borderRadius: 38,
      offset: 20,
    },
    selectable: false,
    focusable: false,
    updatable: false,
    deletable: false,
    style: {
      stroke: branchColor || 'rgba(120, 131, 155, 0.24)',
      strokeWidth: sourceLevel <= 2 ? 3 : (targetLevel >= 5 ? 1.6 : 2.1),
      strokeLinecap: 'round',
      strokeLinejoin: 'round',
      opacity: props.featured ? 1 : 0.84,
    },
    data: {
      linkType: 'parent',
    },
  }
}))

const graphKey = computed(() => (
  `syllabus-${toText(props.subject?.subjectCode)}-${graphPayload.value.nodes.length}`
))

const summaryMetrics = computed(() => [
  { label: '节点总数', value: graphPayload.value.nodes.length || 0 },
  { label: '主章节', value: contentOutline.value.length || 0 },
  { label: '题型说明', value: examSummary.value?.items?.length || 0 },
])

const metaLine = computed(() => (
  [
    props.subject?.subjectType === 'PUBLIC' ? '公共课' : '专业课',
    toText(props.subject?.examCategoryName || props.subject?.examCategoryCode),
    toText(props.subject?.jointExamGroupName || props.subject?.jointExamGroupCode || '全局共享'),
  ].filter(Boolean).join(' · ')
))

const descriptorTags = computed(() => {
  const rows = []
  if (specialSections.value.introNodeId) {
    rows.push('含科目简介')
  }
  if (specialSections.value.examNodeId) {
    rows.push(`考试形式 ${examSummary.value?.items?.length || 0} 项`)
  }
  if (specialSections.value.contentNodeId) {
    rows.push(`内容章节 ${contentOutline.value.length || 0} 组`)
  }
  if (toText(props.subject?.sourceFile)) {
    rows.push(`来源 ${toText(props.subject.sourceFile)}`)
  }
  return rows
})

const accentStyle = computed(() => {
  const accent = props.featured ? 'var(--qb-subject-fallback-2)' : 'var(--qb-primary-600)'
  const softPercent = props.featured ? 14 : 10
  return {
    '--syllabus-accent': accent,
    '--syllabus-accent-soft': `color-mix(in srgb, ${accent} ${softPercent}%, white ${100 - softPercent}%)`,
  }
})
</script>

<template>
  <section
    class="student-syllabus-mindmap"
    :class="{ 'student-syllabus-mindmap--featured': featured }"
    :style="accentStyle"
  >
    <header class="student-syllabus-mindmap__header">
      <div class="student-syllabus-mindmap__copy">
        <span class="student-syllabus-mindmap__eyebrow">{{ featured ? '当前报考范围' : '折叠查阅' }}</span>
        <h4>{{ subject.subjectName || subject.subjectCode || '未命名科目' }}</h4>
        <p>{{ metaLine || '官方考试大纲思维导图' }}</p>
      </div>
      <div class="student-syllabus-mindmap__stats">
        <article
          v-for="item in summaryMetrics"
          :key="item.label"
          class="mindmap-stat"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </div>
    </header>

    <div v-if="descriptorTags.length" class="student-syllabus-mindmap__tags">
      <span
        v-for="item in descriptorTags"
        :key="item"
        class="student-syllabus-mindmap__tag"
      >
        {{ item }}
      </span>
    </div>

    <KnowledgeGraphFlowSurface
      :nodes="nodes"
      :edges="edges"
      :loading="false"
      :has-graph-data="Boolean(nodes.length)"
      :is-teacher-mode="false"
      :teacher-relation-mode="false"
      :flow-render-key="graphKey"
    />
  </section>
</template>

<style scoped>
.student-syllabus-mindmap {
  display: grid;
  gap: 18px;
  padding: 22px;
  border: 1px solid color-mix(in srgb, var(--syllabus-accent) 16%, white 84%);
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, var(--syllabus-accent-soft), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 248, 255, 0.94));
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
}

.student-syllabus-mindmap--featured {
  box-shadow: 0 24px 54px rgba(15, 118, 110, 0.12);
}

.student-syllabus-mindmap__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.student-syllabus-mindmap__copy {
  display: grid;
  gap: 8px;
}

.student-syllabus-mindmap__copy h4,
.student-syllabus-mindmap__copy p,
.mindmap-stat span,
.mindmap-stat strong {
  margin: 0;
}

.student-syllabus-mindmap__eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--syllabus-accent) 12%, white 88%);
  color: var(--syllabus-accent);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.student-syllabus-mindmap__copy h4 {
  color: var(--qb-text-heading);
  font-size: 28px;
  line-height: 1.15;
}

.student-syllabus-mindmap__copy p {
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.75;
}

.student-syllabus-mindmap__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  min-width: min(100%, 360px);
}

.mindmap-stat {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--syllabus-accent) 12%, white 88%);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
}

.mindmap-stat span {
  color: var(--qb-text-meta);
  font-size: 11px;
}

.mindmap-stat strong {
  color: var(--qb-text-heading);
  font-size: 22px;
  line-height: 1;
}

.student-syllabus-mindmap__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.student-syllabus-mindmap__tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--syllabus-accent) 8%, white 92%);
  color: color-mix(in srgb, var(--syllabus-accent) 72%, black 28%);
  font-size: 12px;
  font-weight: 600;
}

@media (max-width: 960px) {
  .student-syllabus-mindmap {
    padding: 18px;
  }

  .student-syllabus-mindmap__header {
    flex-direction: column;
  }

  .student-syllabus-mindmap__stats {
    width: 100%;
    min-width: 0;
  }
}

@media (max-width: 720px) {
  .student-syllabus-mindmap__copy h4 {
    font-size: 24px;
  }

  .student-syllabus-mindmap__stats {
    grid-template-columns: 1fr;
  }
}
</style>
