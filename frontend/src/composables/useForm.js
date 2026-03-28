import { reactive } from 'vue'

export function useForm(createInitialState) {
  const form = reactive(createInitialState())

  function resetForm() {
    Object.assign(form, createInitialState())
  }

  function patchForm(nextState = {}) {
    Object.assign(form, nextState || {})
  }

  return {
    form,
    resetForm,
    patchForm,
  }
}
