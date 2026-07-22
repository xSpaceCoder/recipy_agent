# Task 1 Report: Rewrite LoginPage with email/password auth

## What I implemented

- **`frontend/src/components/LoginPage.jsx`** — Replaced magic link flow with three-mode email/password auth:
  - `signin` mode: email + password form with "Sign In" button, forgot password link, and toggle to signup
  - `signup` mode: email + password + name fields with "Sign Up" button, toggle back to sign in
  - `forgot` mode: email-only form with "Send Reset Link" button, back link to sign in
  - Google OAuth button retained in all modes
  - Handles loading, error, and sent states; mode switching clears error/sent state

- **`tests/auth.spec.ts`** — 7 E2E tests covering all UI states

## What I tested and test results

All 7 tests pass with `npx playwright test tests/auth.spec.ts --project=chromium`:

| Test | Status |
|------|--------|
| renders Google OAuth button | ✅ |
| shows sign-in form by default | ✅ |
| toggles to sign-up mode | ✅ |
| shows forgot password link in sign-in mode | ✅ |
| forgot password shows email-only form with back link | ✅ |
| shows error on invalid sign-in | ✅ |
| sign-up form has name field | ✅ |

## TDD Evidence

**RED** — Before implementing: 6 tests failed, 1 passed (Google button already existed). Failures were:
- No `input[type="password"]` (magic link had none)
- No `.auth-toggle` buttons
- No `.forgot-password` link
- `.submit-btn` showed "Send Magic Link" not "Sign In"

**GREEN** — After rewrite: all 7 tests pass.

## Files changed

- `frontend/src/components/LoginPage.jsx` — full rewrite (77 → 134 lines)
- `tests/auth.spec.ts` — new file (54 lines)

## Self-review findings

- Tests originally used `.auth-toggle` locator which was ambiguous (both "Forgot password?" and "Sign up" buttons shared the class). Fixed by switching to `getByRole('button', { name: '...' })` for mode toggle buttons.
- `.forgot-password` is unique (only rendered in signin mode), so class locator works fine there.
- Implementation matches the brief exactly — no deviations, no unnecessary additions.

## Issues or concerns

None. All tests pass, commit clean.
