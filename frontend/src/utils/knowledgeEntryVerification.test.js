import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import {
  buildKnowledgeGraphIndex,
  buildKnowledgeLevelTreeState,
  buildKnowledgeSelectorState,
} from './knowledgeTree'
import { buildStudentGalaxyModel } from './studentAnalysisGalaxy'

const knowledgeTreeFixturePath = new URL('../../../data/knowledge_tree.json', import.meta.url)
const knowledgeTreeFixture = JSON.parse(readFileSync(knowledgeTreeFixturePath, 'utf8'))
const allNodes = Array.isArray(knowledgeTreeFixture?.nodes) ? knowledgeTreeFixture.nodes : []

function buildSubjectPayload(subjectCode) {
  const nodes = allNodes.filter((item) => String(item?.subject_code || '').trim() === subjectCode)
  const nodeIds = new Set(nodes.map((item) => String(item?.id || '').trim()).filter(Boolean))
  const normalizedNodes = nodes.map((item) => ({
    id: String(item?.id || '').trim(),
    label: String(item?.name || item?.label || item?.id || '').trim(),
    parentId: String(item?.parent_id || '').trim(),
    level: Number(item?.level || 0),
    sort: Number(item?.sort || 0),
    mastery: Number(item?.mastery || 0),
    questionCount: Number(item?.question_count || item?.questionCount || 0),
  }))
  const links = normalizedNodes
    .filter((item) => item.parentId && nodeIds.has(item.parentId))
    .map((item) => ({ source: item.parentId, target: item.id, type: 'parent' }))
  return {
    nodes: normalizedNodes,
    links,
  }
}

function buildPracticeLikeSnapshot(subjectCode) {
  const selectorState = buildKnowledgeSelectorState(buildSubjectPayload(subjectCode))
  const levelTreeState = buildKnowledgeLevelTreeState(selectorState, { startLevel: 3, endLevel: 5 })
  return {
    l3Options: Array.isArray(levelTreeState?.options) ? levelTreeState.options.length : 0,
    chapterCodes: Object.keys(selectorState?.chapterCodeMap || {}).length,
    pointCodes: Object.keys(selectorState?.pointCodeMap || {}).length,
    searchOptions: Array.isArray(selectorState?.searchOptions) ? selectorState.searchOptions.length : 0,
    selectorState,
  }
}

function buildAnalysisLikeSnapshot(selectorState) {
  const galaxyModel = buildStudentGalaxyModel(selectorState)
  return {
    chapterCount: Number(galaxyModel?.chapterCount || 0),
    pointCount: Number(galaxyModel?.pointCount || 0),
  }
}

function buildHomeTasksLikeSnapshot(subjectCode) {
  const graphIndex = buildKnowledgeGraphIndex(buildSubjectPayload(subjectCode))
  const l5Count = Object.entries(graphIndex?.levelById || {}).filter(([, level]) => Number(level || 0) >= 5).length
  return {
    l5Count,
  }
}

describe('knowledge entry verification', () => {
  const subjectCodes = [
    'POLITICS',
    'ENGLISH',
    'INFO_TECH_INTRO',
    'ADVANCED_MATH_1',
    'ART_INTRODUCTION',
    'JURISPRUDENCE',
  ]

  it.each(subjectCodes)('keeps student and teacher entry contracts aligned for %s', (subjectCode) => {
    const practiceLike = buildPracticeLikeSnapshot(subjectCode)
    const analysisLike = buildAnalysisLikeSnapshot(practiceLike.selectorState)
    const homeTasksLike = buildHomeTasksLikeSnapshot(subjectCode)

    expect(practiceLike.l3Options).toBeGreaterThan(0)
    expect(practiceLike.chapterCodes).toBeGreaterThan(0)
    expect(practiceLike.pointCodes).toBeGreaterThan(0)
    expect(practiceLike.searchOptions).toBeGreaterThan(0)
    expect(analysisLike.chapterCount).toBeGreaterThan(0)
    expect(analysisLike.pointCount).toBeGreaterThan(0)
    expect(homeTasksLike.l5Count).toBeGreaterThan(0)
  })
})
