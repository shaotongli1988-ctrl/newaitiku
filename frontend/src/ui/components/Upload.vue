<script setup>
import { computed, ref, useAttrs } from 'vue'
import {
  buildUploadFile,
  matchesUploadAccept,
  normalizeUploadFileList,
  splitUploadFiles,
} from './uploadShared'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps({
  accept: {
    type: String,
    default: '',
  },
  action: {
    type: String,
    default: '',
  },
  autoUpload: {
    type: Boolean,
    default: true,
  },
  beforeUpload: {
    type: Function,
    default: undefined,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  drag: {
    type: Boolean,
    default: false,
  },
  fileList: {
    type: Array,
    default: undefined,
  },
  limit: {
    type: [String, Number],
    default: undefined,
  },
  multiple: {
    type: Boolean,
    default: false,
  },
  onChange: {
    type: Function,
    default: undefined,
  },
  onExceed: {
    type: Function,
    default: undefined,
  },
  onRemove: {
    type: Function,
    default: undefined,
  },
  showFileList: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['change', 'exceed', 'remove'])

const attrs = useAttrs()
const inputRef = ref(null)
const dragActive = ref(false)
const internalFiles = ref([])

const rootAttrs = computed(() => ({
  class: attrs.class,
  style: attrs.style,
}))

const currentFiles = computed(() => (
  Array.isArray(props.fileList)
    ? normalizeUploadFileList(props.fileList)
    : internalFiles.value
))

const uploadClasses = computed(() => [
  'ui-upload',
  'el-upload',
  props.drag ? 'el-upload--text' : '',
  props.disabled ? 'is-disabled' : '',
])

const draggerClasses = computed(() => [
  'ui-upload__trigger',
  props.drag ? 'el-upload-dragger' : 'ui-upload__trigger--inline',
  dragActive.value ? 'is-dragover' : '',
])

function resetNativeInput() {
  if (inputRef.value) {
    inputRef.value.value = ''
  }
}

async function allowFile(rawFile) {
  if (!rawFile || !matchesUploadAccept(rawFile, props.accept)) {
    return false
  }

  if (typeof props.beforeUpload !== 'function') {
    return true
  }

  const result = await props.beforeUpload(rawFile)
  return result !== false
}

async function processFiles(rawFiles) {
  if (props.disabled) {
    return
  }

  const candidates = Array.isArray(rawFiles) ? rawFiles.filter(Boolean) : []
  const allowedFiles = []
  for (const rawFile of candidates) {
    if (await allowFile(rawFile)) {
      allowedFiles.push(rawFile)
    }
  }

  const { accepted, exceeded } = splitUploadFiles(
    allowedFiles,
    props.limit,
    currentFiles.value.length,
  )

  if (exceeded.length) {
    props.onExceed?.(exceeded, currentFiles.value)
    emit('exceed', exceeded, currentFiles.value)
  }

  if (!accepted.length) {
    resetNativeInput()
    return
  }

  const normalizedAccepted = accepted.map((rawFile) => buildUploadFile(rawFile))
  const nextFileList = [...currentFiles.value, ...normalizedAccepted]

  if (!Array.isArray(props.fileList)) {
    internalFiles.value = nextFileList
  }

  normalizedAccepted.forEach((uploadFile) => {
    props.onChange?.(uploadFile, nextFileList)
    emit('change', uploadFile, nextFileList)
  })

  resetNativeInput()
}

function openPicker() {
  if (props.disabled) {
    return
  }
  inputRef.value?.click()
}

function handleNativeChange(event) {
  const nextFiles = Array.from(event?.target?.files || [])
  processFiles(nextFiles)
}

function handleRemove(file, event) {
  event?.stopPropagation?.()
  const nextFileList = currentFiles.value.filter((item) => item.uid !== file.uid)
  if (!Array.isArray(props.fileList)) {
    internalFiles.value = nextFileList
  }
  props.onRemove?.(file, nextFileList)
  emit('remove', file, nextFileList)
}

function handleDragOver(event) {
  if (!props.drag || props.disabled) {
    return
  }
  event.preventDefault()
  dragActive.value = true
}

function handleDragLeave() {
  dragActive.value = false
}

function handleDrop(event) {
  if (!props.drag || props.disabled) {
    return
  }

  event.preventDefault()
  dragActive.value = false
  processFiles(Array.from(event.dataTransfer?.files || []))
}
</script>

<template>
  <div v-bind="rootAttrs" :class="uploadClasses">
    <div
      :class="draggerClasses"
      role="button"
      tabindex="0"
      @click="openPicker"
      @keydown.enter.prevent="openPicker"
      @keydown.space.prevent="openPicker"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <input
        ref="inputRef"
        class="ui-upload__native-input"
        type="file"
        :accept="accept || undefined"
        :multiple="multiple"
        :disabled="disabled"
        @change="handleNativeChange"
      >
      <slot />
    </div>

    <slot name="tip" />

    <ul v-if="showFileList && currentFiles.length" class="el-upload-list el-upload-list--text">
      <li
        v-for="file in currentFiles"
        :key="file.uid"
        class="el-upload-list__item"
      >
        <span class="el-upload-list__item-name">{{ file.name }}</span>
        <button
          type="button"
          class="el-upload-list__item-delete"
          aria-label="移除文件"
          @click="handleRemove(file, $event)"
        >
          删除
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.ui-upload {
  display: grid;
  gap: 12px;
  width: 100%;
}

.ui-upload.is-disabled {
  opacity: 0.68;
}

.ui-upload__trigger {
  position: relative;
  width: 100%;
  cursor: pointer;
}

.ui-upload__trigger--inline {
  display: inline-flex;
}

.el-upload-dragger {
  display: grid;
  place-items: center;
  gap: 12px;
  min-height: 180px;
  padding: 24px;
  border: 1px dashed var(--qb-border-muted);
  border-radius: 20px;
  background:
    radial-gradient(circle at top, rgba(37, 99, 235, 0.08), transparent 58%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 250, 255, 0.96));
  text-align: center;
  transition:
    border-color 180ms ease,
    transform 180ms ease,
    box-shadow 180ms ease;
}

.el-upload-dragger:hover,
.el-upload-dragger.is-dragover {
  border-color: var(--qb-primary-student);
  box-shadow: 0 18px 40px -28px color-mix(in srgb, var(--qb-primary-student) 42%, transparent 58%);
  transform: translateY(-1px);
}

.ui-upload__native-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
}

.el-upload-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.el-upload-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border: 1px solid var(--qb-border-muted);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
}

.el-upload-list__item-name {
  min-width: 0;
  color: var(--qb-text-primary);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.el-upload-list__item-delete {
  border: 0;
  background: transparent;
  color: var(--qb-danger);
  font-size: 13px;
  cursor: pointer;
}
</style>
