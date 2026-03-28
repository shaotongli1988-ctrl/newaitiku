import { describe, expect, it } from 'vitest'
import {
  normalizeAutocompleteItems,
  resolveAutocompleteItemLabel,
  runAutocompleteFetcher,
} from './autocompleteShared'

describe('autocompleteShared', () => {
  it('normalizes suggestion arrays into safe lists', () => {
    expect(normalizeAutocompleteItems([{ value: '政治' }, null])).toEqual([{ value: '政治' }])
  })

  it('covers 异常路径 when fetcher or item input is invalid', async () => {
    expect(resolveAutocompleteItemLabel(null, 'pathLabel')).toBe('')
    await expect(runAutocompleteFetcher(undefined, 'abc')).resolves.toEqual([])
  })

  it('covers 边界路径 for callback-style suggestion loaders', async () => {
    await expect(runAutocompleteFetcher((_query, callback) => callback([{ pathLabel: '马克思主义', value: '政治' }]), '政')).resolves.toEqual([
      { pathLabel: '马克思主义', value: '政治' },
    ])
  })

  it('prefers the configured value key when building input labels', () => {
    expect(resolveAutocompleteItemLabel({ value: '知识点', pathLabel: '政治 / 马原' }, 'pathLabel')).toBe('政治 / 马原')
  })
})
