function toText(value) {
  return String(value || '').trim()
}

function normalizeSubjectLabel(subjectCode = '', subjectName = '') {
  const normalizedName = toText(subjectName)
  if (normalizedName && normalizedName !== '当前科目') {
    return normalizedName
  }

  const normalizedCode = toText(subjectCode).toUpperCase()
  const fallbackMap = {
    ADVANCED_MATH: '高等数学',
    ADVANCED_MATH_1: '高等数学一',
    ADVANCED_MATH_2: '高等数学二',
    ENGLISH: '英语',
    POLITICS: '政治',
    COMPUTER: '计算机基础',
  }

  return fallbackMap[normalizedCode] || normalizedName || normalizedCode || '当前科目'
}

function stringifyExtJson(extJson) {
  return JSON.stringify(extJson)
}

function buildPreviewQuestion({
  questionId,
  type = 'single_choice',
  stem,
  options,
  score,
  correctAnswer,
  analysis,
  difficulty,
  timeLimitSec,
  knowledgeTags,
  subjectCode,
  paper,
}) {
  return {
    id: questionId,
    type,
    stem,
    answer: toText(correctAnswer),
    optionsJson: JSON.stringify(options),
    extJson: stringifyExtJson({
      subjectCode: toText(subjectCode),
      analysis: toText(analysis),
      difficulty,
      knowledgeTags,
      practiceConfig: {
        timeLimitSec: Number(timeLimitSec || 0),
      },
      paperBindings: [
        {
          paperId: paper.paperId,
          paperName: paper.paperName,
          durationMinutes: paper.durationMinutes,
          questionScore: Number(score || 0),
        },
      ],
    }),
  }
}

function buildPreviewPapers({ subjectCode = '', subjectName = '' } = {}) {
  const normalizedSubjectCode = toText(subjectCode) || 'COMMON'
  const subjectLabel = normalizeSubjectLabel(subjectCode, subjectName)

  const sprintPaper = {
    paperId: `preview-mock-${normalizedSubjectCode.toLowerCase()}-sprint`,
    paperName: `${subjectLabel} 冲刺预测卷 A`,
    durationMinutes: 45,
  }
  const stablePaper = {
    paperId: `preview-mock-${normalizedSubjectCode.toLowerCase()}-stable`,
    paperName: `${subjectLabel} 节奏校准卷 B`,
    durationMinutes: 35,
  }

  return [
    {
      ...sprintPaper,
      questions: [
        buildPreviewQuestion({
          questionId: `${sprintPaper.paperId}-q1`,
          stem: `【预览卷】${subjectLabel}第 1 题：若系统希望你先锁定核心概念，再展开整卷练习，最合适的策略是？`,
          options: [
            { key: 'A', content: '先完成基础定义辨析，再进入综合题' },
            { key: 'B', content: '直接跳到最后一道大题' },
            { key: 'C', content: '只看答案不作答' },
            { key: 'D', content: '随机切题，忽略题型顺序' },
          ],
          score: 5,
          correctAnswer: 'A',
          analysis: '预览卷默认建议先完成基础定义辨析，再进入整卷推进。',
          difficulty: 'easy',
          timeLimitSec: 60,
          knowledgeTags: ['核心概念', '题感热身'],
          subjectCode,
          paper: sprintPaper,
        }),
        buildPreviewQuestion({
          questionId: `${sprintPaper.paperId}-q2`,
          stem: `【预览卷】${subjectLabel}第 2 题：进入模考后，最能体现真实考试节奏的页面反馈应该是？`,
          options: [
            { key: 'A', content: '展示全局倒计时、题号推进和当前试卷信息' },
            { key: 'B', content: '展示章节树和所有运营提示' },
            { key: 'C', content: '每答一题都立即弹解析' },
            { key: 'D', content: '每隔十秒弹一次激励文案' },
          ],
          score: 5,
          correctAnswer: 'A',
          analysis: '真实考试感最强的反馈是倒计时、题号推进和试卷上下文同步存在。',
          difficulty: 'medium',
          timeLimitSec: 75,
          knowledgeTags: ['考试节奏', '界面识别'],
          subjectCode,
          paper: sprintPaper,
        }),
        buildPreviewQuestion({
          questionId: `${sprintPaper.paperId}-q3`,
          type: 'judge',
          stem: `【预览卷】${subjectLabel}第 3 题：模拟考试阶段应尽量避免在作答中途展示“本题对错”和完整解析。`,
          options: [
            { key: 'T', content: '正确' },
            { key: 'F', content: '错误' },
          ],
          score: 4,
          correctAnswer: 'T',
          analysis: '模考阶段不应边做边给对错和解析，统一交卷后再看更符合考试情境。',
          difficulty: 'easy',
          timeLimitSec: 45,
          knowledgeTags: ['考试反馈规则'],
          subjectCode,
          paper: sprintPaper,
        }),
        buildPreviewQuestion({
          questionId: `${sprintPaper.paperId}-q4`,
          stem: `【预览卷】${subjectLabel}第 4 题：若你想快速确认整卷覆盖度，最需要优先补齐哪块信息？`,
          options: [
            { key: 'A', content: '答题卡状态与未答题标识' },
            { key: 'B', content: '社区热帖入口' },
            { key: 'C', content: '课程推荐海报' },
            { key: 'D', content: '排行榜分享按钮' },
          ],
          score: 6,
          correctAnswer: 'A',
          analysis: '整卷覆盖度的核心是题号状态和未答题提醒，而不是运营入口。',
          difficulty: 'medium',
          timeLimitSec: 70,
          knowledgeTags: ['答题卡', '状态可见性'],
          subjectCode,
          paper: sprintPaper,
        }),
        buildPreviewQuestion({
          questionId: `${sprintPaper.paperId}-q5`,
          stem: `【预览卷】${subjectLabel}第 5 题：系统在模考中记录已作答题数，最直接服务于哪类信息展示？`,
          options: [
            { key: 'A', content: '当前推进与剩余题数' },
            { key: 'B', content: '课程销量趋势' },
            { key: 'C', content: '教师排课安排' },
            { key: 'D', content: '站点访问来源' },
          ],
          score: 5,
          correctAnswer: 'A',
          analysis: '已答题数和剩余题数是考生最直接的节奏反馈。',
          difficulty: 'medium',
          timeLimitSec: 65,
          knowledgeTags: ['进度感知', '考试反馈'],
          subjectCode,
          paper: sprintPaper,
        }),
        buildPreviewQuestion({
          questionId: `${sprintPaper.paperId}-q6`,
          stem: `【预览卷】${subjectLabel}第 6 题：如果发生网络波动，哪种体验更符合模考场景的预期？`,
          options: [
            { key: 'A', content: '自动保存并在恢复后继续当前试卷' },
            { key: 'B', content: '直接清空所有答案重新开始' },
            { key: 'C', content: '强制跳回首页' },
            { key: 'D', content: '关闭试卷入口一天' },
          ],
          score: 5,
          correctAnswer: 'A',
          analysis: '异常场景下自动保存并恢复进度，比强制重来更符合模考体验。',
          difficulty: 'hard',
          timeLimitSec: 80,
          knowledgeTags: ['断点恢复', '稳定性'],
          subjectCode,
          paper: sprintPaper,
        }),
      ],
    },
    {
      ...stablePaper,
      questions: [
        buildPreviewQuestion({
          questionId: `${stablePaper.paperId}-q1`,
          stem: `【预览卷】${subjectLabel}第 1 题：考前校准卷更适合验证哪种能力？`,
          options: [
            { key: 'A', content: '题型切换与时间分配是否稳定' },
            { key: 'B', content: '首页配色是否好看' },
            { key: 'C', content: '消息中心未读数是否增长' },
            { key: 'D', content: '积分海报是否可下载' },
          ],
          score: 5,
          correctAnswer: 'A',
          analysis: '校准卷更适合验证题型切换和时间分配是否稳定。',
          difficulty: 'easy',
          timeLimitSec: 60,
          knowledgeTags: ['时间分配', '节奏校准'],
          subjectCode,
          paper: stablePaper,
        }),
        buildPreviewQuestion({
          questionId: `${stablePaper.paperId}-q2`,
          type: 'judge',
          stem: `【预览卷】${subjectLabel}第 2 题：沉浸模考模式下隐藏站点级导航，有助于降低分心。`,
          options: [
            { key: 'T', content: '正确' },
            { key: 'F', content: '错误' },
          ],
          score: 4,
          correctAnswer: 'T',
          analysis: '沉浸模考隐藏站点级导航，可以明显减少非考试信息干扰。',
          difficulty: 'easy',
          timeLimitSec: 45,
          knowledgeTags: ['沉浸模式'],
          subjectCode,
          paper: stablePaper,
        }),
        buildPreviewQuestion({
          questionId: `${stablePaper.paperId}-q3`,
          stem: `【预览卷】${subjectLabel}第 3 题：如果需要在交卷前做最后检查，最有帮助的模块是？`,
          options: [
            { key: 'A', content: '可跳转的题号条与未答题提醒' },
            { key: 'B', content: '首页学习日报' },
            { key: 'C', content: '错题本章节统计' },
            { key: 'D', content: '积分排行榜' },
          ],
          score: 6,
          correctAnswer: 'A',
          analysis: '交卷前最有价值的是按题号快速回看未答和待查题。',
          difficulty: 'medium',
          timeLimitSec: 70,
          knowledgeTags: ['交卷前检查'],
          subjectCode,
          paper: stablePaper,
        }),
        buildPreviewQuestion({
          questionId: `${stablePaper.paperId}-q4`,
          stem: `【预览卷】${subjectLabel}第 4 题：为了让用户感到“像在考试”，下面哪项更值得优先补？`,
          options: [
            { key: 'A', content: '倒计时、交卷确认和未答题校验' },
            { key: 'B', content: '更多营销入口' },
            { key: 'C', content: '更复杂的排行榜文案' },
            { key: 'D', content: '首页轮播广告' },
          ],
          score: 6,
          correctAnswer: 'A',
          analysis: '倒计时、交卷确认和未答题检查是最核心的考试感组件。',
          difficulty: 'hard',
          timeLimitSec: 90,
          knowledgeTags: ['考试感', '交互优先级'],
          subjectCode,
          paper: stablePaper,
        }),
      ],
    },
  ]
}

export function buildMockExamPreviewRows({ subjectCode = '', subjectName = '' } = {}) {
  return buildPreviewPapers({ subjectCode, subjectName }).flatMap((paper) => paper.questions)
}

export function listMockExamPreviewQuestions(paperId, { subjectCode = '', subjectName = '' } = {}) {
  const normalizedPaperId = toText(paperId)
  const matchedPaper = buildPreviewPapers({ subjectCode, subjectName }).find(
    (paper) => paper.paperId === normalizedPaperId,
  )
  return Array.isArray(matchedPaper?.questions) ? matchedPaper.questions : []
}

export function isMockExamPreviewPaper(paperId) {
  return toText(paperId).startsWith('preview-mock-')
}
