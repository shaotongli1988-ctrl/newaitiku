<script setup>
import { computed } from 'vue'
import BaseDrawer from '../common/BaseDrawer.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  subject: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'analyze', 'tasks'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const weakNodes = computed(() => (
  Array.isArray(props.subject?.weakNodes) ? props.subject.weakNodes : []
))

const hasInsight = computed(() => Boolean(props.subject?.hasInsight))
const isLoadingInsight = computed(() => String(props.subject?.insightStatus || '').trim() === 'loading')
const isIdleInsight = computed(() => ['idle', 'queued', 'empty'].includes(String(props.subject?.insightStatus || '').trim()))
const coverageValue = computed(() => (
  hasInsight.value ? `${Number(props.subject?.coverage || 0)}%` : '--'
))
const l5CoverageValue = computed(() => (
  hasInsight.value ? `${Number(props.subject?.l5Covered || 0)}/${Number(props.subject?.l5Total || 0)}` : '--'
))
const weakEmptyDescription = computed(() => {
  if (isLoadingInsight.value) {
    return '当前正在同步这门科目的学情摘要，请稍候。'
  }
  if (isIdleInsight.value) {
    return '当前还未拉取这门科目的学情摘要，已在后台优先补齐。'
  }
  if (!hasInsight.value) {
    return '这门科目的学情摘要暂不可用，请稍后重试。'
  }
  return '当前还没有识别出需要优先补强的薄弱点。'
})
</script>

<template>
  <BaseDrawer
    v-model="visible"
    class="subject-drawer"
    :title="subject?.subjectName || '科目详情'"
    size="36%"
  >
    <div v-if="subject" class="subject-drawer-body">
      <section class="drawer-hero" :style="{ '--subject-accent': subject.accent || 'var(--qb-subject-fallback-1)' }">
        <span class="drawer-icon">{{ subject.badge }}</span>
        <div>
          <p class="drawer-kicker">科目详情</p>
          <h3>{{ subject.subjectName }}</h3>
          <p class="drawer-copy">点击卡片后在这里查看掌握度、覆盖率和优先补强的薄弱点，再决定今天的任务和下一轮冲分重点。</p>
        </div>
      </section>

      <section class="drawer-metrics">
        <article>
          <span>掌握度</span>
          <strong>{{ subject.mastery }}%</strong>
        </article>
        <article>
          <span>覆盖率</span>
          <strong>{{ coverageValue }}</strong>
        </article>
        <article>
          <span>L5 覆盖</span>
          <strong>{{ l5CoverageValue }}</strong>
        </article>
      </section>

      <section class="drawer-progress">
        <div class="drawer-section-head">
          <strong>当前进度</strong>
          <span>{{ coverageValue }}</span>
        </div>
        <div class="drawer-track" aria-hidden="true">
          <div class="drawer-fill" :style="{ width: `${hasInsight ? subject.coverage : 100}%` }" />
        </div>
      </section>

      <section class="drawer-weakness">
        <div class="drawer-section-head">
          <strong>优先补强点</strong>
          <span>{{ weakNodes.length ? `${weakNodes.length} 个候选` : '暂无' }}</span>
        </div>

        <el-empty
          v-if="!weakNodes.length"
          :description="weakEmptyDescription"
        />

        <div v-else class="weak-list">
          <article
            v-for="node in weakNodes"
            :key="node.id"
            class="weak-item"
          >
            <div>
              <strong>{{ node.label || node.id }}</strong>
              <p>题量 {{ Number(node.questionCount || 0) }}，建议先看知识诊断，再去今日任务推进，后续更容易把这块转成稳定段位分。</p>
            </div>
            <span>掌握度 {{ Number(node.mastery || 0) }}%</span>
          </article>
        </div>
      </section>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <el-button plain @click="emit('update:modelValue', false)">
          关闭
        </el-button>
        <el-button plain @click="emit('analyze', subject)">
          诊断总览
        </el-button>
        <el-button type="primary" @click="emit('tasks', subject)">
          今日任务
        </el-button>
      </div>
    </template>
  </BaseDrawer>
</template>

<style scoped>
.subject-drawer-body,
.drawer-kicker,
.drawer-copy,
.weak-item p {
  margin: 0;
}

.subject-drawer-body {
  display: grid;
  gap: var(--qb-space-6);
}

.drawer-hero {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--qb-space-4);
  align-items: center;
  padding: var(--qb-space-5);
  border-radius: var(--qb-radius-2xl);
  background: linear-gradient(145deg, color-mix(in srgb, var(--subject-accent) 16%, white 84%), var(--qb-surface-strong));
}

.drawer-icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: var(--qb-radius-lg);
  background: var(--subject-accent);
  color: var(--qb-text-inverse);
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.drawer-kicker {
  color: var(--qb-primary-student);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.drawer-hero h3 {
  margin: var(--qb-space-2-5) 0 0;
  color: var(--qb-text-heading);
  font-size: 24px;
}

.drawer-copy {
  margin-top: 8px;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.drawer-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--qb-space-3);
}

.drawer-metrics article {
  padding: var(--qb-space-4);
  border-radius: var(--qb-radius-lg);
  background: var(--qb-surface-solid);
}

.drawer-metrics span,
.drawer-section-head span {
  color: var(--qb-text-meta);
  font-size: 12px;
}

.drawer-metrics strong {
  display: block;
  margin-top: 8px;
  color: var(--qb-text-heading);
  font-size: 24px;
  line-height: 1.15;
}

.drawer-progress,
.drawer-weakness {
  display: grid;
  gap: var(--qb-space-3);
}

.drawer-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--qb-space-3);
}

.drawer-section-head strong {
  color: var(--qb-text-heading);
  font-size: 16px;
}

.drawer-track {
  width: 100%;
  height: 10px;
  overflow: hidden;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-track-soft);
}

.drawer-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--subject-accent), color-mix(in srgb, var(--subject-accent) 70%, white 30%));
}

.weak-list {
  display: grid;
  gap: var(--qb-space-3);
}

.weak-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--qb-space-4);
  padding: var(--qb-space-3-5) var(--qb-space-4);
  border-radius: var(--qb-radius-lg);
  background: var(--qb-surface-raised);
}

.weak-item strong {
  color: var(--qb-text-heading);
  font-size: 14px;
}

.weak-item p {
  margin-top: 6px;
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.6;
}

.weak-item span {
  color: var(--qb-danger);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--qb-space-3);
}

@media (max-width: 768px) {
  .drawer-hero {
    grid-template-columns: 1fr;
  }

  .drawer-metrics {
    grid-template-columns: 1fr;
  }

  .weak-item {
    flex-direction: column;
  }

  .drawer-footer {
    flex-direction: column-reverse;
  }
}
</style>
