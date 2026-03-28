import { describe, expect, it } from 'vitest'
import {
  buildKnowledgeBreadcrumbText,
  buildKnowledgePathItems,
  buildSelectedKnowledgeBreadcrumb,
} from './layoutBreadcrumb.js'

describe('layoutBreadcrumb', () => {
  it('正常路径: 从 pathLabel 中提取 L4/L5 breadcrumb', () => {
    expect(buildSelectedKnowledgeBreadcrumb({
      pathLabel: '高等数学 / 函数极限 / 极限的定义',
    })).toEqual([
      { level: 'L4', label: '函数极限' },
      { level: 'L5', label: '极限的定义' },
    ])
  })

  it('异常路径: 没有路径时回退到默认提示', () => {
    expect(buildKnowledgeBreadcrumbText({})).toBe('当前未选择 L4 / L5 路径')
  })

  it('边界路径: 仅有 chapterName 和 pointName 时也能生成 L4/L5', () => {
    expect(buildKnowledgePathItems({
      chapterName: '马克思主义哲学',
      pointName: '世界的物质统一性',
    }).slice(1)).toEqual([
      { level: 'L4', label: '马克思主义哲学' },
      { level: 'L5', label: '世界的物质统一性' },
    ])
  })

  it('前端联动: breadcrumb 文本只保留当前 L4/L5 路径', () => {
    expect(buildKnowledgeBreadcrumbText({
      pathLabel: '政治 / 唯物论 / 世界的物质统一性',
    })).toBe('唯物论 > 世界的物质统一性')
  })
})
