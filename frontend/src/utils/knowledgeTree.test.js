import { describe, expect, it } from 'vitest'
import {
  buildKnowledgeGraphIndex,
  buildKnowledgeLevelTreeState,
  buildKnowledgeSelectorState,
  buildKnowledgeSemanticMap,
} from './knowledgeTree'

const fourLevelSubjectGraph = {
  nodes: [
    { id: 'subject-root', label: '艺术概论', level: 1, sort: 10 },
    { id: 'module-root', label: '艺术本质论', level: 2, sort: 10, parentId: 'subject-root' },
    { id: 'chapter-a', label: '艺术起源', level: 3, sort: 10, parentId: 'module-root' },
    { id: 'point-a1', label: '劳动起源说', level: 4, sort: 10, parentId: 'chapter-a' },
  ],
  links: [
    { source: 'subject-root', target: 'module-root', type: 'parent' },
    { source: 'module-root', target: 'chapter-a', type: 'parent' },
    { source: 'chapter-a', target: 'point-a1', type: 'parent' },
  ],
}

describe('knowledgeTree normalization', () => {
  it('normalizes four-level subjects into the shared L3/L4/L5 display contract', () => {
    const graphIndex = buildKnowledgeGraphIndex(fourLevelSubjectGraph)

    expect(graphIndex.rawLevelById).toEqual({
      'subject-root': 1,
      'module-root': 2,
      'chapter-a': 3,
      'point-a1': 4,
    })
    expect(graphIndex.levelById).toEqual({
      'subject-root': 1,
      'module-root': 3,
      'chapter-a': 4,
      'point-a1': 5,
    })
  })

  it('builds selector options, chapter codes and point codes from normalized levels', () => {
    const selectorState = buildKnowledgeSelectorState(fourLevelSubjectGraph)
    const levelTreeState = buildKnowledgeLevelTreeState(selectorState, { startLevel: 3, endLevel: 5 })
    const semanticMap = buildKnowledgeSemanticMap(selectorState)

    expect(levelTreeState.options).toEqual([
      {
        value: 'module-root',
        label: '艺术本质论',
        level: 3,
        leaf: false,
        children: [
          {
            value: 'chapter-a',
            label: '艺术起源',
            level: 4,
            leaf: false,
            children: [
              {
                value: 'point-a1',
                label: '劳动起源说',
                level: 5,
                leaf: true,
                children: [],
              },
            ],
          },
        ],
      },
    ])
    expect(selectorState.chapterCodeMap).toEqual({ 'chapter-a': 'CH_001' })
    expect(selectorState.pointCodeMap).toEqual({ 'point-a1': 'PT_001_001' })
    expect(selectorState.searchOptions[0]).toEqual(
      expect.objectContaining({
        nodeId: 'point-a1',
        pathLabel: '艺术起源 / 劳动起源说',
      }),
    )
    expect(semanticMap['module-root']).toEqual(
      expect.objectContaining({
        level: 3,
        levelLabel: 'L3 模块',
      }),
    )
    expect(semanticMap['point-a1']).toEqual(
      expect.objectContaining({
        level: 5,
        levelLabel: 'L5 原子知识点',
      }),
    )
  })
})
