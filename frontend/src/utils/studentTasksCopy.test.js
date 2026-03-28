import { describe, expect, it } from 'vitest'
import {
  buildDailyTaskScopeCopy,
  buildTaskOverviewCards,
  buildTaskRecordHeading,
  buildTaskRecordScopeCopy,
  buildTaskStatusMeta,
  buildTaskSummaryFootnote,
  buildTasksErrorState,
  buildTasksExecutionScopeNote,
  buildWeakPointScopeCopy,
  normalizeTaskRecord,
} from './studentTasksCopy'

describe('studentTasksCopy', () => {
  it('builds execution scope note with subject name', () => {
    expect(buildTasksExecutionScopeNote('政治')).toBe(
      '今日任务按全局学习节奏汇总展示；弱项提醒覆盖全部科目，点击后按对应科目进入补强。',
    )
  })

  it('falls back when subject name is empty', () => {
    expect(buildTasksExecutionScopeNote('')).toContain('覆盖全部科目')
    expect(buildWeakPointScopeCopy('')).toContain('覆盖全部科目')
  })

  it('builds global task summary footnote for empty, partial and full totals', () => {
    expect(buildTaskSummaryFootnote(0, 0)).toBe('当前还没有可展示的全局任务记录。')
    expect(buildTaskSummaryFootnote(8, 23)).toBe('以下摘要基于最近 8 条全局记录，全量共 23 条任务。')
    expect(buildTaskSummaryFootnote(8, 8)).toBe('以下摘要基于当前可见的 8 条全局任务记录。')
  })

  it('keeps task and weakness scope copy stable', () => {
    expect(buildDailyTaskScopeCopy()).toContain('不按当前科目拆分')
    expect(buildTaskRecordScopeCopy()).toContain('全局汇总口径')
    expect(buildWeakPointScopeCopy('英语')).toContain('弱项提醒覆盖全部科目')
  })

  it('builds overview cards and record heading with recent-record wording', () => {
    expect(buildTaskOverviewCards({
      recentTaskCount: 12,
      runningCount: 3,
      failedCount: 2,
      completedCount: 7,
    })).toEqual([
      { label: '最近记录', value: 12, helper: '基于当前可见任务记录' },
      { label: '最近进行中', value: 3, helper: '当前列表内仍在执行', tone: 'info' },
      { label: '最近失败', value: 2, helper: '优先恢复这部分任务', tone: 'danger' },
      { label: '最近完成', value: 7, helper: '当前列表内已完成记录', tone: 'success' },
    ])
    expect(buildTaskRecordHeading(2)).toBe('待恢复与最近执行')
    expect(buildTaskRecordHeading(0)).toBe('最近执行记录')
  })

  it('builds tasks error state for each page section', () => {
    expect(buildTasksErrorState('dashboard', '接口超时')).toEqual({
      title: '今日任务暂时加载失败',
      message: '接口超时',
    })
    expect(buildTasksErrorState('taskList', '')).toEqual({
      title: '任务记录暂时加载失败',
      message: '任务流水加载失败',
    })
    expect(buildTasksErrorState('graphSummary')).toEqual({
      title: '弱项摘要加载失败',
      message: '弱项摘要加载失败',
    })
    expect(buildTasksErrorState('weakPoint')).toEqual({
      title: '弱项提醒暂时加载失败',
      message: '弱项摘要加载失败',
    })
  })

  it('builds task status meta with correct action semantics', () => {
    expect(buildTaskStatusMeta('FAILED', true)).toEqual({
      tone: 'danger',
      label: '执行失败',
      actionLabel: '重试任务',
    })
    expect(buildTaskStatusMeta('RUNNING', false)).toEqual({
      tone: 'info',
      label: '进行中',
      actionLabel: '查看进度',
    })
    expect(buildTaskStatusMeta('COMPLETED', true)).toEqual({
      tone: 'success',
      label: '已完成',
      actionLabel: '再次进入',
    })
    expect(buildTaskStatusMeta('QUEUED', false)).toEqual({
      tone: 'neutral',
      label: 'QUEUED',
      actionLabel: '查看诊断',
    })
  })

  it('normalizes task records with stable fallbacks and bounded progress', () => {
    expect(normalizeTaskRecord({
      taskId: 'task-1',
      taskName: '完成章节刷题',
      actionLabel: '去完成',
      updateTime: '2026-03-23 16:00',
      progress: 135,
      status: 'RUNNING',
      actionPath: '/student/practice',
    }, 0)).toEqual({
      taskId: 'task-1',
      taskName: '完成章节刷题',
      actionLabel: '继续执行',
      updateTime: '2026-03-23 16:00',
      progress: 135,
      status: 'RUNNING',
      actionPath: '/student/practice',
      recordId: 'task-1',
      title: '完成章节刷题',
      summary: '去完成',
      helper: '2026-03-23 16:00',
      progressValue: 100,
      statusLabel: '进行中',
      statusTone: 'info',
      hasExplicitAction: true,
    })

    expect(normalizeTaskRecord({
      type: 'AI_TUTOR',
      status: 'QUEUED',
      progress: -5,
    }, 2)).toEqual({
      type: 'AI_TUTOR',
      status: 'QUEUED',
      progress: -5,
      recordId: 'record-2',
      title: 'AI_TUTOR',
      summary: 'AI_TUTOR',
      helper: '-',
      progressValue: 0,
      statusLabel: 'QUEUED',
      statusTone: 'neutral',
      actionLabel: '查看诊断',
      hasExplicitAction: false,
    })
  })
})
