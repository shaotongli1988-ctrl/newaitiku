<script setup>
import { inject } from 'vue'
import { dropdownContextKey, resolveDropdownCommand } from './dropdownShared'

const props = defineProps({
  command: {
    type: [String, Number, Boolean, Object],
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  divided: {
    type: Boolean,
    default: false,
  },
})

const dropdown = inject(dropdownContextKey, null)

function handleClick() {
  if (props.disabled) {
    return
  }
  dropdown?.emitCommand(resolveDropdownCommand(props.command), props.disabled)
}
</script>

<template>
  <li
    class="el-dropdown-menu__item"
    :class="{
      'is-disabled': disabled,
      'el-dropdown-menu__item--divided': divided,
    }"
    @mousedown.prevent
    @click.stop="handleClick"
  >
    <slot />
  </li>
</template>

<style scoped>
.el-dropdown-menu__item {
  padding: 10px 12px;
  border-radius: 12px;
  color: var(--qb-text-primary);
  font-size: 14px;
  line-height: 1.4;
  cursor: pointer;
  transition: background-color 160ms ease, color 160ms ease;
}

.el-dropdown-menu__item:hover:not(.is-disabled) {
  background: color-mix(in srgb, var(--qb-primary-student) 10%, white 90%);
}

.el-dropdown-menu__item.is-disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.el-dropdown-menu__item--divided {
  border-top: 1px solid var(--qb-border-muted);
  margin-top: 4px;
  padding-top: 14px;
}
</style>
