<script setup>
import { getCurrentInstance, inject, onBeforeUnmount, watchEffect, useSlots } from 'vue'
import { tableContextKey } from './tableShared'

const props = defineProps({
  type: {
    type: String,
    default: '',
  },
  prop: {
    type: String,
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  width: {
    type: [String, Number],
    default: undefined,
  },
  minWidth: {
    type: [String, Number],
    default: undefined,
  },
  fixed: {
    type: [Boolean, String],
    default: undefined,
  },
  reserveSelection: {
    type: Boolean,
    default: false,
  },
  showOverflowTooltip: {
    type: Boolean,
    default: false,
  },
})

const slots = useSlots()
const tableContext = inject(tableContextKey, null)
const instance = getCurrentInstance()
const uid = `ui-table-column-${instance?.uid || Math.random().toString(36).slice(2)}`

watchEffect(() => {
  if (!tableContext?.registerColumn) {
    return
  }

  tableContext.registerColumn({
    uid,
    type: props.type,
    prop: props.prop,
    label: props.label,
    width: props.width,
    minWidth: props.minWidth,
    fixed: props.fixed,
    reserveSelection: props.reserveSelection,
    showOverflowTooltip: props.showOverflowTooltip,
    render: slots.default,
  })
})

onBeforeUnmount(() => {
  tableContext?.unregisterColumn?.(uid)
})
</script>

<template />
