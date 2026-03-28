import { describe, expect, it } from 'vitest'
import {
  buildTeacherContentOutlineTree,
  buildTeacherExamSectionSummary,
  buildTeacherKnowledgeIndex,
  buildTeacherMindmapLayout,
  buildTeacherNodeDetail,
  resolveTeacherSpecialSections,
  buildTeacherVisibleSummary,
  collectTeacherVisibleNodeIds,
  resolveTeacherFocusNodeId,
} from './knowledgeGraphTeacher'

const graphPayload = {
  nodes: [
    { id: 'subject-root', label: '信息技术概论', level: 1, sort: 10, mastery: 0.9, questionCount: 10 },
    { id: 'intro', label: '科目简介', level: 2, sort: 10, mastery: 0.9, questionCount: 0 },
    { id: 'content-root', label: '具体内容与要求', level: 2, sort: 20, mastery: 0.7, questionCount: 0 },
    { id: 'exam-root', label: '考试形式与参考题型', level: 2, sort: 30, mastery: 0.4, questionCount: 0 },
    { id: 'section-1', label: '计算机系统组成', level: 3, sort: 10, mastery: 0.5, questionCount: 4 },
    { id: 'section-2', label: '操作系统', level: 3, sort: 20, mastery: 0.7, questionCount: 5 },
    { id: 'point-1', label: '冯诺依曼结构', level: 5, sort: 10, mastery: 0.2, questionCount: 2 },
    { id: 'point-2', label: '输入输出设备', level: 5, sort: 20, mastery: 0.8, questionCount: 1 },
    { id: 'exam-form', label: '考试形式', level: 3, sort: 10, mastery: 0.1, questionCount: 0 },
    { id: 'exam-type', label: '参考题型', level: 3, sort: 20, mastery: 0.1, questionCount: 0 },
  ],
  links: [
    { source: 'subject-root', target: 'intro', type: 'parent' },
    { source: 'subject-root', target: 'content-root', type: 'parent' },
    { source: 'subject-root', target: 'exam-root', type: 'parent' },
    { source: 'content-root', target: 'section-1', type: 'parent' },
    { source: 'content-root', target: 'section-2', type: 'parent' },
    { source: 'section-1', target: 'point-1', type: 'parent' },
    { source: 'section-1', target: 'point-2', type: 'parent' },
    { source: 'exam-root', target: 'exam-form', type: 'parent' },
    { source: 'exam-root', target: 'exam-type', type: 'parent' },
    { source: 'point-1', target: 'point-2', type: 'prerequisite' },
  ],
}

describe('knowledgeGraphTeacher', () => {
  it('builds outline rows from levels 1-3', () => {
    const index = buildTeacherKnowledgeIndex(graphPayload)
    expect(index.outlineRows.map((item) => item.id)).toEqual(
      expect.arrayContaining(['subject-root', 'content-root', 'exam-root', 'section-1', 'section-2']),
    )
    expect(index.outlineRows).toHaveLength(8)
  })

  it('selects a sensible default focus', () => {
    const index = buildTeacherKnowledgeIndex(graphPayload)
    expect(resolveTeacherFocusNodeId(index, '')).toBe('section-1')
    expect(resolveTeacherFocusNodeId(index, 'section-2')).toBe('section-2')
  })

  it('collects only the focused subtree plus ancestors', () => {
    const index = buildTeacherKnowledgeIndex(graphPayload)
    expect(collectTeacherVisibleNodeIds(index, '')).toEqual(['subject-root', 'section-1', 'section-2'])
    expect(collectTeacherVisibleNodeIds(index, 'section-1')).toEqual(
      expect.arrayContaining(['subject-root', 'section-1', 'point-1', 'point-2']),
    )
  })

  it('builds visible summary and detail metadata', () => {
    const index = buildTeacherKnowledgeIndex(graphPayload)
    const visibleIds = collectTeacherVisibleNodeIds(index, 'section-1')
    expect(buildTeacherVisibleSummary(index, visibleIds)).toEqual({
      visibleNodeCount: 4,
      weakNodeCount: 2,
      detailNodeCount: 2,
      leafNodeCount: 2,
      hiddenNodeCount: 6,
    })
    expect(buildTeacherNodeDetail(index, 'point-2')).toEqual({
      id: 'point-2',
      label: '输入输出设备',
      shortLabel: '输入输出设备',
      fullLabel: '输入输出设备',
      level: 5,
      sort: 20,
      mastery: 0.8,
      questionCount: 1,
      parentId: 'section-1',
      parentLabel: '计算机系统组成',
      childCount: 0,
      outgoingPrerequisiteCount: 0,
      incomingPrerequisiteCount: 1,
    })
  })

  it('extracts content tree and exam summary separately', () => {
    const index = buildTeacherKnowledgeIndex(graphPayload)
    expect(resolveTeacherSpecialSections(index)).toEqual({
      subjectRootId: 'subject-root',
      contentNodeId: 'content-root',
      contentNodeLabel: '具体内容与要求',
      examNodeId: 'exam-root',
      examNodeLabel: '考试形式与参考题型',
      introNodeId: 'intro',
      introNodeLabel: '科目简介',
    })
    expect(buildTeacherContentOutlineTree(index).map((item) => item.id)).toEqual(['section-1', 'section-2'])
    expect(buildTeacherExamSectionSummary(index)).toEqual({
      id: 'exam-root',
      label: '考试形式与参考题型',
      items: [
        {
          id: 'exam-form',
          label: '考试形式',
          shortLabel: '考试形式',
          level: 3,
          children: [],
        },
        {
          id: 'exam-type',
          label: '参考题型',
          shortLabel: '参考题型',
          level: 3,
          children: [],
        },
      ],
    })
  })

  it('builds a mindmap-like layout around the focused chapter', () => {
    const index = buildTeacherKnowledgeIndex(graphPayload)
    const visibleIds = collectTeacherVisibleNodeIds(index, 'section-1')
    const positions = buildTeacherMindmapLayout(index, visibleIds, 'section-1', {
      xCenter: 500,
      yCenter: 300,
      xGap: 200,
      yGap: 100,
    })
    expect(positions.get('section-1')).toEqual({ x: 500, y: 300 })
    expect(positions.get('subject-root')?.x).toBeLessThan(500)
    expect(positions.get('point-1')?.x).toBeGreaterThan(500)
    expect(positions.get('point-2')?.x).toBeGreaterThan(500)
  })
})
