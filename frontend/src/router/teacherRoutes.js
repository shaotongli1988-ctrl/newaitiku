const DefaultLayout = () => import('../layouts/DefaultLayout.vue')
const AdminHome = () => import('../views/Admin/Home.vue')
const AdminControlCenter = () => import('../views/Admin/ControlCenter.vue')
const AdminSyllabus = () => import('../views/Admin/Syllabus.vue')
const LoginPage = () => import('../views/Auth/Login.vue')
const TeacherHome = () => import('../views/Teacher/Home.vue')
const TeacherStudentAccounts = () => import('../views/Teacher/StudentAccounts.vue')
const TeacherQuestions = () => import('../views/Teacher/QuestionManagement.vue')
const TeacherImportHistoryDetail = () => import('../views/Teacher/ImportHistoryDetail.vue')
const TeacherPapers = () => import('../views/Teacher/Papers.vue')
const TeacherExamTasks = () => import('../views/Teacher/ExamTasks.vue')
const TeacherKnowledge = () => import('../views/Teacher/Knowledge.vue')
const TeacherContentSystem = () => import('../views/Teacher/ContentSystem.vue')
const TeacherAnalytics = () => import('../views/Teacher/Analytics.vue')
const TeacherUsageGuide = () => import('../views/Teacher/UsageGuide.vue')
const MessageCenter = () => import('../views/System/Messages.vue')
const SystemError = () => import('../views/System/SystemError.vue')

export const teacherRoutes = [
  {
    path: '/',
    redirect: '/teacher/home',
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
    path: '/admin',
    redirect: '/admin/home',
  },
  {
    path: '/admin',
    component: DefaultLayout,
    meta: {
      section: 'admin',
      allowedRoles: ['super_admin'],
    },
    children: [
      {
        path: 'home',
        name: 'adminHome',
        component: AdminHome,
        meta: {
          title: '管理驾驶舱',
          navTitle: '管理驾驶舱',
          navOrder: 10,
          allowedRoles: ['super_admin'],
          requiredPermissions: ['settings:manage'],
        },
      },
      {
        path: 'control-center',
        name: 'adminControlCenter',
        component: AdminControlCenter,
        meta: {
          title: '系统控制台',
          navTitle: '系统控制',
          navOrder: 15,
          allowedRoles: ['super_admin'],
          requiredPermissions: ['settings:manage'],
        },
      },
      {
        path: 'syllabus',
        name: 'adminSyllabus',
        component: AdminSyllabus,
        meta: {
          title: '大纲仓库',
          navTitle: '大纲仓库',
          navOrder: 16,
          allowedRoles: ['super_admin'],
          requiredPermissions: ['settings:manage'],
        },
      },
    ],
  },
  {
    path: '/teacher',
    redirect: '/teacher/home',
  },
  {
    path: '/teacher',
    component: DefaultLayout,
    meta: {
      section: 'teacher',
      allowedRoles: ['teacher'],
    },
    children: [
      {
        path: 'home',
        name: 'teacherHome',
        component: TeacherHome,
        meta: {
          title: '教师工作台',
          navTitle: '教师工作台',
          navOrder: 20,
          allowedRoles: ['teacher'],
          requiredPermissions: [],
        },
      },
      {
        path: 'questions',
        name: 'teacherQuestions',
        component: TeacherQuestions,
        meta: {
          title: '题库管理',
          navTitle: '题库管理',
          navOrder: 30,
          allowedRoles: ['teacher'],
          requiredPermissions: ['question:manage'],
        },
      },
      {
        path: 'student-accounts',
        name: 'teacherStudentAccounts',
        component: TeacherStudentAccounts,
        meta: {
          title: '学生账号开通',
          navTitle: '学生账号',
          navOrder: 32,
          allowedRoles: ['teacher'],
          requiredPermissions: ['student:manage'],
        },
      },
      {
        path: 'content-system',
        name: 'teacherContentSystem',
        component: TeacherContentSystem,
        meta: {
          title: '内容体系字典',
          navTitle: '内容体系',
          navOrder: 33,
          allowedRoles: ['teacher'],
          requiredPermissions: ['paper:manage'],
        },
      },
      {
        path: 'import-history',
        name: 'teacherImportHistory',
        redirect: '/teacher/questions#import-history',
        meta: {
          allowedRoles: ['teacher'],
          requiredPermissions: ['question:manage'],
        },
      },
      {
        path: 'import-history/task/:taskId',
        name: 'teacherImportHistoryDetail',
        component: TeacherImportHistoryDetail,
        meta: {
          title: '导入任务详情',
          allowedRoles: ['teacher'],
          requiredPermissions: ['question:manage'],
        },
      },
      {
        path: 'papers',
        name: 'teacherPapers',
        component: TeacherPapers,
        meta: {
          title: '组卷中心',
          navTitle: '组卷中心',
          navOrder: 35,
          allowedRoles: ['teacher'],
          requiredPermissions: ['paper:manage'],
        },
      },
      {
        path: 'exam-tasks',
        name: 'teacherExamTasks',
        component: TeacherExamTasks,
        meta: {
          title: '考试任务管理',
          navTitle: '考试任务',
          navOrder: 36,
          allowedRoles: ['teacher'],
          requiredPermissions: ['paper:manage'],
        },
      },
      {
        path: 'knowledge',
        name: 'teacherKnowledge',
        component: TeacherKnowledge,
        meta: {
          title: '知识点管理',
          navTitle: '知识点管理',
          navOrder: 45,
          allowedRoles: ['teacher'],
          requiredPermissions: ['question:manage'],
        },
      },
      {
        path: 'analytics',
        name: 'teacherAnalytics',
        component: TeacherAnalytics,
        meta: {
          title: '学情管理',
          navTitle: '学情管理',
          navOrder: 40,
          allowedRoles: ['teacher'],
          requiredPermissions: ['analytics:view'],
        },
      },
      {
        path: 'guide',
        name: 'teacherUsageGuide',
        component: TeacherUsageGuide,
        meta: {
          title: '使用文档',
          navTitle: '使用文档',
          navOrder: 48,
          allowedRoles: ['teacher'],
          requiredPermissions: [],
        },
      },
    ],
  },
  {
    path: '/messages',
    component: DefaultLayout,
    meta: {
      section: 'shared',
      allowedRoles: ['super_admin', 'teacher'],
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
          allowedRoles: ['super_admin', 'teacher'],
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
    redirect: '/teacher/home',
  },
]
