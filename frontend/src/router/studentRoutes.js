const DefaultLayout = () => import('../layouts/DefaultLayout.vue')
const LoginPage = () => import('../views/Auth/Login.vue')
const StudentHome = () => import('../views/Student/Home.vue')
const StudentOnboardingDiagnosis = () => import('../views/Student/OnboardingDiagnosis.vue')
const StudentSubscriptionCheckout = () => import('../views/Student/SubscriptionCheckout.vue')
const StudentSubscriptionSuccess = () => import('../views/Student/SubscriptionSuccess.vue')
const StudentAnalysisShell = () => import('../views/Student/AnalysisShell.vue')
const StudentAnalysis = () => import('../views/Student/Analysis.vue')
const StudentTasks = () => import('../views/Student/Tasks.vue')
const StudentPractice = () => import('../views/Student/Practice.vue')
const StudentExamTasks = () => import('../views/Student/ExamTasks.vue')
const StudentPoints = () => import('../views/Student/Points.vue')
const StudentLearningMethods = () => import('../views/Student/LearningMethods.vue')
const StudentQuestionBankShell = () => import('../views/Student/QuestionBankShell.vue')
const StudentWrongBook = () => import('../views/Student/WrongBook.vue')
const StudentPersonalBank = () => import('../views/Student/PersonalBank.vue')
const StudentQuestionBankSyllabus = () => import('../views/Student/QuestionBankSyllabus.vue')
const StudentQuestionBankGuide = () => import('../views/Student/QuestionBankGuide.vue')
const MessageCenter = () => import('../views/System/Messages.vue')
const SystemError = () => import('../views/System/SystemError.vue')

function resolveLegacyPracticeRedirect(to) {
  const query = { ...(to?.query || {}) }
  const legacyTab = String(query.tab || '').trim().toLowerCase()
  const legacyModule = String(query.module || '').trim().toLowerCase()
  delete query.tab
  const moduleKey = legacyModule || (legacyTab === 'paper' ? 'mock' : legacyTab === 'free' ? 'free' : 'chapter')
  query.module = moduleKey
  const path = moduleKey === 'free'
    ? '/student/practice/free'
    : moduleKey === 'mock'
      ? '/student/practice/mock'
      : moduleKey === 'tasks'
        ? '/student/practice/tasks'
      : '/student/practice/chapter'
  return { path, query }
}

export const studentRoutes = [
  {
    path: '/',
    redirect: '/student/home',
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: {
      title: '注册登录',
      allowedRoles: [],
      requiredPermissions: [],
    },
  },
  {
    path: '/student',
    redirect: '/student/home',
  },
  {
    path: '/student/wrong-book',
    redirect: (to) => ({
      path: '/student/question-bank/repair',
      query: { ...(to?.query || {}) },
    }),
  },
  {
    path: '/student/personal-bank',
    redirect: (to) => ({
      path: '/student/question-bank/archive',
      query: { ...(to?.query || {}) },
    }),
  },
  {
    path: '/student/learning-methods',
    redirect: (to) => ({
      path: '/student/question-bank/learning-methods',
      query: { ...(to?.query || {}) },
    }),
  },
  {
    path: '/student',
    component: DefaultLayout,
    meta: {
      section: 'student',
      allowedRoles: ['student', 'super_admin'],
    },
    children: [
      {
        path: 'home',
        name: 'studentHome',
        component: StudentHome,
        meta: {
          title: '学习首页',
          navTitle: '学习首页',
          navOrder: 50,
          designKey: '_3',
          shellVariant: 'galaxy',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'onboarding/diagnosis',
        name: 'studentOnboardingDiagnosis',
        component: StudentOnboardingDiagnosis,
        meta: {
          title: 'AI 快诊',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'subscription/checkout',
        name: 'studentSubscriptionCheckout',
        component: StudentSubscriptionCheckout,
        meta: {
          title: '订阅开通',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'subscription/success',
        name: 'studentSubscriptionSuccess',
        component: StudentSubscriptionSuccess,
        meta: {
          title: '开通成功',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'analysis',
        component: StudentAnalysisShell,
        meta: {
          title: '知识诊断',
          navTitle: '知识诊断',
          navOrder: 53,
          designKey: '_5',
          shellVariant: 'galaxy',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
        children: [
          {
            path: '',
            redirect: (to) => ({
              path: '/student/analysis/overview',
              query: { ...(to?.query || {}) },
            }),
          },
          {
            path: 'overview',
            name: 'studentAnalysis',
            component: StudentAnalysis,
            meta: {
              title: '诊断总览',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
          {
            path: 'tasks',
            name: 'studentAnalysisTasks',
            component: StudentTasks,
            meta: {
              title: '今日任务',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
          {
            path: 'points',
            name: 'studentAnalysisPoints',
            component: StudentPoints,
            meta: {
              title: '练习积分',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
        ],
      },
      {
        path: 'practice',
        redirect: resolveLegacyPracticeRedirect,
        meta: {
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'practice/chapter',
        name: 'studentPracticeChapter',
        component: StudentPractice,
        meta: {
          title: '刷题升本',
          navTitle: '刷题升本',
          navOrder: 55,
          designKey: '_2',
          shellVariant: 'sanctuary',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'practice/free',
        name: 'studentPracticeFree',
        component: StudentPractice,
        meta: {
          title: '自由练习',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'practice/mock',
        name: 'studentPracticeMock',
        component: StudentPractice,
        meta: {
          title: '模拟考试',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'practice/tasks',
        name: 'studentPracticeTasks',
        component: StudentExamTasks,
        meta: {
          title: '考试任务',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'points',
        redirect: (to) => ({
          path: '/student/analysis/points',
          query: { ...(to?.query || {}) },
        }),
        meta: {
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
      {
        path: 'question-bank',
        component: StudentQuestionBankShell,
        meta: {
          title: '我的题库',
          navTitle: '我的题库',
          navOrder: 60,
          designKey: '_1',
          shellVariant: 'sanctuary',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
        children: [
          {
            path: '',
            redirect: '/student/question-bank/repair',
          },
          {
            path: 'repair',
            name: 'studentQuestionBankRepair',
            component: StudentWrongBook,
            meta: {
              title: '错题中心',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
          {
            path: 'archive',
            name: 'studentQuestionBankArchive',
            component: StudentPersonalBank,
            meta: {
              title: '沉淀题库',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
          {
            path: 'syllabus',
            name: 'studentQuestionBankSyllabus',
            component: StudentQuestionBankSyllabus,
            meta: {
              title: '考试大纲',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
          {
            path: 'learning-methods',
            name: 'studentQuestionBankLearningMethods',
            component: StudentLearningMethods,
            meta: {
              title: '学习方法',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
          {
            path: 'guide',
            name: 'studentQuestionBankGuide',
            component: StudentQuestionBankGuide,
            meta: {
              title: '使用文档',
              allowedRoles: ['student', 'super_admin'],
              requiredPermissions: [],
            },
          },
        ],
      },
    ],
  },
  {
    path: '/messages',
    component: DefaultLayout,
    meta: {
      section: 'shared',
      allowedRoles: ['student', 'super_admin'],
    },
    children: [
      {
        path: '',
        name: 'messageCenter',
        component: MessageCenter,
        meta: {
          title: '消息中心',
          navTitle: '消息中心',
          navOrder: 90,
          designKey: '_4',
          shellVariant: 'sanctuary',
          allowedRoles: ['student', 'super_admin'],
          requiredPermissions: [],
        },
      },
    ],
  },
  {
    path: '/error/500',
    name: 'systemError',
    component: SystemError,
    meta: {
      title: '系统错误',
      allowedRoles: [],
      requiredPermissions: [],
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/student/home',
  },
]
