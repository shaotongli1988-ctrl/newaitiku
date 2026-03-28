<template>
  <span class="ui-icon el-icon" aria-hidden="true">
    <slot />
  </span>
</template>

<style scoped>
.ui-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1em;
  height: 1em;
  line-height: 1;
  vertical-align: middle;
}

.ui-icon :deep(svg) {
  width: 1em;
  height: 1em;
  fill: currentColor;
}
</style>
