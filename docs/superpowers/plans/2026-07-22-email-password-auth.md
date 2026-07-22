# Email/Password Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace email magic link with email+password login while keeping Google OAuth. Add self-service sign-up and password reset.

**Architecture:** Single LoginPage component with mode toggling (sign-in / sign-up / forgot-password). All auth methods use Supabase JS client built-in functions directly. No backend changes needed.

**Tech Stack:** React, Supabase JS client, Playwright (E2E tests)

## Global Constraints

- `@supabase/supabase-js` already installed — no new dependencies
- Backend `auth.py` unchanged — JWT verification remains identical
- Service worker `sw.js` unchanged — already excludes Supabase URLs from cache
- Auth context `useAuth.jsx` unchanged — session management stays the same
- All auth via `supabase.auth.*` built-in methods — no custom API endpoints
- Supabase Dashboard: "Confirm email" already disabled in Auth → Settings
- Existing users need to be deleted (magic link users can't use password auth)

---

### Task 1: Rewrite LoginPage with email/password, sign-up toggle, and forgot password

**Files:**
- Modify: `frontend/src/components/LoginPage.jsx` (full rewrite)
- Test: `tests/auth.spec.ts` (new file)

**Interfaces:**
- Consumes: `supabase.auth.signInWithPassword({ email, password })`, `supabase.auth.signUp({ email, password })`, `supabase.auth.resetPasswordForEmail(email)`, `supabase.auth.signInWithOAuth({ provider: 'google' })`
- Produces: `<LoginPage />` with `data-mode` attribute (`"signin"`, `"signup"`, `"forgot"`), toggle links, submit handler

- [ ] **Step 1: Write the failing E2E tests**

Create `tests/auth.spec.ts`:

```ts
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
    await expect(page.locator('.auth-toggle')).toContainText('Sign up')
  })

  test('toggles to sign-up mode', async ({ page }) => {
    await page.goto('/')
    await page.locator('.auth-toggle').click()
    await expect(page.locator('.submit-btn')).toContainText('Sign Up')
    await expect(page.locator('.auth-toggle')).toContainText('Sign in')
  })

  test('shows forgot password link in sign-in mode', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.forgot-password')).toBeVisible()
    await expect(page.locator('.forgot-password')).toContainText('Forgot password?')
  })

  test('forgot password shows email-only form with back link', async ({ page }) => {
    await page.goto('/')
    await page.locator('.forgot-password').click()
    // Should show email field, no password field, "Send Reset Link" button
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).not.toBeVisible()
    await expect(page.locator('.submit-btn')).toContainText('Send Reset Link')
    // Should have a back link
    await expect(page.locator('.auth-toggle')).toContainText('Back to sign in')
  })

  test('shows error on invalid sign-in', async ({ page }) => {
    await page.goto('/')
    await page.locator('input[type="email"]').fill('nonexistent@test.com')
    await page.locator('input[type="password"]').fill('wrongpassword')
    await page.locator('.submit-btn').click()
    // Supabase returns error for invalid credentials
    await expect(page.locator('.error')).toBeVisible()
  })

  test('sign-up form has name field', async ({ page }) => {
    await page.goto('/')
    await page.locator('.auth-toggle').click()
    await expect(page.locator('input[type="text"]')).toBeVisible()
    await expect(page.locator('input[type="text"]')).toHaveAttribute('placeholder', /name/i)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx playwright test tests/auth.spec.ts --project=chromium`
Expected: Tests fail because LoginPage still shows magic link form

- [ ] **Step 3: Rewrite LoginPage.jsx**

Replace the magic link logic with email+password auth supporting three modes: `signin`, `signup`, `forgot`.

```jsx
import { useState } from 'react'
import { supabase } from '../lib/supabase'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [mode, setMode] = useState('signin')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    let result
    if (mode === 'signin') {
      result = await supabase.auth.signInWithPassword({ email, password })
    } else if (mode === 'signup') {
      result = await supabase.auth.signUp({
        email,
        password,
        options: { data: { full_name: name } }
      })
    } else if (mode === 'forgot') {
      result = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin
      })
    }

    setLoading(false)
    if (result?.error) {
      setError(result.error.message)
    } else if (mode === 'forgot') {
      setSent(true)
    }
  }

  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin }
    })
    if (error) setError(error.message)
  }

  const switchMode = (newMode) => {
    setMode(newMode)
    setError('')
    setSent(false)
  }

  const isSignIn = mode === 'signin'
  const isSignUp = mode === 'signup'
  const isForgot = mode === 'forgot'

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Recipe Agent</h1>
        <p className="login-subtitle">Sign in to access your recipes</p>

        {error && <div className="error">{error}</div>}

        {sent ? (
          <div className="reset-sent">
            Check your email for the reset link!
          </div>
        ) : (
          <>
            <button className="google-btn" onClick={handleGoogleLogin}>
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>

            <div className="divider">
              <span>or</span>
            </div>

            <form onSubmit={handleSubmit}>
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              {isSignUp && (
                <input
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              )}
              {!isForgot && (
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              )}
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading
                  ? (isSignIn ? 'Signing in...' : isSignUp ? 'Signing up...' : 'Sending...')
                  : (isSignIn ? 'Sign In' : isSignUp ? 'Sign Up' : 'Send Reset Link')}
              </button>
            </form>

            <div className="auth-links">
              {isSignIn && (
                <button className="auth-toggle forgot-password" onClick={() => switchMode('forgot')}>
                  Forgot password?
                </button>
              )}
              <button className="auth-toggle" onClick={() => switchMode(isSignIn ? 'signup' : 'signin')}>
                {isSignIn ? 'Sign up' : isSignUp ? 'Sign in' : 'Back to sign in'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx playwright test tests/auth.spec.ts --project=chromium`
Expected: All 7 tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/LoginPage.jsx tests/auth.spec.ts
git commit -m "feat: replace magic link with email/password auth
```

---

### Task 2: Add and update CSS styles

**Files:**
- Modify: `frontend/src/index.css` (lines ~694-700)

**Interfaces:**
- Consumes: new classNames from LoginPage.jsx: `.auth-toggle`, `.forgot-password`, `.reset-sent`
- Produces: styled login form

- [ ] **Step 1: Update CSS**

Replace the `.magic-link-sent` block and add styles for auth toggle links:

After line 700 (end of `.magic-link-sent` / `.reset-sent`), replace the block and add new styles:

```css
.reset-sent {
  padding: 16px;
  background: var(--green-bg);
  color: var(--green);
  border-radius: 8px;
  font-weight: 500;
}

.auth-links {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.auth-toggle {
  background: none;
  border: none;
  color: var(--green);
  font-size: 0.875rem;
  cursor: pointer;
  padding: 4px;
}

.auth-toggle:hover {
  text-decoration: underline;
}

.forgot-password {
  color: var(--text-muted);
  font-size: 0.8rem;
}
```

Remove the old `.magic-link-sent` block (lines 694-700).

- [ ] **Step 2: Run E2E tests to verify CSS works**

Run: `npx playwright test tests/auth.spec.ts tests/smoke.spec.ts --project=chromium`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "style: add login form styles for email/password auth"
```

---

### Task 3: Update smoke test for new login elements

**Files:**
- Modify: `tests/smoke.spec.ts`

**Interfaces:**
- Consumes: updated LoginPage with new DOM structure
- Produces: verified smoke tests pass with new elements

- [ ] **Step 1: Update smoke tests**

Replace `tests/smoke.spec.ts` with:

```ts
import { test, expect } from '@playwright/test'

test('login page renders with email/password form', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('.login-card')).toBeVisible()
  await expect(page.locator('input[type="email"]')).toBeVisible()
  await expect(page.locator('input[type="password"]')).toBeVisible()
  await expect(page.locator('.submit-btn')).toContainText('Sign In')
  await expect(page.locator('.google-btn')).toBeVisible()
  await expect(page.locator('.forgot-password')).toBeVisible()
  await expect(page.locator('.auth-toggle')).toContainText('Sign up')
})

test('app has no console errors on load', async ({ page }) => {
  const errors: string[] = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text())
  })
  await page.goto('/')
  await page.waitForLoadState('networkidle')
  const unexpected = errors.filter(
    (e) => !e.includes('auth') && !e.includes('session') && !e.includes('refresh_token')
  )
  expect(unexpected).toHaveLength(0)
})
```

- [ ] **Step 2: Run smoke tests**

Run: `npx playwright test tests/smoke.spec.ts --project=chromium`
Expected: Both tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/smoke.spec.ts
git commit -m "test: update smoke tests for email/password login form
```
