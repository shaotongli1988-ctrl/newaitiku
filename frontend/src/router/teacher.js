import { createScopedRouter } from './index'
import { teacherRoutes } from './teacherRoutes'

const teacherRouter = createScopedRouter({
  routes: teacherRoutes,
  entryType: 'teacher',
})

export { teacherRoutes }
export default teacherRouter

