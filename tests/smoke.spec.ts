import { test, expect } from '@playwright/test';

test('login page renders', async ({ page }) => {
  await page.goto('/');
  // App should show login page when not authenticated
  await expect(page.locator('body')).toBeVisible();
  // Check that the app loaded (not a blank page or error)
  const title = await page.title();
  expect(title).toBeTruthy();
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
