import { describe, expect, it } from 'vitest'
import {
  buildStudentPracticeRouteLocation,
  STUDENT_PRACTICE_MODULE,
  STUDENT_PRACTICE_SOURCE,
  resolveStudentPracticeSourceDescriptor,
} from './studentPracticeNavigation'

describe('studentPracticeNavigation helpers', () => {
  it('prefers explicit module when provided', () => {
    expect(buildStudentPracticeRouteLocation({
      module: STUDENT_PRACTICE_MODULE.MOCK,
      subjectCode: 'POLITICS',
    })).toEqual({
      path: '/student/practice/mock',
      query: {
        module: 'mock',
        subjectCode: 'POLITICS',
      },
    })
  })

  it('falls back to extraQuery module when module param is omitted', () => {
    expect(buildStudentPracticeRouteLocation({
      subjectCode: 'POLITICS',
      knowledgePathNodeId: 'l5-node-9',
      practiceSource: STUDENT_PRACTICE_SOURCE.TASK,
      practiceSourceLabel: '完成1次模拟考试',
      extraQuery: { module: 'mock' },
    })).toEqual({
      path: '/student/practice/mock',
      query: {
        module: 'mock',
        subjectCode: 'POLITICS',
        knowledgePathNodeId: 'l5-node-9',
        practiceSource: 'TASK',
        practiceSourceLabel: '完成1次模拟考试',
      },
    })
  })

  it('defaults to chapter route when no module is provided', () => {
    expect(buildStudentPracticeRouteLocation({
      subjectCode: 'ENGLISH',
    })).toEqual({
      path: '/student/practice/chapter',
      query: {
        module: 'chapter',
        subjectCode: 'ENGLISH',
      },
    })
  })

  it('resolves task source descriptor with task copy', () => {
    expect(resolveStudentPracticeSourceDescriptor('TASK', '')).toEqual({
      key: 'TASK',
      title: '今日任务进入',
      description: '当前练习来自知识诊断今日任务，先把今天该拿的分拿下来，再扩展更多练习。',
    })
  })

  it('resolves home and points source descriptors with dedicated copy', () => {
    expect(resolveStudentPracticeSourceDescriptor(STUDENT_PRACTICE_SOURCE.HOME, '')).toEqual({
      key: 'HOME',
      title: '学习首页进入',
      description: '当前练习来自学习首页主线，适合顺着诊断、任务、刷题的节奏快速进入状态。',
    })
    expect(resolveStudentPracticeSourceDescriptor(STUDENT_PRACTICE_SOURCE.POINTS, '')).toEqual({
      key: 'POINTS',
      title: '积分页进入',
      description: '当前练习来自刷题段位页，适合一边冲积分，一边把正确输出练成升本时能稳定拿分的状态。',
    })
  })

  it('supports learning method recommendation source and adaptive query forwarding', () => {
    expect(buildStudentPracticeRouteLocation({
      module: STUDENT_PRACTICE_MODULE.FREE,
      subjectCode: 'ENGLISH',
      adaptiveQuestionIds: ['Q-01', 'Q-02', 'Q-01'],
      adaptiveDimension: 'LM_TIME_BLOCK',
      adaptiveMastery: '64.2',
      practiceSource: STUDENT_PRACTICE_SOURCE.LEARNING_METHOD,
      practiceSourceLabel: '学习方法推荐题包',
      extraQuery: { immersive: '1' },
    })).toEqual({
      path: '/student/practice/free',
      query: {
        immersive: '1',
        module: 'free',
        subjectCode: 'ENGLISH',
        adaptiveQuestionIds: 'Q-01,Q-02',
        adaptiveDimension: 'LM_TIME_BLOCK',
        adaptiveMastery: '64.2',
        practiceSource: 'LEARNING_METHOD',
        practiceSourceLabel: '学习方法推荐题包',
      },
    })
    expect(resolveStudentPracticeSourceDescriptor(STUDENT_PRACTICE_SOURCE.LEARNING_METHOD, '')).toEqual({
      key: 'LEARNING_METHOD',
      title: '学习方法推荐进入',
      description: '当前练习来自学习方法推荐题包，建议先完成定向题再回到方法页反馈匹配效果。',
    })
  })
})
