import { init, use } from 'echarts/core'
import { GaugeChart, GraphChart, RadarChart, SunburstChart } from 'echarts/charts'
import { install as GraphicComponent } from 'echarts/lib/component/graphic/install.js'
import { install as RadarComponent } from 'echarts/lib/component/radar/install.js'
import { install as TitleComponent } from 'echarts/lib/component/title/install.js'
import { install as TooltipComponent } from 'echarts/lib/component/tooltip/install.js'
import { CanvasRenderer } from 'echarts/renderers'
import { ensureZsbEchartsTheme } from './zsbTheme'

let registered = false

export function ensureStudentEchartsRuntime() {
  const themeName = ensureZsbEchartsTheme()
  if (!registered) {
    use([
      GaugeChart,
      GraphChart,
      RadarChart,
      SunburstChart,
      GraphicComponent,
      RadarComponent,
      TitleComponent,
      TooltipComponent,
      CanvasRenderer,
    ])
    registered = true
  }
  return function initWithZsbTheme(dom, opts) {
    return init(dom, themeName, opts)
  }
}
