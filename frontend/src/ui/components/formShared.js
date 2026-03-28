export const formContextKey = Symbol('uiFormContext')

export function getValueByPath(source, path) {
  const normalizedPath = Array.isArray(path)
    ? path
    : String(path || '')
        .split('.')
        .map((segment) => segment.trim())
        .filter(Boolean)

  return normalizedPath.reduce((current, segment) => {
    if (current == null) {
      return undefined
    }
    return current[segment]
  }, source)
}

export function normalizeFormRules(rules, prop) {
  if (!prop || !rules || typeof rules !== 'object') {
    return []
  }
  const matchedRules = rules[prop]
  return Array.isArray(matchedRules) ? matchedRules : []
}

export async function runSingleRule(rule, value, model) {
  if (!rule || typeof rule !== 'object') {
    return ''
  }

  if (rule.required) {
    const isEmptyArray = Array.isArray(value) && value.length === 0
    const isEmptyValue = value === undefined || value === null || value === ''
    if (isEmptyArray || isEmptyValue) {
      return String(rule.message || '请完善当前字段')
    }
  }

  if (typeof rule.validator === 'function') {
    const maybeMessage = await new Promise((resolve) => {
      let settled = false
      const callback = (error) => {
        if (settled) {
          return
        }
        settled = true
        if (error instanceof Error) {
          resolve(error.message || '校验未通过')
          return
        }
        if (typeof error === 'string') {
          resolve(error)
          return
        }
        resolve('')
      }

      try {
        const result = rule.validator(rule, value, callback, model)
        if (result && typeof result.then === 'function') {
          result
            .then(() => callback())
            .catch((error) => callback(error))
        } else if (rule.validator.length < 3) {
          callback(result instanceof Error ? result : '')
        }
      } catch (error) {
        callback(error)
      }
    })

    return String(maybeMessage || '')
  }

  return ''
}

export async function validateFormField({ model, prop, rules }) {
  const value = getValueByPath(model, prop)
  const normalizedRules = normalizeFormRules(rules, prop)

  for (const rule of normalizedRules) {
    const errorMessage = await runSingleRule(rule, value, model)
    if (errorMessage) {
      return {
        valid: false,
        message: errorMessage,
      }
    }
  }

  return {
    valid: true,
    message: '',
  }
}
