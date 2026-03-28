import { computed } from 'vue'

export function useModal(props, emit) {
  const visible = computed({
    get() {
      return Boolean(props.modelValue)
    },
    set(value) {
      emit('update:modelValue', Boolean(value))
    },
  })

  function close() {
    visible.value = false
  }

  return {
    visible,
    close,
  }
}
