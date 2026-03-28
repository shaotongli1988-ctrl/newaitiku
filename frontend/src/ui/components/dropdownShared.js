export const dropdownContextKey = Symbol('uiDropdownContext')

export function normalizeDropdownTrigger(trigger) {
  return String(trigger || '').trim() === 'hover' ? 'hover' : 'click'
}

export function resolveDropdownCommand(command, fallback = undefined) {
  return command === undefined ? fallback : command
}

export function shouldCloseDropdownOnCommand({ hideOnClick = true, disabled = false } = {}) {
  return Boolean(hideOnClick) && !disabled
}
