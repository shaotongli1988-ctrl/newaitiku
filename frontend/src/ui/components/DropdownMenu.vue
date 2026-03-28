<template>
  <ul class="ui-dropdown-menu el-dropdown-menu">
    <slot />
  </ul>
</template>

<style scoped>
.ui-dropdown-menu {
  display: grid;
  gap: 4px;
  margin: 0;
  padding: 8px;
  list-style: none;
  border: 1px solid var(--qb-border-muted);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 22px 48px -32px rgba(15, 23, 42, 0.38);
  backdrop-filter: blur(10px);
}
</style>
