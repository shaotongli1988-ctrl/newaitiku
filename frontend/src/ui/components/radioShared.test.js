import { describe, expect, it } from 'vitest'
import {
  isRadioChecked,
  normalizeRadioSize,
  shouldEmitRadioChange,
} from './radioShared'

describe('radioShared', () => {
  it('matches selected radio labels', () => {
    expect(isRadioChecked('AI_TUTOR', 'AI_TUTOR')).toBe(true)
    expect(isRadioChecked('AI_TUTOR', 'AI_MARKING')).toBe(false)
  })

  it('keeps only supported radio sizes', () => {
    expect(normalizeRadioSize('large')).toBe('large')
    expect(normalizeRadioSize('small')).toBe('small')
    expect(normalizeRadioSize('huge')).toBe('')
  })

  it('emits only when radio value really changes', () => {
    expect(shouldEmitRadioChange('single', 'batch')).toBe(true)
    expect(shouldEmitRadioChange('single', 'single')).toBe(false)
  })
})
