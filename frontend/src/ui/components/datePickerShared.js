function pad(value) {
  return `${value}`.padStart(2, '0')
}

function formatLocalDate(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function formatLocalDateTime(date) {
  return `${formatLocalDate(date)}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function resolveDatePickerInputType(type = 'date') {
  return String(type || '').trim() === 'datetime' ? 'datetime-local' : 'date'
}

export function normalizeDatePickerInputValue(value, { type = 'date' } = {}) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return ''
  }

  if (String(type || '').trim() === 'datetime') {
    const directMatch = normalized.match(/^(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2})(?::(\d{2}))?/)
    if (directMatch) {
      const seconds = directMatch[3] || '00'
      return `${directMatch[1]}T${directMatch[2]}:${seconds}`
    }
  } else {
    const directDateMatch = normalized.match(/^(\d{4}-\d{2}-\d{2})/)
    if (directDateMatch) {
      return directDateMatch[1]
    }
  }

  const parsed = new Date(normalized)
  if (Number.isNaN(parsed.getTime())) {
    return ''
  }

  return String(type || '').trim() === 'datetime'
    ? formatLocalDateTime(parsed)
    : formatLocalDate(parsed)
}

export function formatDatePickerOutput(inputValue, { type = 'date', valueFormat = '' } = {}) {
  const normalized = String(inputValue || '').trim()
  if (!normalized) {
    return ''
  }

  if (String(type || '').trim() !== 'datetime') {
    return normalized.slice(0, 10)
  }

  const matched = normalized.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::(\d{2}))?/)
  if (!matched) {
    return ''
  }

  const seconds = matched[3] || '00'
  if (String(valueFormat || '').trim() === 'YYYY-MM-DDTHH:mm:ss') {
    return `${matched[1]}T${matched[2]}:${seconds}`
  }

  return `${matched[1]}T${matched[2]}`
}
