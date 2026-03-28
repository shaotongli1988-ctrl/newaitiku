<script setup>
import { useRouter } from 'vue-router'
import QuestionBankPageHeader from '../../components/student/QuestionBankPageHeader.vue'
import QuestionBankSectionHeader from '../../components/student/QuestionBankSectionHeader.vue'

const router = useRouter()

const moduleCards = [
  {
    key: 'repair',
    title: '错题中心',
    path: '/student/question-bank/repair',
    summary: '聚合错题、错因统计和复习打点，是日常复盘的主入口。',
    actions: ['按错因筛选题目', '生成专项巩固卷', '生成 AI 同类卷并继续练习'],
  },
  {
    key: 'archive',
    title: '沉淀题库',
    path: '/student/question-bank/archive',
    summary: '沉淀收藏题与高价值题，支持复习计划和导出。',
    actions: ['收藏与取消收藏', '查看复习计划并开始复习', '按需导出 CSV/PDF'],
  },
  {
    key: 'methods',
    title: '学习方法',
    path: '/student/question-bank/learning-methods',
    summary: '按方法论给出可执行学习路径，帮助你把练习时间用在关键点上。',
    actions: ['选择学习方法卡片', '启动学习任务并记录进度', '完成方法训练闭环'],
  },
  {
    key: 'syllabus',
    title: '考试大纲',
    path: '/student/question-bank/syllabus',
    summary: '按报考范围展示大纲结构，先看清考什么再安排刷题。',
    actions: ['查看必看科目结构', '展开节点查看考点层级', '配合积分与刷题页面联动学习'],
  },
]

const quickFlows = [
  {
    title: '错题复盘流程',
    steps: [
      '进入错题中心，先按错因或知识点筛选。',
      '对高频错题做复习打点，确认是否已掌握。',
      '从当前错题生成专项卷，检验修复效果。',
    ],
  },
  {
    title: '沉淀收藏流程',
    steps: [
      '在刷题页面将高价值题加入沉淀题库。',
      '到沉淀题库查看汇总与复习计划。',
      '按计划完成复习并按需导出资料。',
    ],
  },
  {
    title: '大纲驱动流程',
    steps: [
      '先在考试大纲确认当前必考范围。',
      '回到刷题或积分页，优先训练高频重点。',
      '每周复查大纲覆盖度，避免偏离主线。',
    ],
  },
]

const dailyScenarios = [
  {
    key: 'daily-warmup',
    phase: '日常',
    title: '每天开练前 10 分钟校准',
    goal: '先明确今天刷题重点，避免无目标练习。',
    entries: ['/student/question-bank/syllabus', '/student/analysis/points', '/student/practice/chapter'],
    steps: [
      '先在考试大纲确认今天要覆盖的章节和知识点。',
      '在积分页看当前短板科目，确定练习优先级。',
      '进入章节闯关开始当日训练。',
    ],
    output: '当日训练范围清晰，练习更聚焦。',
  },
  {
    key: 'chapter-practice',
    phase: '日常',
    title: '章节刷题主流程',
    goal: '稳定完成日练，提升核心知识点正确率。',
    entries: ['/student/practice/chapter', '/student/question-bank/repair'],
    steps: [
      '在章节练习中完成当日题量。',
      '错题自动沉淀后，立刻回到错题中心做复盘。',
      '对反复错误题打上复习标记。',
    ],
    output: '章节进度前进且错题可追踪。',
  },
  {
    key: 'error-repair',
    phase: '日常',
    title: '错题修复闭环',
    goal: '把“会错的题”变成“能稳定做对的题”。',
    entries: ['/student/question-bank/repair', '/student/question-bank/learning-methods'],
    steps: [
      '在错题中心按错因筛选并做针对复习。',
      '生成专项巩固卷验证本轮修复效果。',
      '结合学习方法页选择下一步训练策略。',
    ],
    output: '错因收敛，重复错误减少。',
  },
  {
    key: 'archive-review',
    phase: '周内',
    title: '沉淀题库复习日',
    goal: '把高价值题反复打磨，形成稳定得分点。',
    entries: ['/student/question-bank/archive', '/student/practice/free'],
    steps: [
      '从沉淀题库挑选高价值题进入复习计划。',
      '在自由练习模式做二次验证。',
      '完成后更新复习状态并清理低价值收藏。',
    ],
    output: '高价值题库持续提纯。',
  },
  {
    key: 'weekly-retro',
    phase: '周度',
    title: '周学习复盘',
    goal: '每周确认提分是否在关键科目发生。',
    entries: ['/student/analysis/overview', '/student/question-bank/syllabus', '/student/question-bank/guide'],
    steps: [
      '在诊断总览检查本周正确率与覆盖率变化。',
      '对照考试大纲核对是否偏离主线。',
      '在使用文档里按推荐流程调整下周计划。',
    ],
    output: '下周学习计划更有针对性。',
  },
  {
    key: 'mock-exam-day',
    phase: '月度',
    title: '模考日全流程',
    goal: '通过整卷检验阶段学习质量。',
    entries: ['/student/practice/mock', '/student/practice/tasks', '/student/question-bank/repair'],
    steps: [
      '进入模拟考试完成整卷作答。',
      '在考试任务页复看提交状态和报告。',
      '把模考错题纳入错题中心优先修复。',
    ],
    output: '阶段测评结果转化为后续训练动作。',
  },
  {
    key: 'sprint-before-exam',
    phase: '冲刺',
    title: '考前冲刺学习',
    goal: '在有限时间内优先拿下高频必考点。',
    entries: ['/student/question-bank/syllabus', '/student/question-bank/repair', '/messages'],
    steps: [
      '依据大纲锁定高频高分章节。',
      '在错题中心集中清理相关错题。',
      '通过消息中心跟进老师下发的冲刺提醒。',
    ],
    output: '冲刺阶段练习时间投入更有效。',
  },
  {
    key: 'new-term-start',
    phase: '开学',
    title: '新学期重启流程',
    goal: '快速恢复学习节奏，避免开局混乱。',
    entries: ['/student/home', '/student/onboarding/diagnosis', '/student/question-bank/syllabus'],
    steps: [
      '先看首页当前权益和任务状态。',
      '必要时先做快诊更新当前能力画像。',
      '回到大纲重新确认本学期优先学习范围。',
    ],
    output: '新周期学习路径清晰。',
  },
  {
    key: 'abnormal-handling',
    phase: '应急',
    title: '异常情况处理',
    goal: '在题目异常、任务异常时快速恢复学习连续性。',
    entries: ['/messages', '/student/question-bank/guide', '/student/practice/chapter'],
    steps: [
      '先在消息中心查看系统通知与老师说明。',
      '在使用文档按排查建议完成自检。',
      '确认恢复后返回章节练习继续学习。',
    ],
    output: '异常期间学习不中断。',
  },
]

const weeklyRhythm = [
  '周一到周四：章节练习 + 错题当日复盘。',
  '周五：沉淀题库复习与一周小结。',
  '周末：模考或专题冲刺（按当前阶段选择）。',
  '每天：至少一次对照大纲校准学习方向。',
]

const abilityTracks = [
  {
    key: 'foundation',
    level: '基础薄弱',
    target: '正确率波动大、错题重复率高的同学',
    focus: '先稳基础，优先修错，不追求一次做太多题。',
    cadence: '建议频率：每天 1 次章节练习 + 1 次错题修复。',
    entries: ['/student/practice/chapter', '/student/question-bank/repair', '/student/question-bank/syllabus'],
  },
  {
    key: 'improving',
    level: '中等水平',
    target: '已有基础，但得分不稳定、阶段提升慢的同学',
    focus: '训练稳定输出能力，强化高频考点覆盖率。',
    cadence: '建议频率：工作日章节练习，周末模考 1 次。',
    entries: ['/student/practice/chapter', '/student/practice/mock', '/student/analysis/overview'],
  },
  {
    key: 'sprint',
    level: '冲刺提分',
    target: '临近考试，希望短期提高分数上限的同学',
    focus: '围绕高频高分点做专题冲刺和限时训练。',
    cadence: '建议频率：每周 2 次模考 + 每天冲刺错题清零。',
    entries: ['/student/practice/mock', '/student/question-bank/repair', '/messages'],
  },
]

function openPath(path) {
  const normalizedPath = String(path || '').trim()
  if (!normalizedPath) {
    return
  }
  router.push(normalizedPath)
}
</script>

<template>
  <section class="question-bank-guide-page">
    <section class="guide-hero-card">
      <QuestionBankPageHeader
        eyebrow="我的题库"
        title="使用文档"
        description="这份文档覆盖学生端题库模块的入口说明、常用流程和排查建议。建议先看总览，再按流程执行。"
      >
        <template #meta>
          <el-tag effect="dark" type="primary">学生端</el-tag>
        </template>
      </QuestionBankPageHeader>
    </section>

    <section class="guide-section">
      <QuestionBankSectionHeader
        kicker="模块总览"
        title="我的题库四个核心模块"
        description="每个模块都有明确职责，避免同一问题在多个页面重复处理。"
      />

      <div class="module-grid">
        <article
          v-for="item in moduleCards"
          :key="item.key"
          class="module-card"
        >
          <header>
            <h4>{{ item.title }}</h4>
            <el-button link type="primary" @click="openPath(item.path)">打开入口</el-button>
          </header>
          <p>{{ item.summary }}</p>
          <ul>
            <li v-for="action in item.actions" :key="action">{{ action }}</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="guide-section">
      <QuestionBankSectionHeader
        kicker="推荐用法"
        title="高频操作流程"
        description="按流程走能减少来回跳转，学习效率会更稳定。"
      />

      <div class="flow-list">
        <article
          v-for="flow in quickFlows"
          :key="flow.title"
          class="flow-card"
        >
          <h4>{{ flow.title }}</h4>
          <ol>
            <li v-for="step in flow.steps" :key="step">{{ step }}</li>
          </ol>
        </article>
      </div>
    </section>

    <section class="guide-section">
      <QuestionBankSectionHeader
        kicker="场景手册"
        title="日常学习场景覆盖"
        description="以下场景覆盖日常、周度、模考、冲刺和异常处理路径。"
      />

      <div class="scenario-grid">
        <article
          v-for="item in dailyScenarios"
          :key="item.key"
          class="scenario-card"
        >
          <header class="scenario-card__head">
            <h4>{{ item.title }}</h4>
            <el-tag size="small" type="info">{{ item.phase }}</el-tag>
          </header>
          <p class="scenario-goal">目标：{{ item.goal }}</p>
          <p class="scenario-entry">入口：{{ item.entries.join(' -> ') }}</p>
          <ol>
            <li v-for="step in item.steps" :key="step">{{ step }}</li>
          </ol>
          <p class="scenario-output">产出：{{ item.output }}</p>
        </article>
      </div>
    </section>

    <section class="guide-section">
      <QuestionBankSectionHeader
        kicker="执行节奏"
        title="每周学习节奏建议"
        description="可作为默认模板，再按个人时间微调。"
      />

      <ol class="guide-steps">
        <li v-for="item in weeklyRhythm" :key="item">{{ item }}</li>
      </ol>
    </section>

    <section class="guide-section">
      <QuestionBankSectionHeader
        kicker="分层路径"
        title="按学习基础选择策略"
        description="同样的题库，不同基础要走不同节奏。先选层级，再执行对应路径。"
      />

      <div class="ability-grid">
        <article
          v-for="track in abilityTracks"
          :key="track.key"
          class="ability-card"
        >
          <header class="ability-card__head">
            <h4>{{ track.level }}</h4>
            <el-tag size="small" type="success">推荐路径</el-tag>
          </header>
          <p class="ability-target">适用：{{ track.target }}</p>
          <p class="ability-focus">重点：{{ track.focus }}</p>
          <p class="ability-cadence">{{ track.cadence }}</p>
          <p class="ability-entry">入口：{{ track.entries.join(' -> ') }}</p>
        </article>
      </div>
    </section>

    <section class="guide-section guide-faq">
      <QuestionBankSectionHeader
        kicker="常见问题"
        title="排查建议"
        description="遇到数据或页面异常时，先按下面顺序自检。"
      />

      <ul>
        <li>看不到题目：先确认顶部科目切换是否为当前科目。</li>
        <li>按钮灰色不可点：通常是当前状态不满足操作前置条件。</li>
        <li>数据未刷新：切换页面后等待同步提示消失，再重试一次。</li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.question-bank-guide-page {
  display: grid;
  gap: 16px;
}

.guide-hero-card,
.guide-section {
  border: 1px solid var(--qb-border-soft);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
  padding: 20px;
}

.module-grid,
.flow-list {
  margin-top: 14px;
  display: grid;
  gap: 12px;
}

.module-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.module-card {
  border: 1px solid var(--qb-border-soft);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(240, 249, 255, 0.8), rgba(255, 255, 255, 0.98));
  padding: 14px;
  display: grid;
  gap: 10px;
}

.module-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.module-card h4,
.module-card p {
  margin: 0;
}

.module-card p {
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.module-card ul,
.flow-card ol,
.guide-faq ul,
.scenario-card ol,
.guide-steps {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
  color: var(--qb-text-copy);
  line-height: 1.6;
}

.flow-card {
  border: 1px dashed var(--qb-primary-soft-border);
  border-radius: 16px;
  background: var(--qb-primary-soft-bg);
  padding: 14px;
}

.flow-card h4 {
  margin: 0 0 10px;
  color: var(--qb-text-heading);
}

.scenario-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.scenario-card {
  border: 1px solid var(--qb-border-soft);
  border-radius: 16px;
  background: linear-gradient(165deg, rgba(236, 253, 245, 0.82), rgba(255, 255, 255, 0.98));
  padding: 14px;
  display: grid;
  gap: 10px;
}

.scenario-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.scenario-card__head h4,
.scenario-goal,
.scenario-entry,
.scenario-output {
  margin: 0;
}

.scenario-goal,
.scenario-entry,
.scenario-output {
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.6;
}

.scenario-output {
  color: var(--qb-text-info-ink);
}

.guide-steps {
  margin-top: 8px;
}

.ability-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.ability-card {
  border: 1px solid var(--qb-border-soft);
  border-radius: 16px;
  background: linear-gradient(160deg, rgba(254, 249, 195, 0.68), rgba(255, 255, 255, 0.98));
  padding: 14px;
  display: grid;
  gap: 8px;
}

.ability-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ability-card__head h4,
.ability-target,
.ability-focus,
.ability-cadence,
.ability-entry {
  margin: 0;
}

.ability-target,
.ability-focus,
.ability-cadence,
.ability-entry {
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.6;
}

.ability-entry {
  color: var(--qb-text-info-ink);
}

@media (max-width: 900px) {
  .module-grid,
  .scenario-grid,
  .ability-grid {
    grid-template-columns: 1fr;
  }
}
</style>
