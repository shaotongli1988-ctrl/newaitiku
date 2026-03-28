<script setup>
import { computed } from 'vue'

defineOptions({
  name: 'QuestionBankSyllabusBranch',
})

const props = defineProps({
  nodes: {
    type: Array,
    default: () => [],
  },
  depth: {
    type: Number,
    default: 0,
  },
  expandedIds: {
    type: Array,
    default: () => [],
  },
  highlightedIds: {
    type: Array,
    default: () => [],
  },
  searchKeyword: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['toggle-node'])

const expandedIdSet = computed(() => new Set((props.expandedIds || []).map((item) => String(item || '').trim()).filter(Boolean)))
const highlightedIdSet = computed(() => new Set((props.highlightedIds || []).map((item) => String(item || '').trim()).filter(Boolean)))

function hasChildren(node) {
  return Array.isArray(node?.children) && node.children.length > 0
}

function isExpanded(node) {
  return hasChildren(node) && expandedIdSet.value.has(String(node?.id || '').trim())
}

function isHighlighted(node) {
  return highlightedIdSet.value.has(String(node?.id || '').trim())
}

function resolveNodeCountLabel(node) {
  const descendantCount = Number(node?.descendantCount || 0)
  const weakCount = Number(node?.weakCount || 0)
  if (descendantCount > 0 && weakCount > 0) {
    return `${descendantCount} 个子项 · ${weakCount} 个重点`
  }
  if (descendantCount > 0) {
    return `${descendantCount} 个子项`
  }
  return ''
}

function escapeRegExp(value) {
  return String(value || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function buildHighlightedSegments(label) {
  const normalizedLabel = String(label || '')
  const normalizedKeyword = String(props.searchKeyword || '').trim()
  if (!normalizedLabel || !normalizedKeyword) {
    return [{ text: normalizedLabel, matched: false }]
  }
  const pattern = new RegExp(`(${escapeRegExp(normalizedKeyword)})`, 'ig')
  const parts = normalizedLabel.split(pattern).filter((item) => item)
  if (!parts.length) {
    return [{ text: normalizedLabel, matched: false }]
  }
  const lowerKeyword = normalizedKeyword.toLowerCase()
  return parts.map((item) => ({
    text: item,
    matched: item.toLowerCase() === lowerKeyword,
  }))
}
</script>

<template>
  <ul class="syllabus-branch" :class="[`syllabus-branch--depth-${depth}`]">
    <li
      v-for="node in nodes"
      :id="`syllabus-node-${node.id}`"
      :key="node.id"
      class="syllabus-branch__item"
      :class="{ 'syllabus-branch__item--expanded': isExpanded(node) }"
    >
      <article
        class="syllabus-branch__card"
        :class="[
          `syllabus-branch__card--level-${node.level || 0}`,
          {
            'syllabus-branch__card--highlighted': isHighlighted(node),
            'syllabus-branch__card--expandable': hasChildren(node),
          },
        ]"
      >
        <div class="syllabus-branch__main">
          <span class="syllabus-branch__level">L{{ node.level || 0 }}</span>
          <strong>
            <template
              v-for="(segment, index) in buildHighlightedSegments(node.label)"
              :key="`${node.id}-${index}-${segment.text}`"
            >
              <mark v-if="segment.matched" class="syllabus-branch__mark">{{ segment.text }}</mark>
              <template v-else>{{ segment.text }}</template>
            </template>
          </strong>
          <small v-if="resolveNodeCountLabel(node)">{{ resolveNodeCountLabel(node) }}</small>
        </div>

        <button
          v-if="hasChildren(node)"
          type="button"
          class="syllabus-branch__toggle"
          :aria-expanded="isExpanded(node)"
          @click="emit('toggle-node', node.id)"
        >
          {{ isExpanded(node) ? '收起' : '展开' }}
        </button>
      </article>

      <div v-if="hasChildren(node) && isExpanded(node)" class="syllabus-branch__children">
        <QuestionBankSyllabusBranch
          :nodes="node.children"
          :depth="depth + 1"
          :expanded-ids="expandedIds"
          :highlighted-ids="highlightedIds"
          :search-keyword="searchKeyword"
          @toggle-node="emit('toggle-node', $event)"
        />
      </div>
    </li>
  </ul>
</template>

<style scoped>
.syllabus-branch {
  --branch-line: color-mix(in srgb, var(--qb-primary-student) 18%, white 82%);
  display: grid;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.syllabus-branch__item {
  position: relative;
  display: grid;
  gap: 12px;
  min-width: 0;
}

.syllabus-branch__item::before {
  content: '';
  position: absolute;
  left: 17px;
  top: 56px;
  bottom: -12px;
  width: 1px;
  background: var(--branch-line);
}

.syllabus-branch__item:last-child::before {
  bottom: calc(100% - 56px);
}

.syllabus-branch__card {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  min-width: 0;
  padding: 16px 18px 16px 22px;
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  border-radius: 22px;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 32%),
    linear-gradient(160deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94));
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.06);
}

.syllabus-branch__card::before {
  content: '';
  position: absolute;
  left: -1px;
  top: 14px;
  bottom: 14px;
  width: 5px;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--qb-primary-student), var(--qb-success));
}

.syllabus-branch__card--highlighted {
  border-color: color-mix(in srgb, var(--qb-warning) 48%, white 52%);
  box-shadow: 0 18px 36px rgba(250, 173, 20, 0.16);
}

.syllabus-branch__main {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.syllabus-branch__main strong,
.syllabus-branch__main small {
  margin: 0;
}

.syllabus-branch__level {
  display: inline-flex;
  width: fit-content;
  padding: 5px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  color: var(--qb-primary-student);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.syllabus-branch__main strong {
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.65;
}

.syllabus-branch__main small {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.6;
}

.syllabus-branch__toggle {
  flex-shrink: 0;
  min-width: 56px;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid color-mix(in srgb, var(--qb-primary-student) 16%, white 84%);
  border-radius: 999px;
  background: color-mix(in srgb, var(--qb-primary-student) 6%, white 94%);
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.syllabus-branch__toggle:hover,
.syllabus-branch__toggle:focus-visible {
  border-color: color-mix(in srgb, var(--qb-primary-student) 34%, white 66%);
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
  transform: translateY(-1px);
  outline: none;
}

.syllabus-branch__mark {
  padding: 0 4px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--qb-warning) 28%, white 72%);
  color: inherit;
}

.syllabus-branch__card--level-3::before {
  background: linear-gradient(180deg, var(--qb-primary-student), color-mix(in srgb, var(--qb-primary-student) 76%, white 24%));
}

.syllabus-branch__card--level-4::before {
  background: linear-gradient(180deg, var(--qb-success), color-mix(in srgb, var(--qb-success) 72%, white 28%));
}

.syllabus-branch__card--level-5::before {
  background: linear-gradient(180deg, var(--qb-warning), color-mix(in srgb, var(--qb-warning) 72%, var(--qb-danger) 28%));
}

.syllabus-branch__children {
  position: relative;
  padding-left: 28px;
}

.syllabus-branch__children::before {
  content: '';
  position: absolute;
  left: 10px;
  top: -4px;
  bottom: 8px;
  width: 1px;
  background: var(--branch-line);
}

@media (max-width: 768px) {
  .syllabus-branch__card {
    flex-direction: column;
  }

  .syllabus-branch__toggle {
    width: 100%;
  }

  .syllabus-branch__children {
    padding-left: 18px;
  }
}
</style>
