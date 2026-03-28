import { describe, expect, it } from 'vitest'
import { buildKnowledgeSelectorState } from './knowledgeTree'
import {
  buildStudentGalaxyModel,
  buildStudentGalaxySunburstData,
  classifyGalaxyMasteryBand,
} from './studentAnalysisGalaxy'

const graphPayload = {
  nodes: [
    { id: 'subject-root', label: '政治', level: 1, sort: 10, mastery: 0.8, questionCount: 0 },
    { id: 'module-root', label: '具体内容与要求', level: 3, sort: 10, mastery: 0.8, questionCount: 0, parentId: 'subject-root' },
    { id: 'chapter-a', label: '马克思主义哲学', level: 4, sort: 10, mastery: 0.7, questionCount: 0, parentId: 'module-root' },
    { id: 'chapter-b', label: '毛泽东思想概论', level: 4, sort: 20, mastery: 0.7, questionCount: 0, parentId: 'module-root' },
    { id: 'point-a1', label: '世界的物质统一性', shortLabel: '物质统一性', fullLabel: '世界的物质统一性', level: 5, sort: 10, mastery: 0.92, questionCount: 5, wrongCount: 1, parentId: 'chapter-a' },
    { id: 'point-a2', label: '联系与发展', level: 5, sort: 20, mastery: 0.56, questionCount: 3, wrongCount: 4, parentId: 'chapter-a' },
    { id: 'point-b1', label: '新民主主义革命', level: 5, sort: 10, mastery: 0, questionCount: 4, wrongCount: 2, parentId: 'chapter-b' },
  ],
  links: [
    { source: 'subject-root', target: 'module-root', type: 'parent' },
    { source: 'module-root', target: 'chapter-a', type: 'parent' },
    { source: 'module-root', target: 'chapter-b', type: 'parent' },
    { source: 'chapter-a', target: 'point-a1', type: 'parent' },
    { source: 'chapter-a', target: 'point-a2', type: 'parent' },
    { source: 'chapter-b', target: 'point-b1', type: 'parent' },
  ],
}

describe('studentAnalysisGalaxy', () => {
  it('classifies mastery bands with the requested thresholds', () => {
    expect(classifyGalaxyMasteryBand(0)).toBe('unpracticed')
    expect(classifyGalaxyMasteryBand(0.59)).toBe('weak')
    expect(classifyGalaxyMasteryBand(0.6)).toBe('fuzzy')
    expect(classifyGalaxyMasteryBand(0.86)).toBe('strong')
  })

  it('builds chapter and point rows from the L4/L5 subtree', () => {
    const selectorState = buildKnowledgeSelectorState(graphPayload)
    const model = buildStudentGalaxyModel(selectorState)

    expect(model.subjectRootLabel).toBe('政治')
    expect(model.chapterCount).toBe(2)
    expect(model.pointCount).toBe(3)
    expect(model.averageMastery).toBe(49)
    expect(model.wrongCount).toBe(7)
    expect(model.chapterRows.map((item) => item.label)).toEqual(['马克思主义哲学', '毛泽东思想概论'])
    expect(model.chapterRows[0].wrongCount).toBe(5)
    expect(model.chapterRows[0].points.map((item) => item.masteryBand)).toEqual(['strong', 'weak'])
    expect(model.chapterRows[1].points[0]).toEqual(
      expect.objectContaining({
        label: '新民主主义革命',
        displayLabel: '新民主主义革命',
        masteryBand: 'unpracticed',
        wrongCount: 2,
      }),
    )
    expect(model.chapterRows[0].points[0]).toEqual(
      expect.objectContaining({
        label: '世界的物质统一性',
        displayLabel: '物质统一性',
        fullLabel: '世界的物质统一性',
      }),
    )
  })

  it('produces a sunburst tree with subject, chapter and point metadata', () => {
    const selectorState = buildKnowledgeSelectorState(graphPayload)
    const model = buildStudentGalaxyModel(selectorState)
    const tree = buildStudentGalaxySunburstData(model, (_mastery, band) => band)

    expect(tree).toHaveLength(1)
    expect(tree[0]).toEqual(
      expect.objectContaining({
        id: 'subject-root',
        name: '政治',
      }),
    )
    expect(tree[0].children[0]).toEqual(
      expect.objectContaining({
        name: '马克思主义哲学',
        itemStyle: { color: 'fuzzy' },
        meta: expect.objectContaining({ wrongCount: 5 }),
      }),
    )
    expect(tree[0].children[1].children[0]).toEqual(
      expect.objectContaining({
        name: '新民主主义革命',
        itemStyle: { color: 'unpracticed' },
        meta: expect.objectContaining({ wrongCount: 2 }),
      }),
    )
    expect(tree[0].children[0].children[0]).toEqual(
      expect.objectContaining({
        name: '物质统一性',
        meta: expect.objectContaining({
          label: '物质统一性',
          fullLabel: '世界的物质统一性',
        }),
      }),
    )
  })
})
