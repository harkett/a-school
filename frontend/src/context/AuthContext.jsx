import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    try {
      let r = await fetch('/api/auth/me', { credentials: 'include' })
      if (r.ok) {
        setUser(await r.json())
        return
      }
      if (r.status === 401) {
        // Try to refresh silently
        const ref = await fetch('/api/auth/refresh', {
          method: 'POST',
          credentials: 'include',
        })
        if (ref.ok) {
          r = await fetch('/api/auth/me', { credentials: 'include' })
          if (r.ok) {
            setUser(await r.json())
            return
          }
        }
      }
      setUser(null)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
    // Refresh proactively every 10 min so the access token never expires mid-session
    const id = setInterval(() => {
      fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' })
    }, 10 * 60 * 1000)
    return () => clearInterval(id)
  }, [checkAuth])

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
