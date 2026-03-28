export function normalizeButtonType(type) {
  const candidate = String(type || '').trim()
  if (['primary', 'success', 'warning', 'danger', 'info'].includes(candidate)) {
    return candidate
  }
  return ''
}

export function normalizeButtonSize(size) {
  const candidate = String(size || '').trim()
  if (['large', 'default', 'small'].includes(candidate)) {
    return candidate
  }
  return 'default'
}

export function resolveButtonVariant({ plain = false, link = false, text = false } = {}) {
  if (link) {
    return 'link'
  }
  if (text) {
    return 'text'
  }
  if (plain) {
    return 'plain'
  }
  return 'solid'
}

const paletteMap = {
  default: {
    solid: {
      bg: 'var(--qb-surface-strong)',
      border: 'color-mix(in srgb, var(--qb-border-muted) 84%, white 16%)',
      text: 'var(--qb-text-primary)',
      hoverBg: 'color-mix(in srgb, var(--qb-surface-strong) 84%, white 16%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-border-muted) 64%, white 36%)',
      hoverText: 'var(--qb-text-primary)',
    },
    plain: {
      bg: 'transparent',
      border: 'color-mix(in srgb, var(--qb-border-muted) 84%, white 16%)',
      text: 'var(--qb-text-primary)',
      hoverBg: 'color-mix(in srgb, var(--qb-primary-soft-bg) 56%, white 44%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-primary-student) 32%, white 68%)',
      hoverText: 'var(--qb-primary-student)',
    },
    text: {
      bg: 'transparent',
      border: 'transparent',
      text: 'var(--qb-text-secondary-strong)',
      hoverBg: 'color-mix(in srgb, var(--qb-primary-soft-bg) 58%, white 42%)',
      hoverBorder: 'transparent',
      hoverText: 'var(--qb-primary-student)',
    },
    link: {
      bg: 'transparent',
      border: 'transparent',
      text: 'var(--qb-text-secondary-strong)',
      hoverBg: 'transparent',
      hoverBorder: 'transparent',
      hoverText: 'var(--qb-primary-student)',
    },
  },
  primary: {
    solid: {
      bg: 'var(--qb-primary-student)',
      border: 'var(--qb-primary-student)',
      text: 'var(--qb-text-inverse)',
      hoverBg: 'color-mix(in srgb, var(--qb-primary-student) 88%, black 12%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-primary-student) 88%, black 12%)',
      hoverText: 'var(--qb-text-inverse)',
    },
    plain: {
      bg: 'var(--qb-primary-soft-bg)',
      border: 'var(--qb-primary-soft-border)',
      text: 'var(--qb-primary-student)',
      hoverBg: 'color-mix(in srgb, var(--qb-primary-soft-bg) 72%, white 28%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-primary-student) 40%, white 60%)',
      hoverText: 'color-mix(in srgb, var(--qb-primary-student) 88%, black 12%)',
    },
    text: {
      bg: 'transparent',
      border: 'transparent',
      text: 'var(--qb-primary-student)',
      hoverBg: 'color-mix(in srgb, var(--qb-primary-soft-bg) 60%, white 40%)',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-primary-student) 88%, black 12%)',
    },
    link: {
      bg: 'transparent',
      border: 'transparent',
      text: 'var(--qb-primary-student)',
      hoverBg: 'transparent',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-primary-student) 88%, black 12%)',
    },
  },
  success: {
    solid: {
      bg: 'var(--qb-success)',
      border: 'var(--qb-success)',
      text: 'var(--qb-text-inverse)',
      hoverBg: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
      hoverText: 'var(--qb-text-inverse)',
    },
    plain: {
      bg: 'color-mix(in srgb, var(--qb-success) 12%, white 88%)',
      border: 'color-mix(in srgb, var(--qb-success) 28%, white 72%)',
      text: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
      hoverBg: 'color-mix(in srgb, var(--qb-success) 16%, white 84%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-success) 40%, white 60%)',
      hoverText: 'color-mix(in srgb, var(--qb-success) 90%, black 10%)',
    },
    text: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
      hoverBg: 'color-mix(in srgb, var(--qb-success) 12%, white 88%)',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-success) 90%, black 10%)',
    },
    link: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-success) 88%, black 12%)',
      hoverBg: 'transparent',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-success) 90%, black 10%)',
    },
  },
  warning: {
    solid: {
      bg: 'var(--qb-warning)',
      border: 'var(--qb-warning)',
      text: 'var(--qb-text-inverse)',
      hoverBg: 'color-mix(in srgb, var(--qb-warning) 88%, black 12%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-warning) 88%, black 12%)',
      hoverText: 'var(--qb-text-inverse)',
    },
    plain: {
      bg: 'color-mix(in srgb, var(--qb-warning) 14%, white 86%)',
      border: 'color-mix(in srgb, var(--qb-warning) 32%, white 68%)',
      text: 'color-mix(in srgb, var(--qb-warning) 86%, black 14%)',
      hoverBg: 'color-mix(in srgb, var(--qb-warning) 18%, white 82%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-warning) 44%, white 56%)',
      hoverText: 'color-mix(in srgb, var(--qb-warning) 90%, black 10%)',
    },
    text: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-warning) 86%, black 14%)',
      hoverBg: 'color-mix(in srgb, var(--qb-warning) 12%, white 88%)',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-warning) 90%, black 10%)',
    },
    link: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-warning) 86%, black 14%)',
      hoverBg: 'transparent',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-warning) 90%, black 10%)',
    },
  },
  danger: {
    solid: {
      bg: 'var(--qb-danger)',
      border: 'var(--qb-danger)',
      text: 'var(--qb-text-inverse)',
      hoverBg: 'color-mix(in srgb, var(--qb-danger) 88%, black 12%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-danger) 88%, black 12%)',
      hoverText: 'var(--qb-text-inverse)',
    },
    plain: {
      bg: 'color-mix(in srgb, var(--qb-danger) 12%, white 88%)',
      border: 'color-mix(in srgb, var(--qb-danger) 28%, white 72%)',
      text: 'color-mix(in srgb, var(--qb-danger) 88%, black 12%)',
      hoverBg: 'color-mix(in srgb, var(--qb-danger) 16%, white 84%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-danger) 40%, white 60%)',
      hoverText: 'color-mix(in srgb, var(--qb-danger) 90%, black 10%)',
    },
    text: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-danger) 88%, black 12%)',
      hoverBg: 'color-mix(in srgb, var(--qb-danger) 12%, white 88%)',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-danger) 90%, black 10%)',
    },
    link: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-danger) 88%, black 12%)',
      hoverBg: 'transparent',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-danger) 90%, black 10%)',
    },
  },
  info: {
    solid: {
      bg: 'var(--qb-info)',
      border: 'var(--qb-info)',
      text: 'var(--qb-text-inverse)',
      hoverBg: 'color-mix(in srgb, var(--qb-info) 88%, black 12%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-info) 88%, black 12%)',
      hoverText: 'var(--qb-text-inverse)',
    },
    plain: {
      bg: 'color-mix(in srgb, var(--qb-info) 12%, white 88%)',
      border: 'color-mix(in srgb, var(--qb-info) 28%, white 72%)',
      text: 'color-mix(in srgb, var(--qb-info) 86%, black 14%)',
      hoverBg: 'color-mix(in srgb, var(--qb-info) 16%, white 84%)',
      hoverBorder: 'color-mix(in srgb, var(--qb-info) 40%, white 60%)',
      hoverText: 'color-mix(in srgb, var(--qb-info) 88%, black 12%)',
    },
    text: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-info) 86%, black 14%)',
      hoverBg: 'color-mix(in srgb, var(--qb-info) 12%, white 88%)',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-info) 88%, black 12%)',
    },
    link: {
      bg: 'transparent',
      border: 'transparent',
      text: 'color-mix(in srgb, var(--qb-info) 86%, black 14%)',
      hoverBg: 'transparent',
      hoverBorder: 'transparent',
      hoverText: 'color-mix(in srgb, var(--qb-info) 88%, black 12%)',
    },
  },
}

export function resolveButtonPalette(type = '', variant = 'solid') {
  const typeKey = type || 'default'
  const resolvedVariant = ['solid', 'plain', 'text', 'link'].includes(variant) ? variant : 'solid'
  return paletteMap[typeKey]?.[resolvedVariant] || paletteMap.default.solid
}
