import { createScopedRouter } from './index'
import { studentRoutes } from './studentRoutes'

const studentRouter = createScopedRouter({
  routes: studentRoutes,
  entryType: 'student',
})

export { studentRoutes }
export default studentRouter

