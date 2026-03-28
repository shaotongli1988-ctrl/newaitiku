export function resolveSwitchChecked(modelValue, activeValue = true) {
  return modelValue === activeValue
}

export function resolveSwitchNextValue(checked, activeValue = true, inactiveValue = false) {
  return checked ? activeValue : inactiveValue
}

export function resolveSwitchPrompt(checked, activeText = '', inactiveText = '') {
  return checked ? activeText : inactiveText
}
