import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'

// Les lectures en base passent par react-query : c'est LUI qui tient le cycle de vie d'un GET
// (en cours / erreur / relecture), pas un useEffect qui pose des états à la main. Réglages
// volontairement muets — ils reproduisent à l'identique ce que faisaient les écrans : UNE
// tentative (pas de reprise automatique), pas de relecture au retour d'onglet, et rien gardé
// après démontage (un écran rouvert relit la base, il ne repeint pas un vieux cache).
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false, gcTime: 0 } },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
)
