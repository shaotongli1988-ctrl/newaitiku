import { chromium } from 'playwright'

const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({
  viewport: { width: 1100, height: 1400 },
})
const page = await context.newPage()

await page.addInitScript(() => {
  window.localStorage.setItem('qbAccessToken', 'mock-teacher-token')
  window.localStorage.setItem('qbUserRole', 'teacher')
  window.localStorage.setItem('qbUserId', 'teacher-001')
  window.localStorage.setItem('qbPermissionKeys', JSON.stringify(['analytics:view', 'paper:manage', 'question:manage', 'student:manage']))
})

await page.goto('http://127.0.0.1:4186/teacher/analytics', { waitUntil: 'domcontentloaded' })
await page.locator('.page-header').waitFor()
await page.waitForTimeout(2000)

const confirmButton = page.getByRole('button', { name: '我知道了' })
if (await confirmButton.count()) {
  await confirmButton.click()
}

await page.getByRole('button', { name: 'AI 建议' }).click()
await page.waitForTimeout(500)
await page.screenshot({ path: '/tmp/newaitiku-teacher-analytics-drawer-open.png', fullPage: true })

await browser.close()
