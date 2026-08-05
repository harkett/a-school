import { createContext, useContext } from 'react'

// Le contexte d'authentification et son accès, SÉPARÉS du Provider. Un fichier de composant
// ne doit exporter que des composants (sinon Vite ne sait plus quoi recharger à chaud et
// remonte tout l'arbre à chaque sauvegarde) : le hook vit donc ici, dans un simple module.
export const AuthContext = createContext(null)

export function useAuth() {
  return useContext(AuthContext)
}
