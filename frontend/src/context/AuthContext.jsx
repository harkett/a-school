import { useCallback, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_AUTH, refreshSession } from '../utils/api.js'
import { AuthContext } from './contexteAuth.js'

const CLE_MOI = ['auth', 'me']

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()

  // QUI est connecté = une lecture serveur (/auth/me), pas un état posé à la main : react-query
  // en tient le cycle de vie (première lecture, relecture, « en cours »). Un échec ne relance
  // rien tout seul — la fonction rend `null`, c'est-à-dire « personne », et l'app va au login.
  const { data: user = null, isPending: loading, refetch } = useQuery({
    queryKey: CLE_MOI,
    queryFn: async () => {
      try {
        let r = await fetchWithTimeout('/api/auth/me', { credentials: 'include' }, TIMEOUT_AUTH)
        if (r.ok) return await r.json()
        if (r.status === 401) {
          // Renouvellement partagé (single-flight) — jamais en parallèle d'un refresh apiFetch.
          const renouvele = await refreshSession()
          if (renouvele) {
            r = await fetchWithTimeout('/api/auth/me', { credentials: 'include' }, TIMEOUT_AUTH)
            if (r.ok) return await r.json()
          }
        }
        return null
      } catch {
        return null   // serveur injoignable : on ne devine pas une session, on n'en a pas
      }
    },
    gcTime: Infinity,   // la session vit tant que l'app vit — elle ne s'oublie pas entre deux écrans
  })

  // Poser l'utilisateur SANS repasser par le serveur : le login vient de recevoir sa fiche
  // complète dans la réponse, la redemander serait un aller-retour pour rien.
  const setUser = useCallback((u) => { queryClient.setQueryData(CLE_MOI, u) }, [queryClient])
  const refreshUser = useCallback(async () => { await refetch() }, [refetch])

  useEffect(() => {
    // Renouvellement proactif toutes les 10 min pour que le jeton n'expire jamais en séance.
    // Passe par le guichet partagé → jamais en concurrence avec un refresh apiFetch.
    const id = setInterval(() => { refreshSession() }, 10 * 60 * 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    function onStorage(e) {
      if (e.key === 'logout') window.location.replace('/login')
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  // Retour sur la page depuis le cache du navigateur (bouton Précédent) : la session a pu
  // mourir entre-temps, on la relit.
  useEffect(() => {
    function onPageShow(e) {
      if (e.persisted) refetch()
    }
    window.addEventListener('pageshow', onPageShow)
    return () => window.removeEventListener('pageshow', onPageShow)
  }, [refetch])

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
    <AuthContext.Provider value={{ user, setUser, loading, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}
