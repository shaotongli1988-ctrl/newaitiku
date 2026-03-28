import { expect, test } from '@playwright/test'

test('teacher analytics drawer screenshot', async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('qbAccessToken', 'mock-teacher-token')
    window.localStorage.setItem('qbUserRole', 'teacher')
    window.localStorage.setItem('qbUserId', 'teacher-001')
    window.localStorage.setItem('qbPermissionKeys', JSON.stringify(['analytics:view', 'paper:manage', 'question:manage', 'student:manage']))
  })

  await page.setViewportSize({ width: 1100, height: 1400 })
  await page.goto('http://127.0.0.1:4186/teacher/analytics', { waitUntil: 'domcontentloaded' })
  await page.locator('.page-header').waitFor()
  await page.waitForTimeout(2000)

  const confirmButton = page.getByRole('button', { name: '我知道了' })
  if (await confirmButton.count()) {
    await confirmButton.click()
  }

  await page.getByRole('button', { name: 'AI 建议' }).click()
  await expect(page.locator('.ai-drawer')).toBeVisible()
  await page.waitForTimeout(500)
  await page.screenshot({ path: '/tmp/newaitiku-teacher-analytics-drawer-open.png', fullPage: true })
})
