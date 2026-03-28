export function normalizeOverlayDirection(direction) {
  const candidate = String(direction || '').trim().toLowerCase()
  if (['rtl', 'ltr', 'ttb', 'btt'].includes(candidate)) {
    return candidate
  }
  return 'rtl'
}

export function normalizeOverlaySize(size, fallback = '42%') {
  if (typeof size === 'number' && Number.isFinite(size)) {
    return `${size}px`
  }

  const candidate = String(size || '').trim()
  return candidate || fallback
}

export function normalizeDialogWidth(width, fallback = '680px') {
  return normalizeOverlaySize(width, fallback)
}

export function resolveDrawerPanelStyle(direction, size) {
  const normalizedDirection = normalizeOverlayDirection(direction)
  const normalizedSize = normalizeOverlaySize(size)

  if (normalizedDirection === 'ttb' || normalizedDirection === 'btt') {
    return {
      '--ui-drawer-width': '100vw',
      '--ui-drawer-height': normalizedSize,
    }
  }

  return {
    '--ui-drawer-width': normalizedSize,
    '--ui-drawer-height': '100vh',
  }
}
