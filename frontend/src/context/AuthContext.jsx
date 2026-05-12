import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { fetchWithTimeout, TIMEOUT_AUTH } from '../utils/api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    try {
      let r = await fetchWithTimeout('/api/auth/me', { credentials: 'include' }, TIMEOUT_AUTH)
      if (r.ok) {
        setUser(await r.json())
        return
      }
      if (r.status === 401) {
        const ref = await fetchWithTimeout('/api/auth/refresh', {
          method: 'POST',
          credentials: 'include',
        }, TIMEOUT_AUTH)
        if (ref.ok) {
          r = await fetchWithTimeout('/api/auth/me', { credentials: 'include' }, TIMEOUT_AUTH)
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
      fetchWithTimeout('/api/auth/refresh', { method: 'POST', credentials: 'include' }, TIMEOUT_AUTH)
    }, 10 * 60 * 1000)
    return () => clearInterval(id)
  }, [checkAuth])

  useEffect(() => {
    function onStorage(e) {
      if (e.key === 'logout') window.location.replace('/login')
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  useEffect(() => {
    function onPageShow(e) {
      if (e.persisted) checkAuth()
    }
    window.addEventListener('pageshow', onPageShow)
    return () => window.removeEventListener('pageshow', onPageShow)
  }, [checkAuth])

  async function logout() {
    try {
      await fetchWithTimeout('/api/auth/logout', { method: 'POST', credentials: 'include' }, TIMEOUT_AUTH)
    } catch {
      // force la sortie locale même si le serveur ne répond pas
    }
    localStorage.setItem('logout', Date.now()) // signal cross-tab avant clear
    localStorage.clear()
    sessionStorage.clear()
    window.location.replace('/login')
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
