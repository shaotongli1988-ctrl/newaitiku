import { init, use } from 'echarts/core'
import { BarChart, PieChart, RadarChart, ScatterChart } from 'echarts/charts'
import { install as GridComponent } from 'echarts/lib/component/grid/install.js'
import { install as LegendComponent } from 'echarts/lib/component/legend/install.js'
import { install as RadarComponent } from 'echarts/lib/component/radar/install.js'
import { install as TooltipComponent } from 'echarts/lib/component/tooltip/install.js'
import { CanvasRenderer } from 'echarts/renderers'
import { ensureZsbEchartsTheme } from './zsbTheme'

let registered = false

export function ensureTeacherEchartsRuntime() {
  const themeName = ensureZsbEchartsTheme()
  if (!registered) {
    use([
      BarChart,
      PieChart,
      RadarChart,
      ScatterChart,
      GridComponent,
      LegendComponent,
      RadarComponent,
      TooltipComponent,
      CanvasRenderer,
    ])
    registered = true
  }
  return function initWithZsbTheme(dom, opts) {
    return init(dom, themeName, opts)
  }
}
