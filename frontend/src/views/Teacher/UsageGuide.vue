<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const featureModules = [
  {
    key: 'home',
    name: '教师工作台',
    entry: '/teacher/home',
    capabilities: [
      '查看待终审题目、已发布试卷、未读教学消息、班级覆盖率等核心指标。',
      '通过快捷入口跳转到题库、组卷、学情、消息等高频页面。',
    ],
  },
  {
    key: 'questions',
    name: '题库管理',
    entry: '/teacher/questions',
    capabilities: [
      '单题新增、编辑、删除，支持题型/状态/知识点/范围多维筛选。',
      '题目状态流转（草稿、提审、审核、发布、驳回）与批量状态操作。',
      '模板导入（预览校对、勾选导入、失败日志）与批量删除恢复。',
    ],
  },
  {
    key: 'students',
    name: '学生账号开通',
    entry: '/teacher/student-accounts',
    capabilities: [
      '维护学生账号开通状态，支持按条件检索。',
      '维护学生基础信息与教学服务范围（按当前权限可见范围）。',
    ],
  },
  {
    key: 'content',
    name: '内容体系字典',
    entry: '/teacher/content-system',
    capabilities: [
      '查看学科门类、联考专业组、科目的基线结构与分布。',
      '通过图表快速了解题量分布与内容覆盖情况。',
    ],
  },
  {
    key: 'papers',
    name: '组卷中心',
    entry: '/teacher/papers',
    capabilities: [
      '手动组卷、AI 组卷、模板保存与复用。',
      '试卷状态流转、导出、删除恢复与题池筛选。',
    ],
  },
  {
    key: 'tasks',
    name: '考试任务管理',
    entry: '/teacher/exam-tasks',
    capabilities: [
      '查看考试任务状态与执行进度。',
      '围绕试卷任务进行教学跟踪和过程管理。',
    ],
  },
  {
    key: 'knowledge',
    name: '知识点管理',
    entry: '/teacher/knowledge',
    capabilities: [
      '知识点三级树维护：增删改查、排序、展开折叠。',
      '删除恢复与结构层级校验，保障知识体系稳定。',
    ],
  },
  {
    key: 'analytics',
    name: '学情管理',
    entry: '/teacher/analytics',
    capabilities: [
      '查看覆盖率、正确率、掌握度、风险学生等分析指标。',
      '查询刷题明细并导出学情报表（CSV/PDF）。',
    ],
  },
  {
    key: 'messages',
    name: '消息中心',
    entry: '/messages',
    capabilities: [
      '发送教学提醒与通知，支持按用户或按分群发送。',
      '支持定时发送、发送历史追踪、撤回与已读状态查看。',
    ],
  },
]

const permissionMap = [
  { permission: 'question:manage', module: '题库管理、知识点管理' },
  { permission: 'paper:manage', module: '内容体系字典、组卷中心、考试任务管理' },
  { permission: 'analytics:view', module: '学情管理' },
  { permission: 'student:manage', module: '学生账号开通' },
  { permission: 'message:send', module: '消息中心（发送、历史、撤回）' },
]

const dailyScenarios = [
  {
    key: 'lesson-prep',
    phase: '课前',
    title: '当天备课与选题',
    goal: '在开课前完成题目筛选、知识点校准和课堂题单准备。',
    entries: ['/teacher/questions', '/teacher/knowledge', '/teacher/papers'],
    steps: [
      '在题库管理按章节、题型、难度筛选当日讲练题。',
      '到知识点管理核对知识树层级与讲解路径是否一致。',
      '在组卷中心生成课堂用题单或测验卷草稿。',
    ],
    output: '可直接上课使用的题单/测验草稿。',
  },
  {
    key: 'in-class-check',
    phase: '课中',
    title: '随堂检测与即时纠偏',
    goal: '通过短测快速发现当前班级薄弱点并即时调整讲解。',
    entries: ['/teacher/papers', '/teacher/exam-tasks', '/teacher/analytics'],
    steps: [
      '从组卷中心选择短测卷并发布到当前班级。',
      '在考试任务管理跟踪提交进度和未提交名单。',
      '在学情管理查看即时正确率，定位高错知识点后回讲。',
    ],
    output: '课中薄弱点清单与回讲动作。',
  },
  {
    key: 'homework-followup',
    phase: '课后',
    title: '课后作业与复盘布置',
    goal: '把课后练习与针对性复习任务下发到位。',
    entries: ['/teacher/papers', '/teacher/exam-tasks', '/messages'],
    steps: [
      '在组卷中心按课堂问题生成课后作业卷。',
      '通过考试任务管理确认作业下发成功与完成时限。',
      '在消息中心发送作业提醒与完成标准。',
    ],
    output: '课后作业任务与学生提醒已闭环。',
  },
  {
    key: 'weekly-review',
    phase: '周度',
    title: '周教学复盘',
    goal: '按周汇总班级学习表现并确定下周教学重点。',
    entries: ['/teacher/analytics', '/teacher/questions', '/messages'],
    steps: [
      '在学情管理导出周维度正确率与风险学生数据。',
      '回到题库管理补齐高错知识点的训练题。',
      '通过消息中心推送周总结和下周学习建议。',
    ],
    output: '周复盘报告与下周教学计划。',
  },
  {
    key: 'monthly-mock',
    phase: '月度',
    title: '月考/模考组织',
    goal: '完成阶段性测评并据此调整教学节奏。',
    entries: ['/teacher/papers', '/teacher/exam-tasks', '/teacher/analytics'],
    steps: [
      '在组卷中心制作月考卷（可用模板或 AI 组卷）。',
      '在考试任务管理发布月考并跟踪全班完成情况。',
      '在学情管理对比班级趋势，识别持续低掌握知识点。',
    ],
    output: '月度测评结果与教学节奏调整建议。',
  },
  {
    key: 'sprint-before-exam',
    phase: '冲刺',
    title: '考前冲刺提分',
    goal: '集中火力覆盖高频高分点，提升短期得分效率。',
    entries: ['/teacher/analytics', '/teacher/questions', '/teacher/papers', '/messages'],
    steps: [
      '从学情管理锁定高频失分章节与风险学生分层。',
      '在题库管理快速筛题，组装冲刺专题卷。',
      '通过消息中心分群发送冲刺安排与每日任务。',
    ],
    output: '冲刺卷包与分层任务执行方案。',
  },
  {
    key: 'new-student-onboard',
    phase: '运营',
    title: '新生入班与账号开通',
    goal: '保障新生及时获得练习权限并进入教学主流程。',
    entries: ['/teacher/student-accounts', '/teacher/home', '/messages'],
    steps: [
      '在学生账号开通页完成账号启用与范围绑定。',
      '回到教师工作台确认新增学生已进入统计口径。',
      '在消息中心发送入班学习指引与首周任务。',
    ],
    output: '新生账号可用、学习指引已触达。',
  },
  {
    key: 'content-governance',
    phase: '治理',
    title: '题库内容维护日',
    goal: '持续清理题库质量问题，保证讲练材料稳定。',
    entries: ['/teacher/questions', '/teacher/knowledge', '/teacher/content-system'],
    steps: [
      '在题库管理处理待终审、驳回和重复题等积压项。',
      '在知识点管理修复节点归属和排序异常。',
      '在内容体系字典复核门类和科目覆盖是否均衡。',
    ],
    output: '题库质量与知识结构保持健康。',
  },
  {
    key: 'teaching-alert',
    phase: '应急',
    title: '异常场景快速处置',
    goal: '在考试任务异常、消息漏发或数据异常时快速止损。',
    entries: ['/teacher/exam-tasks', '/messages', '/teacher/analytics'],
    steps: [
      '在考试任务管理定位异常任务并确认影响范围。',
      '在消息中心向受影响学生补发说明与替代安排。',
      '在学情管理追踪异常时段数据，确认是否需要补测。',
    ],
    output: '异常通知、补救动作和影响追踪完成。',
  },
]

const weeklyRhythm = [
  '周一：备课选题 + 本周任务下发。',
  '周二到周四：随堂检测 + 课后作业追踪。',
  '周五：周复盘导出 + 下周重点确认。',
  '周末：冲刺训练或阶段测评（按教学安排启用）。',
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
  <section class="teacher-guide-page">
    <header class="guide-header">
      <div>
        <p class="guide-header__eyebrow">教师端</p>
        <h3>使用文档（全功能）</h3>
        <p>
          本页覆盖教师端当前全部功能模块、入口路径和权限对应关系。
          建议新老师先按“工作台 -> 题库管理 -> 组卷中心 -> 学情管理 -> 消息中心”顺序熟悉主链路。
        </p>
      </div>
      <el-tag type="success" effect="dark">完整功能清单</el-tag>
    </header>

    <section class="module-section">
      <header class="section-header">
        <h4>一、功能模块与入口</h4>
        <p>点击“进入模块”可直接跳转到对应页面。</p>
      </header>

      <div class="module-grid">
        <article
          v-for="item in featureModules"
          :key="item.key"
          class="module-card"
        >
          <header>
            <h5>{{ item.name }}</h5>
            <el-button link type="primary" @click="openPath(item.entry)">进入模块</el-button>
          </header>
          <p class="entry-path">入口：{{ item.entry }}</p>
          <ul>
            <li v-for="capability in item.capabilities" :key="capability">{{ capability }}</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="module-section">
      <header class="section-header">
        <h4>二、权限点对应关系</h4>
        <p>若某模块不可见或按钮不可点，请先核对账号权限。</p>
      </header>

      <el-table :data="permissionMap" border>
        <el-table-column prop="permission" label="权限点" min-width="180" />
        <el-table-column prop="module" label="覆盖模块" min-width="320" />
      </el-table>
    </section>

    <section class="module-section">
      <header class="section-header">
        <h4>三、日常教学场景（可覆盖尽量全覆盖）</h4>
        <p>以下场景按当前已上线教师端能力整理，覆盖课前、课中、课后、周度、月度、冲刺与异常处置。</p>
      </header>

      <div class="scenario-grid">
        <article
          v-for="item in dailyScenarios"
          :key="item.key"
          class="scenario-card"
        >
          <header class="scenario-card__head">
            <h5>{{ item.title }}</h5>
            <el-tag size="small" type="info">{{ item.phase }}</el-tag>
          </header>
          <p class="scenario-goal">目标：{{ item.goal }}</p>
          <p class="entry-path">入口：{{ item.entries.join(' -> ') }}</p>
          <ol>
            <li v-for="step in item.steps" :key="step">{{ step }}</li>
          </ol>
          <p class="scenario-output">产出：{{ item.output }}</p>
        </article>
      </div>
    </section>

    <section class="module-section">
      <header class="section-header">
        <h4>四、建议执行节奏</h4>
      </header>
      <ol class="guide-steps">
        <li v-for="item in weeklyRhythm" :key="item">{{ item }}</li>
      </ol>
    </section>
  </section>
</template>

<style scoped>
.teacher-guide-page {
  display: grid;
  gap: 14px;
}

.guide-header,
.module-section {
  border: 1px solid var(--qb-border-soft);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  padding: 18px;
}

.guide-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.guide-header__eyebrow {
  margin: 0;
  color: var(--qb-text-info-ink);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.guide-header h3,
.guide-header p {
  margin: 0;
}

.guide-header h3 {
  margin-top: 6px;
  color: var(--qb-text-heading);
  font-size: clamp(24px, 3vw, 32px);
}

.guide-header p {
  margin-top: 8px;
  color: var(--qb-text-copy);
  line-height: 1.7;
  max-width: 820px;
}

.section-header h4,
.section-header p {
  margin: 0;
}

.section-header p {
  margin-top: 6px;
  color: var(--qb-text-subtle-7);
}

.module-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.module-card {
  border: 1px solid var(--qb-border-soft);
  border-radius: 14px;
  background: linear-gradient(140deg, rgba(239, 246, 255, 0.84), rgba(255, 255, 255, 0.98));
  padding: 14px;
  display: grid;
  gap: 10px;
}

.module-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.module-card h5,
.entry-path {
  margin: 0;
}

.entry-path {
  color: var(--qb-text-info-ink);
  font-size: 12px;
}

.module-card ul,
.scenario-card ol,
.guide-steps {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
  color: var(--qb-text-copy);
  line-height: 1.6;
}

.scenario-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.scenario-card {
  border: 1px solid var(--qb-border-soft);
  border-radius: 14px;
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

.scenario-card__head h5 {
  margin: 0;
}

.scenario-goal,
.scenario-output {
  margin: 0;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.6;
}

.scenario-output {
  color: var(--qb-text-info-ink);
}

.guide-steps {
  margin-top: 10px;
}

@media (max-width: 920px) {
  .guide-header {
    flex-direction: column;
  }

  .module-grid,
  .scenario-grid {
    grid-template-columns: 1fr;
  }
}
</style>
