import { registerTheme } from 'echarts/core'

const ZSB_THEME_NAME = 'zsb-theme'
const ZSB_THEME = {
  color: ['#2F54EB', '#52C41A', '#13C2C2', '#722ED1', '#FA8C16'],
}

let themeRegistered = false

export function ensureZsbEchartsTheme() {
  if (!themeRegistered) {
    registerTheme(ZSB_THEME_NAME, ZSB_THEME)
    themeRegistered = true
  }

  return ZSB_THEME_NAME
}
