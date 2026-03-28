import { describe, expect, it } from 'vitest'
import {
  getValueByPath,
  normalizeFormRules,
  validateFormField,
} from './formShared'

describe('formShared', () => {
  it('reads nested model values by prop path', () => {
    expect(getValueByPath({ user: { name: 'Alice' } }, 'user.name')).toBe('Alice')
  })

  it('covers 异常路径 when rules are missing', async () => {
    expect(normalizeFormRules(null, 'title')).toEqual([])
    await expect(validateFormField({ model: {}, prop: 'title', rules: null })).resolves.toEqual({
      valid: true,
      message: '',
    })
  })

  it('covers 边界路径 for required and custom validator rules', async () => {
    const requiredResult = await validateFormField({
      model: { title: '' },
      prop: 'title',
      rules: {
        title: [{ required: true, message: '请输入标题' }],
      },
    })

    expect(requiredResult).toEqual({
      valid: false,
      message: '请输入标题',
    })

    const customResult = await validateFormField({
      model: { scopePath: ['A', 'B'] },
      prop: 'scopePath',
      rules: {
        scopePath: [
          {
            validator: (_rule, value, callback) => {
              if (Array.isArray(value) && value.length === 3) {
                callback()
                return
              }
              callback(new Error('请选择完整路径'))
            },
          },
        ],
      },
    })

    expect(customResult).toEqual({
      valid: false,
      message: '请选择完整路径',
    })
  })
})
