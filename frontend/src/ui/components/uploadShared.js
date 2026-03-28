let uploadUidSeed = 0

function normalizeAcceptToken(token) {
  return String(token || '').trim().toLowerCase()
}

export function buildUploadFile(rawFile, overrides = {}) {
  const fallbackUid = `ui-upload-${Date.now()}-${uploadUidSeed += 1}`
  return {
    uid: overrides.uid ?? fallbackUid,
    name: String(overrides.name ?? rawFile?.name ?? '').trim(),
    size: Number(overrides.size ?? rawFile?.size ?? 0),
    status: String(overrides.status || 'ready'),
    percentage: Number(overrides.percentage ?? 0),
    raw: overrides.raw ?? rawFile ?? null,
    ...overrides,
  }
}

export function normalizeUploadFileList(fileList) {
  if (!Array.isArray(fileList)) {
    return []
  }

  return fileList
    .filter(Boolean)
    .map((item) => buildUploadFile(item?.raw || item, item))
}

export function matchesUploadAccept(rawFile, accept) {
  const tokens = String(accept || '')
    .split(',')
    .map(normalizeAcceptToken)
    .filter(Boolean)

  if (!tokens.length) {
    return true
  }

  const fileName = String(rawFile?.name || '').trim().toLowerCase()
  const mimeType = String(rawFile?.type || '').trim().toLowerCase()

  return tokens.some((token) => {
    if (token.startsWith('.')) {
      return fileName.endsWith(token)
    }

    if (token.endsWith('/*')) {
      const prefix = token.slice(0, -1)
      return mimeType.startsWith(prefix)
    }

    return mimeType === token
  })
}

export function splitUploadFiles(rawFiles, limit, occupiedCount = 0) {
  const files = Array.isArray(rawFiles) ? rawFiles.filter(Boolean) : []
  const numericLimit = Number(limit)
  if (!Number.isFinite(numericLimit) || numericLimit <= 0) {
    return {
      accepted: files,
      exceeded: [],
    }
  }

  const availableCount = Math.max(0, numericLimit - Math.max(0, Number(occupiedCount) || 0))
  return {
    accepted: files.slice(0, availableCount),
    exceeded: files.slice(availableCount),
  }
}
