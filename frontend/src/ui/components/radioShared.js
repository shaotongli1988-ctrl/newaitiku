export const radioGroupContextKey = Symbol('uiRadioGroupContext')

export function isRadioChecked(modelValue, label) {
  return modelValue === label
}

export function normalizeRadioSize(size) {
  return ['large', 'default', 'small'].includes(size) ? size : ''
}

export function shouldEmitRadioChange(currentValue, nextValue) {
  return currentValue !== nextValue
}
