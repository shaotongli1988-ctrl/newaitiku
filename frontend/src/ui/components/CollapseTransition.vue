<script setup>
import { computed } from 'vue'
import { normalizeCollapseDuration } from './collapseTransitionShared'

const props = defineProps({
  duration: {
    type: [String, Number],
    default: 220,
  },
})

const normalizedDuration = computed(() => normalizeCollapseDuration(props.duration))

function beforeEnter(element) {
  element.style.height = '0px'
  element.style.opacity = '0'
  element.style.overflow = 'hidden'
}

function enter(element, done) {
  const nextHeight = `${element.scrollHeight}px`
  element.style.transition = `height ${normalizedDuration.value}ms ease, opacity ${normalizedDuration.value}ms ease`
  requestAnimationFrame(() => {
    element.style.height = nextHeight
    element.style.opacity = '1'
  })
  window.setTimeout(done, normalizedDuration.value)
}

function afterEnter(element) {
  element.style.height = ''
  element.style.opacity = ''
  element.style.overflow = ''
  element.style.transition = ''
}

function beforeLeave(element) {
  element.style.height = `${element.scrollHeight}px`
  element.style.opacity = '1'
  element.style.overflow = 'hidden'
}

function leave(element, done) {
  element.style.transition = `height ${normalizedDuration.value}ms ease, opacity ${normalizedDuration.value}ms ease`
  requestAnimationFrame(() => {
    element.style.height = '0px'
    element.style.opacity = '0'
  })
  window.setTimeout(done, normalizedDuration.value)
}

function afterLeave(element) {
  element.style.height = ''
  element.style.opacity = ''
  element.style.overflow = ''
  element.style.transition = ''
}
</script>

<template>
  <Transition
    @before-enter="beforeEnter"
    @enter="enter"
    @after-enter="afterEnter"
    @before-leave="beforeLeave"
    @leave="leave"
    @after-leave="afterLeave"
  >
    <slot />
  </Transition>
</template>
