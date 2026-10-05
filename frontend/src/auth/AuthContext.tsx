import { createContext, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  clearToken,
  fetchCurrentUser,
  getToken,
  login as loginRequest,
  register as registerRequest,
  setToken,
  type PublicUser,
  type RegisterInput,
} from '../api'

/** How often an active session re-pings the server to reset its expiry. */
const REFRESH_INTERVAL_MS = 5 * 60 * 1000

/** Activity inside this window counts as "still here". */
const ACTIVITY_WINDOW_MS = REFRESH_INTERVAL_MS

export interface AuthState {
  user: PublicUser | null
  isLoading: boolean
  logIn: (email: string, password: string) => Promise<void>
  signUp: (input: RegisterInput) => Promise<void>
  logOut: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const lastActivityRef = useRef(Date.now())

  // Restore the session on load. A token the server rejects is discarded.
  useEffect(() => {
    const token = getToken()
    if (!token) {
      setIsLoading(false)
      return
    }

    let cancelled = false
    fetchCurrentUser(token)
      .then((restored) => {
        if (!cancelled) setUser(restored)
      })
      .catch(() => {
        clearToken()
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Track real interaction so an abandoned tab is not kept alive forever.
  useEffect(() => {
    const note = () => {
      lastActivityRef.current = Date.now()
    }
    const events = ['click', 'keydown', 'scroll', 'touchstart'] as const
    for (const event of events) {
      window.addEventListener(event, note, { passive: true })
    }
    return () => {
      for (const event of events) {
        window.removeEventListener(event, note)
      }
    }
  }, [])

  // Sliding expiry. Most of the site talks to unauthenticated catalogue
  // endpoints, which would never refresh the token on their own, so an active
  // shopper is kept signed in by periodically re-resolving the session. The
  // response carries a token with a reset clock; api.ts stores it.
  useEffect(() => {
    if (!user) return

    const timer = window.setInterval(() => {
      const token = getToken()
      const isActive = Date.now() - lastActivityRef.current < ACTIVITY_WINDOW_MS
      if (!token || !isActive) return

      fetchCurrentUser(token).catch(() => {
        clearToken()
        setUser(null)
      })
    }, REFRESH_INTERVAL_MS)

    return () => window.clearInterval(timer)
  }, [user])

  const logIn = useCallback(async (email: string, password: string) => {
    const result = await loginRequest(email, password)
    setToken(result.token)
    setUser(result.user)
    lastActivityRef.current = Date.now()
  }, [])

  const signUp = useCallback(async (input: RegisterInput) => {
    const result = await registerRequest(input)
    setToken(result.token)
    setUser(result.user)
    lastActivityRef.current = Date.now()
  }, [])

  const logOut = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, isLoading, logIn, signUp, logOut }),
    [user, isLoading, logIn, signUp, logOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
