import { test, expect } from '@playwright/test';

test('login page renders with email/password form', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.login-card')).toBeVisible();
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
  await expect(page.locator('.submit-btn')).toContainText('Sign In');
  await expect(page.locator('.google-btn')).toBeVisible();
  await expect(page.locator('.forgot-password')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Sign up' })).toBeVisible();
});

test('app has no console errors on load', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  // Filter out expected auth-related errors (no session on fresh load)
  const unexpected = errors.filter(
    (e) => !e.includes('auth') && !e.includes('session') && !e.includes('refresh_token')
  );
  expect(unexpected).toHaveLength(0);
});
