import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { fileURLToPath, URL } from 'node:url'

function createLocalUiComponentResolver() {
  const componentMap = {
    ElAlert: './src/ui/components/Alert.vue',
    ElBadge: './src/ui/components/Badge.vue',
    ElButton: './src/ui/components/Button.vue',
    ElBreadcrumb: './src/ui/components/Breadcrumb.vue',
    ElBreadcrumbItem: './src/ui/components/BreadcrumbItem.vue',
    ElCard: './src/ui/components/Card.vue',
    ElCascader: './src/ui/components/Cascader.vue',
    ElCheckbox: './src/ui/components/Checkbox.vue',
    ElCol: './src/ui/components/Col.vue',
    ElCollapseTransition: './src/ui/components/CollapseTransition.vue',
    ElCollapse: './src/ui/components/Collapse.vue',
    ElCollapseItem: './src/ui/components/CollapseItem.vue',
    ElAutocomplete: './src/ui/components/Autocomplete.vue',
    ElDatePicker: './src/ui/components/DatePicker.vue',
    ElDescriptions: './src/ui/components/Descriptions.vue',
    ElDescriptionsItem: './src/ui/components/DescriptionsItem.vue',
    ElDialog: './src/ui/components/Dialog.vue',
    ElDivider: './src/ui/components/Divider.vue',
    ElDropdown: './src/ui/components/Dropdown.vue',
    ElDropdownItem: './src/ui/components/DropdownItem.vue',
    ElDropdownMenu: './src/ui/components/DropdownMenu.vue',
    ElDrawer: './src/ui/components/Drawer.vue',
    ElEmpty: './src/ui/components/EmptyState.vue',
    ElForm: './src/ui/components/Form.vue',
    ElFormItem: './src/ui/components/FormItem.vue',
    ElIcon: './src/ui/components/Icon.vue',
    ElInput: './src/ui/components/Input.vue',
    ElInputNumber: './src/ui/components/InputNumber.vue',
    ElPagination: './src/ui/components/Pagination.vue',
    ElProgress: './src/ui/components/Progress.vue',
    ElRadio: './src/ui/components/Radio.vue',
    ElRadioButton: './src/ui/components/RadioButton.vue',
    ElRadioGroup: './src/ui/components/RadioGroup.vue',
    ElResult: './src/ui/components/ResultState.vue',
    ElRow: './src/ui/components/Row.vue',
    ElOption: './src/ui/components/Option.vue',
    ElSelect: './src/ui/components/Select.vue',
    ElSkeleton: './src/ui/components/Skeleton.vue',
    ElSkeletonItem: './src/ui/components/SkeletonItem.vue',
    ElSlider: './src/ui/components/Slider.vue',
    ElSpace: './src/ui/components/Space.vue',
    ElSwitch: './src/ui/components/Switch.vue',
    ElTabPane: './src/ui/components/TabPane.vue',
    ElTag: './src/ui/components/Tag.vue',
    ElTable: './src/ui/components/Table.vue',
    ElTableColumn: './src/ui/components/TableColumn.vue',
    ElTabs: './src/ui/components/Tabs.vue',
    ElTreeSelect: './src/ui/components/TreeSelect.vue',
    ElTreeV2: './src/ui/components/TreeV2.vue',
    ElUpload: './src/ui/components/Upload.vue',
  }

  return (componentName) => {
    const componentPath = componentMap[componentName]
    if (!componentPath) {
      return undefined
    }

    const browserImportPath = componentPath.startsWith('./')
      ? `/${componentPath.slice(2)}`
      : componentPath

    return {
      name: 'default',
      from: browserImportPath,
    }
  }
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
  },
  plugins: [
    vue(),
    Components({
      dirs: [],
      dts: false,
      resolvers: [
        createLocalUiComponentResolver(),
      ],
    }),
  ],
  resolve: {
    alias: [
      {
        find: '@',
        replacement: fileURLToPath(new URL('./src', import.meta.url)),
      },
    ],
  },
  test: {
    include: ['src/**/*.test.js', 'src/**/*.test.ts'],
    exclude: ['tests/**', 'dist/**', 'node_modules/**'],
  },
  ...(mode === 'test'
    ? {}
    : {
        esbuild: {
          drop: ['console', 'debugger'],
          legalComments: 'none',
        },
      }),
  build: {
    modulePreload: {
      resolveDependencies(_filename, deps, context) {
        if (String(context?.hostType || '') !== 'html') {
          return deps
        }
        return deps.filter((dep) => !String(dep || '').includes('route-'))
      },
    },
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = String(id || '').replace(/\\/g, '/')
          if (normalizedId.includes('/src/utils/echarts/studentRuntime.js')) {
            return 'vendor-echarts-student'
          }
          if (normalizedId.includes('/src/utils/echarts/teacherRuntime.js')) {
            return 'vendor-echarts-teacher'
          }
          if (normalizedId.includes('/src/api/request.js')) {
            return 'shared-request-runtime'
          }
          if (
            normalizedId.includes('/src/api/auth.js') ||
            normalizedId.includes('/src/stores/userStore.js')
          ) {
            return 'shared-user-session'
          }
          if (
            normalizedId.includes('/src/api/services/questionBank.js') ||
            normalizedId.includes('/src/api/services/_shared.js')
          ) {
            return 'shared-questionbank-api'
          }
          if (
            normalizedId.includes('/src/api/services/student.js') ||
            normalizedId.includes('/src/stores/subjectContextStore.js')
          ) {
            return 'shared-student-data'
          }
          if (
            normalizedId.includes('/src/api/admin.js') ||
            normalizedId.includes('/src/api/subjects.js') ||
            normalizedId.includes('/src/api/services/examCategory.js') ||
            normalizedId.includes('/src/api/services/papers.js') ||
            normalizedId.includes('/src/api/services/questions.js')
          ) {
            return 'shared-management-api'
          }
          if (
            normalizedId.includes('/src/api/') ||
            normalizedId.includes('/src/stores/')
          ) {
            return 'shared-app-data'
          }
          if (
            normalizedId.includes('/src/utils/knowledgeTree.js') ||
            normalizedId.includes('/src/utils/knowledgeGraphTeacher.js')
          ) {
            return 'shared-knowledge'
          }
          if (
            normalizedId.includes('/src/utils/contentBaseline.js') ||
            normalizedId.includes('/src/utils/question.js')
          ) {
            return 'shared-question-utils'
          }
          if (!normalizedId.includes('/node_modules/')) {
            return undefined
          }

          if (
            normalizedId.includes('/node_modules/vue/') ||
            normalizedId.includes('/node_modules/@vue/') ||
            normalizedId.includes('/node_modules/vue-router/') ||
            normalizedId.includes('/node_modules/pinia/')
          ) {
            return 'vendor-vue'
          }

          if (
            normalizedId.includes('/node_modules/axios/') ||
            normalizedId.includes('/node_modules/nprogress/')
          ) {
            return 'vendor-request'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/chart/graph/') ||
            normalizedId.includes('/node_modules/echarts/lib/chart/sunburst/')
          ) {
            return 'vendor-echarts-student'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/chart/bar/') ||
            normalizedId.includes('/node_modules/echarts/lib/chart/pie/') ||
            normalizedId.includes('/node_modules/echarts/lib/chart/scatter/')
          ) {
            return 'vendor-echarts-teacher'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/chart/radar/') ||
            normalizedId.includes('/node_modules/echarts/charts.js')
          ) {
            return 'vendor-echarts-radar'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/component/graphic/') ||
            normalizedId.includes('/node_modules/echarts/lib/component/title/')
          ) {
            return 'vendor-echarts-components-graphic'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/component/radar/')
          ) {
            return 'vendor-echarts-components-radar'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/component/grid/') ||
            normalizedId.includes('/node_modules/echarts/lib/component/legend/')
          ) {
            return 'vendor-echarts-components-layout'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/component/tooltip/')
          ) {
            return 'vendor-echarts-components-tooltip'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/component/') ||
            normalizedId.includes('/node_modules/echarts/components.js')
          ) {
            return 'vendor-echarts-components-misc'
          }

          if (
            normalizedId.includes('/node_modules/echarts/lib/core/') ||
            normalizedId.includes('/node_modules/echarts/core.js') ||
            normalizedId.includes('/node_modules/echarts/lib/renderer/') ||
            normalizedId.includes('/node_modules/echarts/renderers.js')
          ) {
            return 'vendor-echarts-runtime'
          }

          if (normalizedId.includes('/node_modules/zrender/')) {
            return 'vendor-zrender'
          }

          if (
            normalizedId.includes('/node_modules/echarts/')
          ) {
            return 'vendor-echarts-core'
          }

          if (normalizedId.includes('/node_modules/@vue-flow/')) {
            return 'vendor-flow'
          }

          return 'vendor-misc'
        },
      },
    },
  },
}))
