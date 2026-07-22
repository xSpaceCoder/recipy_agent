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

