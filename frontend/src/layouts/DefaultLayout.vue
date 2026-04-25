<script setup>
import { ArrowDown, Bell, Collection, DataAnalysis, EditPen, House } from '@/ui/icons'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StudentBottomNav from '../components/student/StudentBottomNav.vue'
import { fetchMessageUnreadSummary } from '../api/services/questionBank.js'
import { useUserStore } from '../stores/userStore.js'
import { useSubjectContextStore } from '../stores/subjectContextStore.js'
import { isRoutePathAllowedInEntry } from '../utils/navigationScope.js'
import { uiFeedbackState } from '../utils/uiFeedbackState.js'
import { buildSelectedKnowledgeBreadcrumb } from '../utils/layoutBreadcrumb.js'
import { buildContentLabelMaps, resolveContentLabel } from '../utils/contentBaseline.js'
import {
  buildStudentRouteLocationForSubject,
  resolveStudentSubjectCode,
  shouldSyncStudentSubjectRoute,
} from '../utils/studentSubjectContext.js'
import { buildStudentSubjectScope } from '../utils/studentSubjectScope.js'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const subjectContextStore = useSubjectContextStore()
const mobileMenuVisible = ref(false)
const currentEntryType = computed(() => (String(window.__QB_ENTRY_TYPE__ || '').trim() === 'teacher' ? 'teacher' : 'student'))
const isStudentEntry = computed(() => currentEntryType.value === 'student')
const entryLabel = computed(() => {
  if (userStore.role === 'super_admin') {
    return '管理员'
  }
  return currentEntryType.value === 'teacher' ? '教师端' : '学生端'
})
const sideConsoleLabel = computed(() => {
  if (userStore.role === 'super_admin') {
    return 'Admin Console'
  }
  return currentEntryType.value === 'teacher' ? 'Teacher Console' : 'Student Console'
})

const routeIconMap = {
  '/student/home': House,
  '/student/analysis': DataAnalysis,
  '/student/analysis/points': DataAnalysis,
  '/student/practice/chapter': EditPen,
  '/student/practice/free': EditPen,
  '/student/practice/mock': EditPen,
  '/student/practice/tasks': EditPen,
  '/student/question-bank': Collection,
  '/student/question-bank/repair': Collection,
  '/student/question-bank/archive': Collection,
  '/student/question-bank/learning-methods': Collection,
  '/student/question-bank/syllabus': Collection,
  '/messages': Bell,
}

const routeDesignMap = {
  '/student/home': {
    navLabel: '学习首页',
    shortLabel: '首页',
  },
  '/student/analysis': {
    navLabel: '知识诊断',
    shortLabel: '诊断',
  },
  '/student/analysis/points': {
    navLabel: '练习积分',
    shortLabel: '积分',
  },
  '/student/practice/chapter': {
    navLabel: '刷题升本',
    shortLabel: '刷题',
  },
  '/student/practice/free': {
    navLabel: '自由练习',
    shortLabel: '练习',
  },
  '/student/practice/mock': {
    navLabel: '模拟考试',
    shortLabel: '模考',
  },
  '/student/practice/tasks': {
    navLabel: '考试任务',
    shortLabel: '任务',
  },
  '/student/question-bank': {
    navLabel: '我的题库',
    shortLabel: '题库',
  },
  '/student/question-bank/repair': {
    navLabel: '错题中心',
    shortLabel: '错题',
  },
  '/student/question-bank/archive': {
    navLabel: '沉淀题库',
    shortLabel: '沉淀',
  },
  '/student/question-bank/learning-methods': {
    navLabel: '学习方法',
    shortLabel: '方法',
  },
  '/student/question-bank/syllabus': {
    navLabel: '考试大纲',
    shortLabel: '大纲',
  },
  '/messages': {
    navLabel: '消息中心',
    shortLabel: '消息',
  },
}

const activeMenuPath = computed(() => {
  const currentPath = String(route.path || '').trim()
  if (currentPath.startsWith('/student/analysis')) {
    return '/student/analysis'
  }
  if (currentPath.startsWith('/student/practice')) {
    return '/student/practice/chapter'
  }
  if (currentPath.startsWith('/student/question-bank')) {
    return '/student/question-bank'
  }
  return currentPath
})
const currentPageLabel = computed(() => (
  String(routeDesignMap[route.path]?.navLabel || route.meta?.navTitle || route.meta?.title || entryLabel.value).trim()
))
const syncingOverlayVisible = computed(() => Boolean(uiFeedbackState.isSyncing))
const syncingOverlayMessage = computed(() => String(uiFeedbackState.syncingMessage || '').trim() || '数据同步中，请稍候...')
const showGlobalSubjectSwitcher = computed(() => isStudentEntry.value && route.path.startsWith('/student'))
const isImmersivePracticeMode = computed(() => {
  const immersive = String(route.query.immersive || '').trim() === '1'
  const path = String(route.path || '').trim()
  return immersive && (path === '/student/practice/free' || path === '/student/practice/mock')
})
const currentRouteSubjectCode = computed(() => String(route.query.subjectCode || '').trim())
const shouldMirrorSubjectIntoRoute = computed(() => shouldSyncStudentSubjectRoute(route.path))
const scopeLabelMaps = computed(() => buildContentLabelMaps(userStore.availableExamCategories))
const unreadMessageCount = ref(0)
const unreadMessageBadge = computed(() => {
  if (!unreadMessageCount.value) {
    return ''
  }
  return unreadMessageCount.value > 99 ? '99+' : String(unreadMessageCount.value)
})

const currentStudentSubjectName = computed(() => (
  String(
    subjectContextStore.currentSubject?.subjectName
    || subjectContextStore.currentSubjectName
    || currentRouteSubjectCode.value
    || '未选择科目',
  ).trim() || '未选择科目'
))
const studentSubjectScope = computed(() => {
  const currentScope = userStore.currentScope || {}
  const examCategoryCode = String(currentScope.examCategoryCode || userStore.examCategoryCode || '').trim()
  const jointExamGroupCode = String(
    currentScope.jointExamGroupCode || userStore.assignedJointGroupCode || userStore.jointExamGroupCode || '',
  ).trim()

  return buildStudentSubjectScope({
    examCategoryName: resolveContentLabel(scopeLabelMaps.value.examCategoryNameMap, examCategoryCode, '未设置学科门类'),
    jointExamGroupName: resolveContentLabel(scopeLabelMaps.value.jointExamGroupNameMap, jointExamGroupCode, '未设置联考专业组'),
    subjectName: currentStudentSubjectName.value,
  })
})

const navigationItems = computed(() => {
  const items = router
    .getRoutes()
    .filter((routeItem) => typeof routeItem.meta?.navTitle === 'string' && routeItem.path.startsWith('/'))
    .filter((routeItem) => !(isStudentEntry.value && routeItem.path === '/messages'))
    .map((routeItem) => ({
      path: routeItem.path,
      navTitle: routeItem.meta.navTitle,
      navOrder: Number(routeItem.meta?.navOrder || 999),
      allowedRoles: Array.isArray(routeItem.meta?.allowedRoles) ? routeItem.meta.allowedRoles : [],
      requiredPermissions: Array.isArray(routeItem.meta?.requiredPermissions)
        ? routeItem.meta.requiredPermissions
        : [],
      icon: routeIconMap[routeItem.path] || Collection,
      designLabel: String(routeDesignMap[routeItem.path]?.navLabel || routeItem.meta?.navTitle || '').trim(),
      shortLabel: String(routeDesignMap[routeItem.path]?.shortLabel || routeItem.meta?.navTitle || '').trim(),
    }))
    .filter((routeItem) => isRoutePathAllowedInEntry(routeItem.path, currentEntryType.value))
    .filter((routeItem) =>
      userStore.ensureAccess({
        allowedRoles: routeItem.allowedRoles,
        requiredPermissions: routeItem.requiredPermissions,
      }).allowed,
    )

  if (userStore.role === 'super_admin') {
    const modulesToHide = [
      '/admin/syllabus', // 大纲仓库
      '/teacher/home', // 教师工作台
      '/teacher/student-accounts', // 学生账号
      '/teacher/questions', // 题库管理
      '/teacher/content-system', // 内容体系
      '/teacher/papers', // 组卷中心
      '/teacher/exam-tasks', // 考试任务
      '/teacher/analytics', // 学情管理
      '/teacher/knowledge', // 知识点管理
    ]
    return items.filter((item) => !modulesToHide.includes(item.path))
  }

  return items.sort((leftItem, rightItem) => leftItem.navOrder - rightItem.navOrder)
})


const practiceSubNavigationItems = computed(() => {
  const rows = [
    {
      path: '/student/practice/chapter',
      label: '章节闯关',
    },
    {
      path: '/student/practice/free',
      label: '自由练习',
    },
    {
      path: '/student/practice/mock',
      label: '模拟考试',
    },
    {
      path: '/student/practice/tasks',
      label: '考试任务',
    },
  ]
  return rows.filter((item) =>
    isRoutePathAllowedInEntry(item.path, currentEntryType.value)
    && userStore.ensureAccess({
      allowedRoles: ['student', 'super_admin'],
      requiredPermissions: [],
    }).allowed,
  )
})

const analysisSubNavigationItems = computed(() => {
  const rows = [
    {
      path: '/student/analysis/overview',
      label: '诊断总览',
    },
    {
      path: '/student/analysis/tasks',
      label: '今日任务',
    },
    {
      path: '/student/analysis/points',
      label: '练习积分',
    },
  ]
  return rows.filter((item) =>
    isRoutePathAllowedInEntry(item.path, currentEntryType.value)
    && userStore.ensureAccess({
      allowedRoles: ['student', 'super_admin'],
      requiredPermissions: [],
    }).allowed,
  )
})

const questionBankSubNavigationItems = computed(() => {
  const rows = [
    {
      path: '/student/question-bank/repair',
      label: '错题中心',
    },
    {
      path: '/student/question-bank/archive',
      label: '沉淀题库',
    },
    {
      path: '/student/question-bank/learning-methods',
      label: '学习方法',
    },
    {
      path: '/student/question-bank/syllabus',
      label: '考试大纲',
    },
    {
      path: '/student/question-bank/guide',
      label: '使用文档',
    },
  ]
  return rows.filter((item) =>
    isRoutePathAllowedInEntry(item.path, currentEntryType.value)
    && userStore.ensureAccess({
      allowedRoles: ['student', 'super_admin'],
      requiredPermissions: [],
    }).allowed,
  )
})

const mobileNavigationItems = computed(() => {
  const mobilePathOrder = [
    '/student/home',
    '/student/practice/chapter',
    '/student/question-bank',
    '/student/analysis',
  ]
  return mobilePathOrder
    .map((path) => navigationItems.value.find((item) => item.path === path))
    .filter(Boolean)
})

const selectedKnowledgeBreadcrumb = computed(() => buildSelectedKnowledgeBreadcrumb(route.query))
const hidePracticeBreadcrumb = computed(() => String(route.path || '').startsWith('/student/practice'))
const showKnowledgeBreadcrumb = computed(() => (
  !isImmersivePracticeMode.value
  && !hidePracticeBreadcrumb.value
  && selectedKnowledgeBreadcrumb.value.length > 0
))
const navigationGroupExpanded = reactive({
  analysis: activeMenuPath.value === '/student/analysis',
  practice: activeMenuPath.value === '/student/practice/chapter',
  questionBank: activeMenuPath.value === '/student/question-bank',
})

function resolveNavigationGroupKey(path) {
  const normalizedPath = String(path || '').trim()
  if (normalizedPath === '/student/analysis') {
    return 'analysis'
  }
  if (normalizedPath === '/student/practice/chapter') {
    return 'practice'
  }
  if (normalizedPath === '/student/question-bank') {
    return 'questionBank'
  }
  return ''
}

function isCollapsibleNavigationItem(path) {
  return Boolean(resolveNavigationGroupKey(path))
}

function isNavigationGroupExpanded(path) {
  const groupKey = resolveNavigationGroupKey(path)
  return groupKey ? Boolean(navigationGroupExpanded[groupKey]) : false
}

function toggleNavigationGroup(path) {
  const groupKey = resolveNavigationGroupKey(path)
  if (!groupKey) {
    return
  }
  navigationGroupExpanded[groupKey] = !navigationGroupExpanded[groupKey]
}

function openMobileMenu() {
  mobileMenuVisible.value = true
}

function normalizeQuerySnapshot(query = {}) {
  return Object.fromEntries(
    Object.keys(query)
      .sort()
      .map((key) => [key, String(Array.isArray(query[key]) ? query[key][0] : query[key] || '').trim()]),
  )
}

async function handleNavigationSelect(nextPath) {
  const normalizedNextPath = String(nextPath || '').trim()
  mobileMenuVisible.value = false
  if (!normalizedNextPath || normalizedNextPath === route.path) {
    return
  }
  await router.push(normalizedNextPath)
}

async function syncGlobalSubjectRouteIfNeeded(subjectCode = '') {
  const normalizedSubjectCode = String(subjectCode || '').trim()
  if (!normalizedSubjectCode || !shouldMirrorSubjectIntoRoute.value) {
    return
  }

  const subjectMeta = subjectContextStore.subjectMetaMap[normalizedSubjectCode] || {}
  const nextLocation = buildStudentRouteLocationForSubject(
    route,
    normalizedSubjectCode,
    String(subjectMeta?.subjectId || '').trim(),
  )

  const currentSnapshot = JSON.stringify(normalizeQuerySnapshot(route.query))
  const nextSnapshot = JSON.stringify(normalizeQuerySnapshot(nextLocation.query))
  if (currentSnapshot === nextSnapshot) {
    return
  }

  await router.replace(nextLocation)
}

async function ensureStudentSubjectContext() {
  if (!showGlobalSubjectSwitcher.value) {
    return
  }

  await subjectContextStore.ensureStudentSubjectContext()
  const nextSubjectCode = resolveStudentSubjectCode(
    subjectContextStore.subjectOptions,
    currentRouteSubjectCode.value,
    subjectContextStore.currentSubjectCode,
  )

  if (!nextSubjectCode) {
    return
  }

  subjectContextStore.setCurrentSubjectCode(nextSubjectCode)
  if (currentRouteSubjectCode.value === nextSubjectCode) {
    return
  }

  await syncGlobalSubjectRouteIfNeeded(nextSubjectCode)
}

async function handleGlobalSubjectChange(nextSubjectCode) {
  const resolvedSubjectCode = resolveStudentSubjectCode(
    subjectContextStore.subjectOptions,
    nextSubjectCode,
    subjectContextStore.currentSubjectCode,
  )
  if (!resolvedSubjectCode) {
    return
  }
  subjectContextStore.setCurrentSubjectCode(resolvedSubjectCode)
  await syncGlobalSubjectRouteIfNeeded(resolvedSubjectCode)
}

async function loadUnreadMessageSummary() {
  try {
    const summary = await fetchMessageUnreadSummary()
    unreadMessageCount.value = Number(summary?.totalUnread || summary?.unreadCount || 0)
  } catch (_error) {
    unreadMessageCount.value = 0
  }
}

async function handleMessageCenterOpen() {
  mobileMenuVisible.value = false
  await router.push('/messages')
}

async function handleLogout() {
  mobileMenuVisible.value = false
  await userStore.logout()
  await router.replace('/login')
}

watch(
  () => [route.path, currentRouteSubjectCode.value],
  async () => {
    await ensureStudentSubjectContext()
  },
)

watch(
  () => route.path,
  async () => {
    await loadUnreadMessageSummary()
  },
)

watch(
  () => activeMenuPath.value,
  (nextPath) => {
    const groupKey = resolveNavigationGroupKey(nextPath)
    if (!groupKey) {
      return
    }
    navigationGroupExpanded[groupKey] = true
  },
)

onMounted(async () => {
  await Promise.all([
    ensureStudentSubjectContext(),
    loadUnreadMessageSummary(),
  ])
})
</script>

<template>
  <div class="layout-frame">
    <div class="layout-frame__backdrop" aria-hidden="true">
      <span class="layout-glow layout-glow--primary"></span>
      <span class="layout-glow layout-glow--secondary"></span>
      <span class="layout-glow layout-glow--accent"></span>
    </div>

    <header v-if="!isImmersivePracticeMode" class="top-shell">
      <div class="top-shell__left">
        <div class="brand-block">
          <div class="brand-line">
            <span class="top-brand">河北专升本AI学习平台</span>
            <div class="page-context">
              <span class="page-context__label">{{ entryLabel }}</span>
              <span class="page-context__divider" aria-hidden="true">/</span>
              <strong>{{ currentPageLabel }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="top-shell__right">
        <div v-if="showGlobalSubjectSwitcher" class="subject-context-cluster">
          <div class="subject-context-switcher">
            <div class="subject-context-copy">
              <span class="subject-context-meta">
                <small>学科门类：</small>
                <strong>{{ studentSubjectScope.examCategoryName }}</strong>
              </span>
              <span class="subject-context-meta">
                <small>联考专业组：</small>
                <strong>{{ studentSubjectScope.jointExamGroupName }}</strong>
              </span>
            </div>
            <el-select
              :model-value="subjectContextStore.currentSubjectCode"
              class="subject-context-select"
              :loading="subjectContextStore.loading"
              :aria-label="`当前科目 ${studentSubjectScope.subjectName}`"
              placeholder="切换科目"
              @change="handleGlobalSubjectChange"
            >
              <el-option
                v-for="item in subjectContextStore.subjectOptions"
                :key="item.subjectCode"
                :label="item.subjectName"
                :value="item.subjectCode"
              />
            </el-select>
          </div>
        </div>

        <button
          type="button"
          class="utility-button utility-button--messages"
          aria-label="notifications"
          @click="handleMessageCenterOpen"
        >
          <el-icon><Bell /></el-icon>
          <span v-if="unreadMessageBadge" class="utility-badge">{{ unreadMessageBadge }}</span>
        </button>

        <button
          type="button"
          class="utility-button utility-button--menu"
          aria-label="navigation menu"
          @click="openMobileMenu"
        >
          <span class="utility-menu-mark">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>

        <div class="avatar-badge">{{ String(userStore.userId || 'S').slice(0, 1).toUpperCase() }}</div>
      </div>
    </header>

    <aside v-if="!isImmersivePracticeMode" class="side-shell">
      <div class="side-shell__brand">
        <span class="side-shell__eyebrow">{{ sideConsoleLabel }}</span>
        <h1>学习导航</h1>
      </div>

      <nav class="side-nav">
        <div
          v-for="item in navigationItems"
          :key="item.path"
          class="side-nav__group"
        >
          <div
            v-if="isCollapsibleNavigationItem(item.path)"
            class="side-nav__item-row"
          >
            <button
              type="button"
              :class="['side-nav__item', { 'side-nav__item--active': activeMenuPath === item.path }]"
              @click="handleNavigationSelect(item.path)"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.designLabel || item.navTitle }}</span>
            </button>
            <button
              type="button"
              :class="[
                'side-nav__toggle',
                { 'side-nav__toggle--active': activeMenuPath === item.path },
                { 'side-nav__toggle--expanded': isNavigationGroupExpanded(item.path) },
              ]"
              :aria-label="`${item.designLabel || item.navTitle}${isNavigationGroupExpanded(item.path) ? '收起' : '展开'}二级菜单`"
              :aria-expanded="String(isNavigationGroupExpanded(item.path))"
              @click="toggleNavigationGroup(item.path)"
            >
              <el-icon class="side-nav__toggle-icon"><ArrowDown /></el-icon>
            </button>
          </div>
          <button
            v-else
            type="button"
            :class="['side-nav__item', { 'side-nav__item--active': activeMenuPath === item.path }]"
            @click="handleNavigationSelect(item.path)"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.designLabel || item.navTitle }}</span>
          </button>

          <transition name="nav-collapse">
            <div
              v-if="item.path === '/student/analysis' && isNavigationGroupExpanded(item.path)"
              class="side-subnav"
            >
              <button
                v-for="subItem in analysisSubNavigationItems"
                :key="subItem.path"
                type="button"
                :class="['side-subnav__item', { 'side-subnav__item--active': route.path === subItem.path }]"
                @click="handleNavigationSelect(subItem.path)"
              >
                <span>{{ subItem.label }}</span>
              </button>
            </div>
          </transition>

          <transition name="nav-collapse">
            <div
              v-if="item.path === '/student/practice/chapter' && isNavigationGroupExpanded(item.path)"
              class="side-subnav"
            >
              <button
                v-for="subItem in practiceSubNavigationItems"
                :key="subItem.path"
                type="button"
                :class="['side-subnav__item', { 'side-subnav__item--active': route.path === subItem.path }]"
                @click="handleNavigationSelect(subItem.path)"
              >
                <span>{{ subItem.label }}</span>
              </button>
            </div>
          </transition>

          <transition name="nav-collapse">
            <div
              v-if="item.path === '/student/question-bank' && isNavigationGroupExpanded(item.path)"
              class="side-subnav"
            >
              <button
                v-for="subItem in questionBankSubNavigationItems"
                :key="subItem.path"
                type="button"
                :class="['side-subnav__item', { 'side-subnav__item--active': route.path === subItem.path }]"
                @click="handleNavigationSelect(subItem.path)"
              >
                <span>{{ subItem.label }}</span>
              </button>
            </div>
          </transition>
        </div>
      </nav>

      <div class="side-utility-links">
        <button type="button" class="side-utility-link" @click="handleMessageCenterOpen">
          <el-icon><Bell /></el-icon>
          <span>帮助与消息</span>
        </button>
        <button type="button" class="side-utility-link side-utility-link--danger" @click="handleLogout">
          <span class="side-utility-link__mark"></span>
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <main :class="['layout-content', { 'layout-content--immersive': isImmersivePracticeMode }]">
      <div class="layout-stage">
        <div v-if="showKnowledgeBreadcrumb" class="global-breadcrumb-bar">
          <span class="global-breadcrumb-label">当前路径</span>
          <el-breadcrumb separator=">">
            <el-breadcrumb-item
              v-for="item in selectedKnowledgeBreadcrumb"
              :key="`${item.level}-${item.label}`"
            >
              <span class="global-breadcrumb-text">{{ item.label }}</span>
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="layout-main">
          <router-view />
        </div>
      </div>
    </main>

    <StudentBottomNav
      v-if="!isImmersivePracticeMode"
      :items="mobileNavigationItems"
      :active-path="activeMenuPath"
      @select="handleNavigationSelect"
    />

    <el-drawer
      v-if="!isImmersivePracticeMode"
      v-model="mobileMenuVisible"
      class="mobile-menu-drawer"
      direction="ltr"
      size="280px"
      :with-header="false"
    >
      <div class="mobile-menu">
        <div class="mobile-menu__head">
          <strong>{{ entryLabel }}菜单</strong>
          <p>完整入口收口在这里，移动端可在这里快速切换页面。</p>
        </div>

        <nav class="mobile-menu__nav">
          <div
            v-for="item in navigationItems"
            :key="item.path"
            class="mobile-menu__group"
          >
            <div
              v-if="isCollapsibleNavigationItem(item.path)"
              class="mobile-menu__item-row"
            >
              <button
                type="button"
                :class="['mobile-menu__item', { 'mobile-menu__item--active': activeMenuPath === item.path }]"
                @click="handleNavigationSelect(item.path)"
              >
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.designLabel || item.navTitle }}</span>
              </button>
              <button
                type="button"
                :class="[
                  'mobile-menu__toggle',
                  { 'mobile-menu__toggle--active': activeMenuPath === item.path },
                  { 'mobile-menu__toggle--expanded': isNavigationGroupExpanded(item.path) },
                ]"
                :aria-label="`${item.designLabel || item.navTitle}${isNavigationGroupExpanded(item.path) ? '收起' : '展开'}二级菜单`"
                :aria-expanded="String(isNavigationGroupExpanded(item.path))"
                @click="toggleNavigationGroup(item.path)"
              >
                <el-icon class="mobile-menu__toggle-icon"><ArrowDown /></el-icon>
              </button>
            </div>
            <button
              v-else
              type="button"
              :class="['mobile-menu__item', { 'mobile-menu__item--active': activeMenuPath === item.path }]"
              @click="handleNavigationSelect(item.path)"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.designLabel || item.navTitle }}</span>
            </button>

            <transition name="nav-collapse">
              <div
                v-if="item.path === '/student/analysis' && isNavigationGroupExpanded(item.path)"
                class="mobile-subnav"
              >
                <button
                  v-for="subItem in analysisSubNavigationItems"
                  :key="subItem.path"
                  type="button"
                  :class="['mobile-subnav__item', { 'mobile-subnav__item--active': route.path === subItem.path }]"
                  @click="handleNavigationSelect(subItem.path)"
                >
                  <span>{{ subItem.label }}</span>
                </button>
              </div>
            </transition>

            <transition name="nav-collapse">
              <div
                v-if="item.path === '/student/practice/chapter' && isNavigationGroupExpanded(item.path)"
                class="mobile-subnav"
              >
                <button
                  v-for="subItem in practiceSubNavigationItems"
                  :key="subItem.path"
                  type="button"
                  :class="['mobile-subnav__item', { 'mobile-subnav__item--active': route.path === subItem.path }]"
                  @click="handleNavigationSelect(subItem.path)"
                >
                  <span>{{ subItem.label }}</span>
                </button>
              </div>
            </transition>

            <transition name="nav-collapse">
              <div
                v-if="item.path === '/student/question-bank' && isNavigationGroupExpanded(item.path)"
                class="mobile-subnav"
              >
                <button
                  v-for="subItem in questionBankSubNavigationItems"
                  :key="subItem.path"
                  type="button"
                  :class="['mobile-subnav__item', { 'mobile-subnav__item--active': route.path === subItem.path }]"
                  @click="handleNavigationSelect(subItem.path)"
                >
                  <span>{{ subItem.label }}</span>
                </button>
              </div>
            </transition>
          </div>
        </nav>

        <div class="mobile-menu__actions">
          <button type="button" class="mobile-menu__link" @click="handleMessageCenterOpen">
            <el-icon><Bell /></el-icon>
            <span>消息中心</span>
          </button>
          <button type="button" class="mobile-menu__link mobile-menu__link--danger" @click="handleLogout">
            <span class="side-utility-link__mark"></span>
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </el-drawer>

    <transition name="loading-fade">
      <div v-if="syncingOverlayVisible" class="global-loading-mask">
        <div class="global-loading-card">
          <span class="loading-dot"></span>
          <span>{{ syncingOverlayMessage }}</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.layout-frame {
  position: relative;
  min-height: 100vh;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(241, 245, 249, 0.94)),
    var(--qb-bg-body);
  color: var(--qb-text-main);
}

.layout-frame__backdrop {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.layout-glow {
  position: absolute;
  border-radius: 999px;
  filter: blur(10px);
  opacity: 0.68;
}

.layout-glow--primary {
  top: -120px;
  right: -80px;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(96, 165, 250, 0.26), rgba(96, 165, 250, 0));
}

.layout-glow--secondary {
  top: 220px;
  left: -120px;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.16), rgba(14, 165, 233, 0));
}

.layout-glow--accent {
  right: 20%;
  bottom: -140px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(129, 140, 248, 0.14), rgba(129, 140, 248, 0));
}

.top-shell {
  position: fixed;
  top: 16px;
  right: 18px;
  left: 18px;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  min-height: 76px;
  padding: 15px 24px;
  border: 1px solid rgba(191, 219, 254, 0.52);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(22px);
  box-shadow: 0 22px 44px rgba(15, 23, 42, 0.08);
}

.top-shell__left,
.top-shell__right,
.side-shell__brand h1,
.side-shell__brand p,
.top-brand,
.page-context strong,
.page-context span {
  margin: 0;
}

.top-shell__left,
.top-shell__right {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.top-shell__left {
  padding-left: 8px;
}

.brand-block {
  min-width: 0;
}

.brand-line {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  min-width: 0;
}

.top-brand {
  color: var(--qb-text-heading);
  font-family: 'Manrope', 'HarmonyOS Sans SC', 'PingFang SC', sans-serif;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.page-context {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
  padding-bottom: 2px;
}

.page-context__label {
  color: var(--qb-text-subtle-9);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

.page-context__divider {
  color: rgba(100, 116, 139, 0.7);
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
}

.page-context strong {
  color: var(--qb-text-info-ink);
  font-size: 14px;
  font-weight: 800;
  line-height: 1.1;
  white-space: nowrap;
}

.side-shell {
  position: fixed;
  top: 108px;
  left: 18px;
  bottom: 20px;
  z-index: 30;
  display: flex;
  flex-direction: column;
  width: 260px;
  padding: 18px 14px 16px;
  border: 1px solid rgba(191, 219, 254, 0.42);
  border-radius: 30px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(241, 245, 249, 0.92)),
    linear-gradient(180deg, rgba(239, 246, 255, 0.24), rgba(239, 246, 255, 0));
  backdrop-filter: blur(18px);
  box-shadow: 0 26px 50px rgba(15, 23, 42, 0.08);
}

.side-shell__brand {
  display: grid;
  gap: 4px;
  padding: 4px 12px 18px;
}

.side-shell__eyebrow {
  color: var(--qb-text-subtle-9);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.side-shell__brand h1 {
  color: var(--qb-text-info-ink);
  font-family: 'Manrope', 'HarmonyOS Sans SC', 'PingFang SC', sans-serif;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.side-nav {
  display: grid;
  gap: 8px;
}

.side-nav__group,
.mobile-menu__group {
  display: grid;
  gap: 6px;
}

.side-nav__item-row,
.mobile-menu__item-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.side-nav__item,
.mobile-menu__item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 13px 14px;
  border: none;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.32);
  color: var(--qb-text-subtle-9);
  font-family: 'Manrope', 'HarmonyOS Sans SC', 'PingFang SC', sans-serif;
  font-size: 14px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.side-nav__item:hover,
.mobile-menu__item:hover {
  background: rgba(255, 255, 255, 0.72);
  color: var(--qb-primary-600);
  transform: translateX(2px) translateY(-1px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.side-nav__item--active,
.mobile-menu__item--active {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.96), rgba(239, 246, 255, 0.92));
  color: var(--qb-text-info-ink);
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.12);
}

.side-nav__toggle,
.mobile-menu__toggle {
  display: grid;
  place-items: center;
  width: 48px;
  border: none;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.32);
  color: var(--qb-text-subtle-9);
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.side-nav__toggle:hover,
.mobile-menu__toggle:hover {
  background: rgba(255, 255, 255, 0.72);
  color: var(--qb-primary-600);
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.side-nav__toggle--active,
.mobile-menu__toggle--active {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.96), rgba(239, 246, 255, 0.92));
  color: var(--qb-text-info-ink);
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.12);
}

.side-nav__toggle-icon,
.mobile-menu__toggle-icon {
  font-size: 16px;
  transition: transform 0.18s ease;
}

.side-nav__toggle--expanded .side-nav__toggle-icon,
.mobile-menu__toggle--expanded .mobile-menu__toggle-icon {
  transform: rotate(180deg);
}

.side-subnav,
.mobile-subnav {
  display: grid;
  gap: 4px;
  padding-left: 18px;
}

.nav-collapse-enter-active,
.nav-collapse-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
  transform-origin: top center;
}

.nav-collapse-enter-from,
.nav-collapse-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.side-subnav__item,
.mobile-subnav__item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.22);
  color: var(--qb-text-subtle-8);
  font-size: 13px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.side-subnav__item:hover,
.mobile-subnav__item:hover {
  background: rgba(255, 255, 255, 0.62);
  color: var(--qb-primary-600);
  transform: translateX(2px);
}

.side-subnav__item--active,
.mobile-subnav__item--active {
  background: rgba(219, 234, 254, 0.9);
  color: var(--qb-text-info-ink);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.08);
}

.side-utility-links {
  display: grid;
  gap: 4px;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid rgba(224, 227, 229, 0.92);
}

.side-utility-link,
.mobile-menu__link {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 14px;
  background: transparent;
  color: var(--qb-text-subtle-9);
  font-size: 14px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.side-utility-link:hover,
.mobile-menu__link:hover {
  background: rgba(241, 245, 249, 0.92);
  color: var(--qb-text-info-ink);
}

.side-utility-link--danger:hover,
.mobile-menu__link--danger:hover {
  color: var(--qb-danger-600);
}

.side-utility-link__mark {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: var(--qb-danger-strong);
  box-shadow: 0 0 0 4px rgba(254, 226, 226, 0.95);
}

.layout-content {
  min-height: 100vh;
  margin-left: 278px;
  padding: 110px 24px 44px 18px;
  position: relative;
  z-index: 1;
}

.layout-content--immersive {
  margin-left: 0;
  padding: 0;
}

.layout-stage {
  padding: 16px 18px 26px;
  border: 1px solid rgba(191, 219, 254, 0.34);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.56);
  backdrop-filter: blur(16px);
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.06);
}

.layout-content--immersive .layout-stage {
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
  backdrop-filter: none;
  box-shadow: none;
}

.global-breadcrumb-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  max-width: 100%;
  margin-bottom: 18px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(191, 219, 254, 0.38);
  color: var(--qb-text-subtle-9);
}

.global-breadcrumb-label,
.global-breadcrumb-text,
.global-breadcrumb-bar :deep(.el-breadcrumb__inner),
.global-breadcrumb-bar :deep(.el-breadcrumb__inner a),
.global-breadcrumb-bar :deep(.el-breadcrumb__separator) {
  color: var(--qb-text-subtle-9);
  font-size: 12px;
  font-weight: 500;
}

.layout-main {
  min-width: 0;
  max-width: 1460px;
}

.subject-context-cluster {
  display: flex;
  align-items: center;
  min-width: min(100%, 470px);
}

.subject-context-switcher {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  width: 100%;
  padding: 4px 0;
}

.subject-context-copy {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex-wrap: wrap;
}

.subject-context-meta,
.subject-context-meta small,
.subject-context-meta strong {
  margin: 0;
}

.subject-context-meta {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  min-width: 0;
}

.subject-context-meta small {
  color: var(--qb-text-subtle-9);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.subject-context-meta strong {
  color: var(--qb-text-heading);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
}

.subject-context-select {
  width: 156px;
  flex-shrink: 0;
}

.subject-context-select :deep(.el-select__wrapper) {
  min-height: 32px;
  border-radius: 999px;
  background: transparent;
  box-shadow: none;
}

.utility-button {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 999px;
  background: rgba(246, 248, 251, 0.92);
  color: var(--qb-text-secondary);
  cursor: pointer;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.utility-button:hover {
  background: rgba(241, 245, 249, 0.94);
  color: var(--qb-text-info-ink);
}

.utility-badge {
  position: absolute;
  top: -4px;
  right: -2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--qb-danger-strong);
  color: var(--qb-text-inverse);
  font-size: 10px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.22);
}

.utility-menu-mark {
  display: grid;
  gap: 3px;
}

.utility-menu-mark span {
  display: block;
  width: 15px;
  height: 2px;
  border-radius: 999px;
  background: currentColor;
}

.avatar-badge {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--qb-primary-100), var(--qb-primary-200));
  color: var(--qb-text-info-ink);
  font-family: 'Manrope', 'HarmonyOS Sans SC', 'PingFang SC', sans-serif;
  font-size: 14px;
  font-weight: 800;
}

.mobile-menu {
  display: grid;
  gap: 18px;
  height: 100%;
}

.mobile-menu__head strong,
.mobile-menu__head p {
  margin: 0;
}

.mobile-menu__head p {
  margin-top: 8px;
  color: var(--qb-text-copy);
  font-size: 13px;
  line-height: 1.7;
}

.mobile-menu__nav,
.mobile-menu__actions {
  display: grid;
  gap: 8px;
}

.mobile-menu__actions {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid rgba(224, 227, 229, 0.92);
}

.mobile-menu-drawer :deep(.el-drawer__body) {
  padding: 20px 16px 16px;
}

.global-loading-mask {
  position: fixed;
  inset: 0;
  z-index: 2500;
  display: grid;
  place-items: center;
  background: rgba(247, 249, 251, 0.62);
  backdrop-filter: blur(4px);
}

.global-loading-card {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(195, 197, 215, 0.28);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
  color: var(--qb-text-heading);
  font-size: 13px;
  font-weight: 700;
}

.loading-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--qb-text-info-ink);
  animation: loading-pulse 0.9s ease-in-out infinite alternate;
}

.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.18s ease;
}

.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

@keyframes loading-pulse {
  from {
    transform: scale(0.85);
    opacity: 0.55;
  }

  to {
    transform: scale(1.12);
    opacity: 1;
  }
}

@media (max-width: 1080px) {
  .top-shell {
    right: 14px;
    left: 14px;
    padding-inline: 16px;
  }

  .top-shell__right {
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .layout-content {
    padding-right: 18px;
   }

  .layout-stage {
    padding-inline: 16px;
  }
}

@media (max-width: 900px) {
  .side-shell {
    display: none;
  }

  .layout-content {
    margin-left: 0;
    padding-top: 102px;
    padding-bottom: 112px;
  }

  .top-shell__right {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .top-shell {
    top: 12px;
    right: 12px;
    left: 12px;
    align-items: flex-start;
    padding-block: 12px;
  }

  .top-shell__left,
  .top-shell__right {
    flex-wrap: wrap;
  }

  .layout-content {
    padding-inline: 12px;
  }

  .layout-stage {
    padding: 14px 12px 20px;
    border-radius: 24px;
  }

  .subject-context-switcher {
    width: 100%;
    justify-content: space-between;
  }

  .subject-context-cluster {
    width: 100%;
    min-width: 0;
  }

  .subject-context-switcher {
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
  }

  .brand-line {
    flex-wrap: wrap;
    gap: 6px 10px;
    align-items: center;
  }

  .global-breadcrumb-bar {
    width: 100%;
  }
}
</style>
