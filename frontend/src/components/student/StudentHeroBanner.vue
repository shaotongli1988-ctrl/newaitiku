<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const emit = defineEmits(['select-module'])

const props = defineProps({
  predictedScore: {
    type: Number,
    default: 0,
  },
  predictedScoreBand: {
    type: Object,
    default: () => ({
      label: '',
      description: '',
      tone: 'steady',
    }),
  },
  masteryOverview: {
    type: Object,
    default: () => ({
      averageMastery: 0,
    }),
  },
  overallCoverage: {
    type: Object,
    default: () => ({
      percent: 0,
      covered: 0,
      total: 0,
    }),
  },
  referenceGroupLabel: {
    type: String,
    default: '',
  },
  subjectCount: {
    type: Number,
    default: 0,
  },
  completedDailyTaskCount: {
    type: Number,
    default: 0,
  },
  totalDailyTaskCount: {
    type: Number,
    default: 0,
  },
  practiceModules: {
    type: Array,
    default: () => [],
  },
})

const displayedScore = ref(0)
let scoreAnimationFrame = 0

function easeOutCubic(value) {
  return 1 - ((1 - value) ** 3)
}

function animateDisplayedScore(targetScore) {
  const endValue = Math.max(0, Math.min(300, Number(targetScore || 0)))
  const startValue = displayedScore.value
  const startTime = performance.now()
  const duration = 900

  cancelAnimationFrame(scoreAnimationFrame)

  const step = (currentTime) => {
    const progress = Math.min(1, (currentTime - startTime) / duration)
    displayedScore.value = Math.round(startValue + ((endValue - startValue) * easeOutCubic(progress)))
    if (progress < 1) {
      scoreAnimationFrame = requestAnimationFrame(step)
    }
  }

  scoreAnimationFrame = requestAnimationFrame(step)
}

const scorePercent = computed(() => Math.max(0, Math.min(100, Math.round((Number(props.predictedScore || 0) / 300) * 100))))
const coveragePercent = computed(() => Math.max(0, Math.min(100, Number(props.overallCoverage?.percent || 0))))
const coverageStatus = computed(() => String(props.overallCoverage?.status || 'ready'))
const hasCoverageSummary = computed(() => ['ready', 'partial'].includes(coverageStatus.value))
const coverageBandLabel = computed(() => (
  coverageStatus.value === 'syncing'
    ? '摘要同步中'
    : (hasCoverageSummary.value ? `${coveragePercent.value}% 覆盖` : '摘要异常')
))
const coverageValueLabel = computed(() => (
  hasCoverageSummary.value ? `${coveragePercent.value}%` : '--'
))
const coverageDescription = computed(() => {
  if (coverageStatus.value === 'syncing') {
    return `已完成 ${Number(props.overallCoverage?.readySubjectCount || 0)} / ${Number(props.overallCoverage?.targetSubjectCount || 0)} 门科目的学情摘要同步。`
  }
  if (coverageStatus.value === 'unavailable') {
    return 'L5 学情摘要暂不可用，请稍后重试。'
  }
  if (coverageStatus.value === 'partial') {
    return `已覆盖 ${props.overallCoverage.covered} / ${props.overallCoverage.total || 0} 个 L5 原子考点，部分科目仍在同步。`
  }
  return `已覆盖 ${props.overallCoverage.covered} / ${props.overallCoverage.total || 0} 个 L5 原子考点。`
})
const heroToneClass = computed(() => (
  coverageStatus.value === 'unavailable'
    ? 'hero-band--alert'
    : coverageStatus.value === 'syncing'
      ? 'hero-band--syncing'
    : `hero-band--${String(props.predictedScoreBand?.tone || 'steady')}`
))
const ringStyle = computed(() => ({
  '--hero-progress-angle': `${Math.round(scorePercent.value * 3.6)}deg`,
}))

watch(
  () => props.predictedScore,
  (value) => {
    animateDisplayedScore(value)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  cancelAnimationFrame(scoreAnimationFrame)
})
</script>

<template>
  <article class="hero-banner">
    <div class="hero-score-stage">
      <span class="hero-kicker">当前预测分</span>
      <div class="hero-ring" :style="ringStyle">
        <div class="hero-ring-core">
          <strong>{{ displayedScore }}</strong>
          <small>/ 300</small>
        </div>
      </div>
    </div>

    <div class="hero-content">
      <div class="hero-head">
        <div>
          <span class="hero-side-label">当前分段</span>
          <h4>{{ predictedScoreBand.label }}</h4>
        </div>
        <span :class="['hero-band', heroToneClass]">{{ coverageBandLabel }}</span>
      </div>

      <p class="hero-copy">{{ predictedScoreBand.description }}</p>

      <div class="hero-side">
        <div class="hero-side-top">
          <span class="hero-side-label">总覆盖率</span>
          <strong>{{ coverageValueLabel }}</strong>
        </div>

        <p>{{ coverageDescription }}</p>

        <div v-if="hasCoverageSummary" class="hero-progress-track" aria-hidden="true">
          <div class="hero-progress-fill" :style="{ width: `${coveragePercent}%` }" />
        </div>

        <div class="hero-metrics">
          <article>
            <span>综合掌握度</span>
            <strong>{{ masteryOverview.averageMastery }}%</strong>
          </article>
          <article>
            <span>参考组别</span>
            <strong>{{ referenceGroupLabel || '-' }}</strong>
          </article>
          <article>
            <span>科目数</span>
            <strong>{{ subjectCount }}</strong>
          </article>
          <article>
            <span>任务进度</span>
            <strong>{{ completedDailyTaskCount }}/{{ totalDailyTaskCount || 0 }}</strong>
          </article>
        </div>
      </div>
    </div>

    <div v-if="practiceModules.length" class="hero-practice-section">
      <div class="hero-practice-head">
        <div>
          <span class="hero-side-label">练习入口</span>
          <strong>知识诊断定方向，今日任务管执行，练习模块负责把动作转成稳定得分</strong>
        </div>
        <small>按当前科目继续</small>
      </div>

      <div class="hero-practice-list">
        <button
          v-for="item in practiceModules"
          :key="item.key"
          type="button"
          :class="['hero-practice-card', { 'hero-practice-card--recommended': item.isRecommended }]"
          @click="emit('select-module', item.key)"
        >
          <div class="hero-practice-card__top">
            <span>{{ item.title }}</span>
            <b v-if="item.badge">{{ item.badge }}</b>
          </div>
          <strong>{{ item.ctaLabel || '立即进入' }}</strong>
          <small>{{ item.description }}</small>
        </button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.hero-banner {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(224, 227, 229, 0.92);
  background: var(--qb-bg-card);
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
  grid-template-columns: minmax(140px, 176px) minmax(0, 1fr);
  align-items: start;
}

.hero-copy,
.hero-side p {
  margin: 0;
}

.hero-content {
  display: grid;
  gap: 10px;
  align-self: center;
}

.hero-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hero-head h4 {
  margin: 4px 0 0;
  color: var(--qb-text-heading);
  font-size: 22px;
  line-height: 1.1;
}

.hero-kicker {
  display: inline-flex;
  align-items: center;
  color: var(--qb-text-subtle-4);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.hero-copy {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.5;
}

.hero-band {
  display: inline-flex;
  align-items: center;
  padding: 7px 10px;
  border-radius: var(--qb-radius-pill);
  color: var(--qb-text-inverse);
  font-size: 11px;
  font-weight: 700;
}

.hero-band--strong {
  background: var(--qb-gradient-success-fill);
}

.hero-band--steady {
  background: var(--qb-gradient-warning-fill);
}

.hero-band--focus {
  background: var(--qb-gradient-danger-fill);
}

.hero-band--alert {
  background: var(--qb-surface-soft-danger);
  color: var(--qb-text-danger-ink);
}

.hero-band--syncing {
  background: var(--qb-surface-soft-warning);
  color: var(--qb-text-warning-ink);
}

.hero-score-stage {
  display: grid;
  justify-items: center;
  align-self: center;
  gap: 10px;
  padding-block: 6px;
}

.hero-ring {
  position: relative;
  display: grid;
  place-items: center;
  width: min(100%, 136px);
  aspect-ratio: 1 / 1;
  border-radius: var(--qb-radius-round);
  background:
    conic-gradient(
      from -90deg,
      var(--qb-primary-student) 0deg,
      var(--qb-primary-400) var(--hero-progress-angle),
      rgba(191, 219, 254, 0.38) var(--hero-progress-angle),
      rgba(191, 219, 254, 0.18) 360deg
    );
  box-shadow:
    inset 0 0 0 9px rgba(255, 255, 255, 0.88);
}

.hero-ring::before {
  content: '';
  position: absolute;
  inset: 13px;
  border-radius: var(--qb-radius-round);
  background: var(--qb-bg-card);
}

.hero-ring-core {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: center;
  gap: 2px;
}

.hero-ring-core strong {
  font-size: clamp(32px, 3.3vw, 42px);
  line-height: 0.95;
  color: var(--qb-text-heading);
}

.hero-ring-core small {
  color: var(--qb-text-meta);
  font-size: 13px;
  font-weight: 600;
}

.hero-side {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(255, 255, 255, 0.98));
}

.hero-side-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--qb-space-3);
}

.hero-side-label {
  color: var(--qb-text-copy);
  font-size: 12px;
  font-weight: 700;
}

.hero-side-top strong {
  color: var(--qb-text-heading);
  font-size: 18px;
  line-height: 1;
}

.hero-side p {
  color: var(--qb-text-copy);
  font-size: 12px;
  line-height: 1.5;
}

.hero-progress-track {
  width: 100%;
  height: 8px;
  overflow: hidden;
  border-radius: var(--qb-radius-pill);
  background: var(--qb-track-soft);
}

.hero-progress-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--qb-gradient-primary-fill);
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.hero-metrics article {
  padding: 8px 10px;
  border-radius: 12px;
  background: var(--qb-bg-card);
  box-shadow: inset 0 0 0 1px rgba(224, 227, 229, 0.88);
}

.hero-metrics span {
  display: block;
  color: var(--qb-text-meta);
  font-size: 12px;
}

.hero-metrics strong {
  display: block;
  margin-top: 3px;
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.15;
}

.hero-practice-section {
  display: grid;
  grid-column: 1 / -1;
  gap: 10px;
}

.hero-practice-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.hero-practice-head strong {
  display: block;
  margin-top: 3px;
  color: var(--qb-text-heading);
  font-size: 15px;
  line-height: 1.3;
}

.hero-practice-head small {
  color: var(--qb-text-meta);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.hero-practice-list {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.hero-practice-card {
  display: grid;
  gap: 8px;
  align-content: start;
  min-height: 96px;
  padding: 13px 14px;
  text-align: left;
  border: 0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: inset 0 0 0 1px rgba(191, 219, 254, 0.75);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  cursor: pointer;
}

.hero-practice-card:hover {
  transform: translateY(-1px);
  box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.82), 0 16px 26px rgba(37, 99, 235, 0.08);
}

.hero-practice-card--recommended {
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 26%),
    rgba(255, 255, 255, 0.82);
  box-shadow: inset 0 0 0 1px rgba(29, 78, 216, 0.52), 0 16px 26px rgba(37, 99, 235, 0.08);
}

.hero-practice-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.hero-practice-card__top span {
  color: var(--qb-text-copy);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.hero-practice-card__top b {
  padding: 3px 7px;
  border-radius: 999px;
  background: rgba(29, 78, 216, 0.1);
  color: var(--qb-primary-student);
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.hero-practice-card strong {
  color: var(--qb-text-heading);
  font-size: clamp(15px, 1.6vw, 17px);
  line-height: 1.2;
}

.hero-practice-card small {
  color: var(--qb-text-copy);
  display: -webkit-box;
  overflow: hidden;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

@media (max-width: 900px) {
  .hero-banner {
    grid-template-columns: 1fr;
  }

  .hero-score-stage {
    justify-items: flex-start;
  }

  .hero-practice-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero-banner {
    padding: 14px;
  }

  .hero-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-side {
    padding: var(--qb-space-4);
  }

  .hero-metrics {
    grid-template-columns: 1fr;
  }

  .hero-practice-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-practice-list {
    grid-template-columns: 1fr;
  }

  .hero-practice-card {
    min-height: 0;
  }
}
</style>
