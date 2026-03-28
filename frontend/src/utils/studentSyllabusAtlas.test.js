import { describe, expect, it } from 'vitest'
import {
  buildStudentSyllabusDisplayPlan,
  buildStudentSyllabusGraphPayload,
  buildStudentSyllabusOverview,
  formatStudentSyllabusTimestamp,
  normalizeStudentCoreSubjects,
  normalizeStudentSyllabusCatalog,
  searchStudentSyllabusContent,
} from './studentSyllabusAtlas'

describe('studentSyllabusAtlas', () => {
  it('normalizes and sorts syllabus subjects', () => {
    const catalog = normalizeStudentSyllabusCatalog({
      subjects: [
        {
          subjectCode: 'SUB-2',
          subjectName: '专业课 B',
          subjectType: 'PROFESSIONAL',
          examCategoryCode: 'SCIENCE',
          jointExamGroupCode: 'SCI-2',
        },
        {
          subjectCode: 'PUBLIC-1',
          subjectName: '公共课 A',
          subjectType: 'PUBLIC',
          examCategoryCode: 'SCIENCE',
          jointExamGroupCode: 'SCI-2',
        },
      ],
    })

    expect(catalog.subjects).toHaveLength(2)
    expect(catalog.subjects[0].subjectCode).toBe('PUBLIC-1')
    expect(catalog.subjects[1].subjectCode).toBe('SUB-2')
  })

  it('builds graph payload from subject nodes', () => {
    const graph = buildStudentSyllabusGraphPayload({
      nodes: [
        { id: 'root', name: '科目', level: 1, sort: 10 },
        { id: 'child', parent_id: 'root', name: '具体内容与要求', level: 2, sort: 20 },
      ],
    })

    expect(graph.nodes).toHaveLength(2)
    expect(graph.links).toEqual([{ source: 'root', target: 'child', type: 'parent' }])
  })

  it('summarizes counts from syllabus catalog', () => {
    const summary = buildStudentSyllabusOverview({
      subjects: [
        { subjectCode: 'PUBLIC-1', subjectName: '公共课 A', subjectType: 'PUBLIC', nodeCount: 10, examCategoryCode: 'SCIENCE', jointExamGroupCode: 'SCI-1' },
        { subjectCode: 'SUB-2', subjectName: '专业课 B', subjectType: 'PROFESSIONAL', nodeCount: 16, examCategoryCode: 'SCIENCE', jointExamGroupCode: 'SCI-2' },
      ],
    })

    expect(summary.subjectCount).toBe(2)
    expect(summary.nodeCount).toBe(26)
    expect(summary.publicSubjectCount).toBe(1)
    expect(summary.professionalSubjectCount).toBe(1)
    expect(summary.examCategoryCount).toBe(1)
    expect(summary.jointExamGroupCount).toBe(2)
  })

  it('normalizes student core subjects and removes duplicate subject codes', () => {
    const coreSubjects = normalizeStudentCoreSubjects({
      coreSubjects: [
        { subjectCode: 'POLITICS', subjectName: '政治', subjectType: 'PUBLIC' },
        { subjectCode: 'POLITICS', subjectName: '政治', subjectType: 'PUBLIC' },
        { subjectCode: 'MATH_1', subjectName: '高等数学（一）', subjectType: 'PUBLIC' },
      ],
    })

    expect(coreSubjects).toEqual([
      { subjectCode: 'POLITICS', subjectName: '政治', subjectType: 'PUBLIC' },
      { subjectCode: 'MATH_1', subjectName: '高等数学（一）', subjectType: 'PUBLIC' },
    ])
  })

  it('builds syllabus display plan with current core subjects first and keeps other subjects collapsed later', () => {
    const plan = buildStudentSyllabusDisplayPlan(
      {
        subjects: [
          { subjectCode: 'POLITICS', subjectName: '政治', subjectType: 'PUBLIC' },
          { subjectCode: 'ENGLISH', subjectName: '英语', subjectType: 'PUBLIC' },
          { subjectCode: 'MATH_1', subjectName: '高等数学（一）', subjectType: 'PUBLIC' },
          { subjectCode: 'CHEMISTRY', subjectName: '化工原理', subjectType: 'PROFESSIONAL' },
          { subjectCode: 'ART', subjectName: '艺术概论', subjectType: 'PROFESSIONAL' },
        ],
      },
      {
        coreSubjects: [
          { subjectCode: 'POLITICS', subjectName: '政治' },
          { subjectCode: 'ENGLISH', subjectName: '英语' },
          { subjectCode: 'MATH_1', subjectName: '高等数学（一）' },
          { subjectCode: 'CHEMISTRY', subjectName: '化工原理' },
        ],
      },
    )

    expect(plan.requiredSubjects.map((item) => item.subjectCode)).toEqual([
      'POLITICS',
      'ENGLISH',
      'MATH_1',
      'CHEMISTRY',
    ])
    expect(plan.optionalSubjects.map((item) => item.subjectCode)).toEqual(['ART'])
  })

  it('falls back to the first four subjects when current core subjects are unavailable', () => {
    const plan = buildStudentSyllabusDisplayPlan({
      subjects: [
        { subjectCode: 'SUBJECT_1', subjectName: '科目 1' },
        { subjectCode: 'SUBJECT_2', subjectName: '科目 2' },
        { subjectCode: 'SUBJECT_3', subjectName: '科目 3' },
        { subjectCode: 'SUBJECT_4', subjectName: '科目 4' },
        { subjectCode: 'SUBJECT_5', subjectName: '科目 5' },
      ],
    })

    expect(plan.requiredSubjects.map((item) => item.subjectCode)).toEqual([
      'SUBJECT_1',
      'SUBJECT_2',
      'SUBJECT_3',
      'SUBJECT_4',
    ])
    expect(plan.optionalSubjects.map((item) => item.subjectCode)).toEqual(['SUBJECT_5'])
  })

  it('formats generated timestamp into readable local text and keeps error-safe fallback for invalid input', () => {
    expect(formatStudentSyllabusTimestamp('2026-03-23T09:45:00+08:00')).toBe('2026-03-23 09:45')
    expect(formatStudentSyllabusTimestamp('not-a-date')).toBe('not-a-date')
    expect(formatStudentSyllabusTimestamp('')).toBe('')
  })

  it('searches syllabus content through the frontend data chain and maps matches to visible sections', () => {
    const index = {
      allNodes: [
        { id: 'root', label: '政治', level: 1 },
        { id: 'content', label: '具体内容与要求', level: 2 },
        { id: 'chapter', label: '马克思主义基本原理', level: 3 },
        { id: 'point', label: '唯物史观核心观点', level: 4 },
        { id: 'intro', label: '科目简介', level: 2 },
        { id: 'intro-child', label: '掌握考试目标', level: 3 },
      ],
      nodesById: new Map([
        ['root', { id: 'root', label: '政治', level: 1 }],
        ['content', { id: 'content', label: '具体内容与要求', level: 2 }],
        ['chapter', { id: 'chapter', label: '马克思主义基本原理', level: 3 }],
        ['point', { id: 'point', label: '唯物史观核心观点', level: 4 }],
        ['intro', { id: 'intro', label: '科目简介', level: 2 }],
        ['intro-child', { id: 'intro-child', label: '掌握考试目标', level: 3 }],
      ]),
      parentByChild: new Map([
        ['content', 'root'],
        ['chapter', 'content'],
        ['point', 'chapter'],
        ['intro', 'root'],
        ['intro-child', 'intro'],
      ]),
    }

    const contentResult = searchStudentSyllabusContent(index, '唯物', {
      contentRootId: 'content',
      introNodeId: 'intro',
      examNodeId: 'exam',
    })

    expect(contentResult.totalMatches).toBe(1)
    expect(contentResult.matchedNodeIds).toEqual(['point'])
    expect(contentResult.expandedNodeIds).toContain('chapter')
    expect(contentResult.matchedSectionIds).toEqual(['chapter'])
    expect(contentResult.firstMatchSectionId).toBe('chapter')

    const introResult = searchStudentSyllabusContent(index, '考试目标', {
      contentRootId: 'content',
      introNodeId: 'intro',
      examNodeId: 'exam',
    })

    expect(introResult.matchedNodeIds).toEqual(['intro-child'])
    expect(introResult.matchedSectionIds).toEqual(['intro'])
  })

  it('returns boundary-safe empty result when search keyword is blank', () => {
    const result = searchStudentSyllabusContent(
      {
        allNodes: [{ id: 'chapter', label: '马克思主义基本原理', level: 3 }],
        nodesById: new Map([['chapter', { id: 'chapter', label: '马克思主义基本原理', level: 3 }]]),
        parentByChild: new Map(),
      },
      '   ',
      { contentRootId: 'content' },
    )

    expect(result.totalMatches).toBe(0)
    expect(result.matchedNodeIds).toEqual([])
    expect(result.firstMatchNodeId).toBe('')
  })
})
