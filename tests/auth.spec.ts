import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test('renders Google OAuth button', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.google-btn')).toBeVisible()
    await expect(page.locator('.google-btn')).toContainText('Continue with Google')
  })

  test('shows sign-in form by default', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('.submit-btn')).toContainText('Sign In')
    await expect(page.getByRole('button', { name: 'Sign up' })).toBeVisible()
  })

  test('toggles to sign-up mode', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Sign up' }).click()
    await expect(page.locator('.submit-btn')).toContainText('Sign Up')
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible()
  })

  test('shows forgot password link in sign-in mode', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.forgot-password')).toBeVisible()
    await expect(page.locator('.forgot-password')).toContainText('Forgot password?')
  })

  test('forgot password shows email-only form with back link', async ({ page }) => {
    await page.goto('/')
    await page.locator('.forgot-password').click()
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).not.toBeVisible()
    await expect(page.locator('.submit-btn')).toContainText('Send Reset Link')
    await expect(page.getByRole('button', { name: 'Back to sign in' })).toBeVisible()
  })

  test('shows error on invalid sign-in', async ({ page }) => {
    await page.goto('/')
    await page.locator('input[type="email"]').fill('nonexistent@test.com')
    await page.locator('input[type="password"]').fill('wrongpassword')
    await page.locator('.submit-btn').click()
    await expect(page.locator('.error')).toBeVisible()
  })

  test('sign-up form has name field', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Sign up' }).click()
    await expect(page.locator('input[type="text"]')).toBeVisible()
    await expect(page.locator('input[type="text"]')).toHaveAttribute('placeholder', /name/i)
  })
})
