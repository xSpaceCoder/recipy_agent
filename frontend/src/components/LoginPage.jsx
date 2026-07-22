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
    <div className="login-page" data-mode={mode}>
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
