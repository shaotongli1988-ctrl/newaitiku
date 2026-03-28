<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  activePath: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['select'])

const navGridStyle = computed(() => ({
  gridTemplateColumns: `repeat(${Math.max(props.items.length, 1)}, minmax(0, 1fr))`,
}))

function handleSelect(path) {
  const normalizedPath = String(path || '').trim()
  if (!normalizedPath) {
    return
  }
  emit('select', normalizedPath)
}
</script>

<template>
  <nav class="student-bottom-nav" :style="navGridStyle" aria-label="学生端底部导航">
    <button
      v-for="item in items"
      :key="item.path"
      type="button"
      :class="['student-bottom-nav__item', { 'student-bottom-nav__item--active': activePath === item.path }]"
      @click="handleSelect(item.path)"
    >
      <el-icon class="student-bottom-nav__icon">
        <component :is="item.icon" />
      </el-icon>
      <span>{{ item.shortLabel || item.navTitle }}</span>
    </button>
  </nav>
</template>

<style scoped>
.student-bottom-nav {
  position: fixed;
  right: 14px;
  bottom: 14px;
  left: 14px;
  z-index: 45;
  display: none;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--qb-border-glass);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--qb-shadow-modal);
  backdrop-filter: blur(18px);
}

.student-bottom-nav__item {
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: 10px 6px;
  border: none;
  border-radius: 18px;
  background: transparent;
  color: var(--qb-text-meta);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.student-bottom-nav__item--active {
  background: rgba(219, 234, 254, 0.92);
  color: var(--qb-text-info-ink);
  transform: translateY(-1px);
}

.student-bottom-nav__icon {
  font-size: 18px;
}

@media (max-width: 900px) {
  .student-bottom-nav {
    display: grid;
  }
}
</style>
