// Écran « Mes contenus » — la bibliothèque unique du prof (modèle playlist :
// séquence ⊃ séances ⊃ activités, parent toujours facultatif).
//
// ARCHITECTURE (décision utilisateur du 30/07) : UNE CARTOUCHE PAR ONGLET — Tout, Séquences,
// Séances, Activités vivent chacun dans LEUR composant (components/contenus/Onglet*.jsx),
// avec leur état à eux (sélection, aperçu). Ce fichier n'est que le SQUELETTE : la requête,
// le titre, la recherche, les onglets avec compteurs, « + Créer » — et il monte LA cartouche
// de l'onglet actif. Toucher une cartouche ne peut pas en abîmer une autre.
//
// État serveur : React Query, LOCAL à ce sous-ensemble (décision de chantier — le reste de
// l'appli migrera dans un chantier dédié). La liste n'est JAMAIS patchée à la main : toute
// écriture invalide la requête et la base est relue. Ne lit QUE les tables neuves du monde
// Mes contenus — jamais l'ancien monde.
import { useEffect, useMemo, useState } from 'react'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import { filtrer, IconActiviteType, IconSeanceType, IconSequenceType } from './contenus/commun.jsx'
import OngletTout from './contenus/OngletTout.jsx'
import OngletSequences from './contenus/OngletSequences.jsx'
import OngletSeances from './contenus/OngletSeances.jsx'
import OngletActivites from './contenus/OngletActivites.jsx'

const IconSearch = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)

const ONGLETS = [
  ['tout', 'Tout', 'tout'],
  ['sequence', 'Séquences', 'sequences'],
  ['seance', 'Séances', 'seances'],
  ['activite', 'Activités', 'activites'],
]

function EcranMesContenus({ onNavigate, onOuvrirSeance, onOuvrirActivite, email }) {
  const [onglet, setOnglet] = useState('tout')
  const [recherche, setRecherche] = useState('')
  const [menuCreer, setMenuCreer] = useState(false)

  // LA source de vérité : la base, relue par React Query (jamais de liste patchée à la main).
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['mes-contenus'],
    queryFn: async () => lireReponse(await apiFetch('/api/mes-contenus', {}, TIMEOUT_STD)),
  })

  // RÈGLE MAISON : tout message d'erreur passe par la BOÎTE DE DIALOGUE (showError), jamais
  // en texte posé dans l'écran. L'écran ne garde qu'un bouton « Réessayer ».
  useEffect(() => {
    if (isError) showError(messagePourEcran(error))
  }, [isError, error])

  const contenus = data?.contenus || []
  const compteurs = data?.compteurs || { tout: 0, sequences: 0, seances: 0, activites: 0 }

  // La recherche s'applique AVANT la cartouche : chaque onglet reçoit sa liste déjà filtrée.
  const visibles = useMemo(() => filtrer(contenus, recherche), [contenus, recherche])

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* En-tête : titre + recherche */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', flexShrink: 0 }}>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: '#1e293b', margin: 0 }}>Mes contenus</h2>
        <div style={{ position: 'relative' }}>
          <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', display: 'inline-flex' }}><IconSearch /></span>
          <input
            type="search"
            value={recherche}
            onChange={e => setRecherche(e.target.value)}
            placeholder="Rechercher…"
            title="Rechercher dans vos contenus (titre, matière, niveau, type)"
            style={{ padding: '7px 12px 7px 30px', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 13, width: 220, background: '#fff' }}
          />
        </div>
      </div>

      {/* Onglets avec compteurs + « Créer » */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', flexShrink: 0 }}>
        <div style={{ display: 'inline-flex', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden', background: '#fff' }}>
          {ONGLETS.map(([id, label, cle], i) => (
            <button
              key={id}
              type="button"
              onClick={() => setOnglet(id)}
              title={`Afficher : ${label.toLowerCase()}`}
              style={{
                padding: '7px 14px', fontSize: 13, border: 'none', cursor: 'pointer',
                borderLeft: i > 0 ? '1px solid #e2e8f0' : 'none',
                background: onglet === id ? 'var(--bordeaux)' : '#fff',
                color: onglet === id ? '#fff' : '#475569',
                fontWeight: onglet === id ? 600 : 400,
              }}
            >
              {label} ({compteurs[cle]})
            </button>
          ))}
        </div>

        <div style={{ position: 'relative' }}>
          <button
            type="button"
            onClick={() => setMenuCreer(o => !o)}
            title="Créer un nouveau contenu"
            style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Créer
          </button>
          {menuCreer && (
            <>
              {/* voile invisible : un clic ailleurs referme le menu */}
              <div style={{ position: 'fixed', inset: 0, zIndex: 40 }} onClick={() => setMenuCreer(false)} />
              <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 6px)', zIndex: 41, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, boxShadow: '0 8px 24px rgba(0,0,0,0.12)', minWidth: 200, padding: 6, display: 'flex', flexDirection: 'column' }}>
                <button
                  type="button"
                  onClick={() => { setMenuCreer(false); onOuvrirActivite(null) }}
                  title="Créer une activité (monde Mes contenus — règle 0, enregistrement automatique)"
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', fontSize: 13, color: '#1e293b', background: 'none', border: 'none', borderRadius: 6, cursor: 'pointer', textAlign: 'left' }}
                >
                  <IconActiviteType size={15} /> Une activité
                </button>
                <button
                  type="button"
                  onClick={() => { setMenuCreer(false); onOuvrirSeance(null) }}
                  title="Créer une séance (monde Mes contenus — règle 0, enregistrement automatique)"
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', fontSize: 13, color: '#1e293b', background: 'none', border: 'none', borderRadius: 6, cursor: 'pointer', textAlign: 'left' }}
                >
                  <IconSeanceType size={15} /> Une séance
                </button>
                <span title="Bientôt — la séquence (conteneur de séances) arrive avec les prochaines briques" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', fontSize: 13, color: '#b4bac3', cursor: 'not-allowed' }}>
                  <IconSequenceType size={15} /> Une séquence
                  <span style={{ marginLeft: 'auto', fontSize: 9, fontWeight: 600, color: '#94a3b8', background: '#f1f5f9', borderRadius: 99, padding: '1px 6px' }}>bientôt</span>
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* LA cartouche de l'onglet actif — remontée à neuf à chaque changement d'onglet
          (key) : chaque onglet garde SES états chez lui, rien ne fuit de l'un à l'autre. */}
      {isLoading && (
        <p style={{ fontSize: 13, color: '#64748b', textAlign: 'center', padding: '28px 16px', margin: 0 }}>Chargement de vos contenus…</p>
      )}
      {isError && (
        <div style={{ textAlign: 'center', padding: '28px 16px' }}>
          <button type="button" className="btn-secondary" onClick={() => refetch()} title="Recharger vos contenus">
            Réessayer
          </button>
        </div>
      )}
      {!isLoading && !isError && contenus.length === 0 && (
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, textAlign: 'center', padding: '32px 16px' }}>
          <p style={{ fontSize: 13.5, color: '#475569', margin: '0 0 4px', fontWeight: 600 }}>Votre bibliothèque est vide pour l'instant.</p>
          <p style={{ fontSize: 12.5, color: '#94a3b8', margin: 0 }}>Vos activités, séances et séquences apparaîtront ici.</p>
        </div>
      )}
      {!isLoading && !isError && contenus.length > 0 && (
        <>
          {onglet === 'tout' && (
            <OngletTout key="tout" contenus={visibles} email={email}
              onOuvrirSeance={onOuvrirSeance} onOuvrirActivite={onOuvrirActivite} />
          )}
          {onglet === 'sequence' && (
            <OngletSequences key="sequence" sequences={visibles.filter(c => c.type === 'sequence')} />
          )}
          {onglet === 'seance' && (
            <OngletSeances key="seance" seances={visibles.filter(c => c.type === 'seance')}
              onOuvrirSeance={onOuvrirSeance} />
          )}
          {onglet === 'activite' && (
            <OngletActivites key="activite" activites={visibles.filter(c => c.type === 'activite')}
              email={email} onOuvrirActivite={onOuvrirActivite} />
          )}
        </>
      )}

    </div>
  )
}

// React Query volontairement LOCAL au sous-ensemble « Mes contenus » : un client dédié ici,
// pas de provider global — le reste de l'appli migrera dans le chantier React Query dédié.
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

export default function MesContenus({ onNavigate, onOuvrirSeance, onOuvrirActivite, email }) {
  return (
    <QueryClientProvider client={queryClient}>
      <EcranMesContenus onNavigate={onNavigate} onOuvrirSeance={onOuvrirSeance} onOuvrirActivite={onOuvrirActivite} email={email} />
    </QueryClientProvider>
  )
}
