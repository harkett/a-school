// Boîte de confirmation de suppression — partagée par les trois pages listes de Mes contenus.
//
// Elle ne récite pas un texte générique : elle DEMANDE D'ABORD AU SERVEUR ce que la suppression
// emporte (GET .../suppression), et annonce des nombres vrais, lus en base. C'est ce que veut la
// règle maison (« confirmation proportionnée à ce qui est détruit ») et c'est indispensable
// depuis que l'historique des versions est promis au prof : supprimer une activité emporte
// aussi ses versions, il doit le savoir AVANT de cliquer.
//
// Elle dit aussi ce qui SURVIT : supprimer une séance ou une séquence ne détruit jamais ce
// qu'elle contient (la base est en SET NULL) — les enfants repassent en « non rangés ».
//
// Échec serveur : le message part en boîte de dialogue (showError) et la fenêtre RESTE ouverte,
// la ligne reste à l'écran. Aucune disparition optimiste : le parent relit le serveur après un
// vrai succès (read-after-write).
import { useState, useEffect } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../../utils/api.js'
import { showError } from '../../errorDialog'

const ARTICLE = {
  activite: 'Cette activité',
  seance:   'Cette séance',
  sequence: 'Cette séquence',
}

// Ce que la suppression DÉTRUIT, en une phrase — construite sur les nombres du serveur.
function phraseDetruit(type, impact) {
  const nom = ARTICLE[type]
  if (impact.versions > 1) {
    return `${nom} et les ${impact.versions} versions de son historique seront supprimées définitivement.`
  }
  if (impact.versions === 1) {
    return `${nom} et la version de son historique seront supprimées définitivement.`
  }
  return `${nom} sera supprimée définitivement.`
}

// Ce que la suppression ÉPARGNE — pour ne pas laisser croire qu'on emporte l'étage du dessous.
function phraseEpargne(type, impact) {
  const nb = type === 'sequence' ? impact.seances_liberees : impact.activites_liberees
  if (!nb) return null
  const mot = type === 'sequence' ? 'séance' : 'activité'
  return nb > 1
    ? `Vos ${nb} ${mot}s ne seront pas supprimées : elles retourneront dans « non rangées ».`
    : `Votre ${mot} ne sera pas supprimée : elle retournera dans « non rangées ».`
}

export default function ConfirmerSuppression({ base, type, titre, onAnnuler, onSupprime }) {
  const [impact, setImpact] = useState(null)      // null = on demande encore au serveur
  const [impactRate, setImpactRate] = useState(false)
  const [enCours, setEnCours] = useState(false)

  useEffect(() => {
    let actif = true
    ;(async () => {
      try {
        const d = await lireReponse(await apiFetch(`${base}/suppression`, {}, TIMEOUT_STD))
        if (actif) setImpact(d)
      } catch (e) {
        if (!actif) return
        setImpactRate(true)
        showError(messagePourEcran(e))
      }
    })()
    return () => { actif = false }
  }, [base])

  // Échap annule (jamais l'inverse : la touche la plus proche ne doit pas détruire).
  useEffect(() => {
    const onEsc = e => { if (e.key === 'Escape' && !enCours) onAnnuler() }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [onAnnuler, enCours])

  async function supprimer() {
    setEnCours(true)
    try {
      await lireReponse(await apiFetch(base, { method: 'DELETE' }, TIMEOUT_STD))
      onSupprime()          // le parent relit la liste depuis le serveur
    } catch (e) {
      showError(messagePourEcran(e))   // la fenêtre reste ouverte, la ligne reste à l'écran
    } finally {
      setEnCours(false)
    }
  }

  const epargne = impact ? phraseEpargne(type, impact) : null

  return (
    <div
      onClick={e => { if (e.target === e.currentTarget && !enCours) onAnnuler() }}
      style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(15,23,42,0.5)',
               display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
    >
      <div style={{ background: '#fff', borderRadius: 10, padding: '24px 28px', maxWidth: 480,
                    width: '100%', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 10, color: '#1e293b' }}>
          Supprimer « {titre || 'ce contenu'} » ?
        </div>

        {impactRate ? (
          <p style={{ fontSize: 13.5, color: '#374151', margin: '0 0 18px', lineHeight: 1.6 }}>
            Impossible de vérifier ce que cette suppression emporte. Fermez et réessayez.
          </p>
        ) : impact === null ? (
          <p style={{ fontSize: 13.5, color: '#94a3b8', margin: '0 0 18px' }}>Vérification…</p>
        ) : (
          <div style={{ margin: '0 0 18px' }}>
            <p style={{ fontSize: 13.5, color: '#374151', margin: 0, lineHeight: 1.6 }}>
              {phraseDetruit(type, impact)}
            </p>
            {epargne && (
              <p style={{ fontSize: 13, color: '#166534', background: '#f0fdf4',
                          border: '1px solid #bbf7d0', borderRadius: 6, padding: '8px 12px',
                          margin: '12px 0 0', lineHeight: 1.55 }}>
                {epargne}
              </p>
            )}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button type="button" className="btn-secondary" disabled={enCours}
            onClick={onAnnuler} title="Annuler — ne rien supprimer">
            Annuler
          </button>
          <button
            type="button"
            disabled={enCours || impact === null}
            onClick={supprimer}
            title="Supprimer définitivement"
            style={{
              padding: '8px 18px', fontSize: 13, fontWeight: 600, borderRadius: 6, border: 'none',
              background: enCours || impact === null ? '#fca5a5' : '#b91c1c', color: '#fff',
              cursor: enCours || impact === null ? 'not-allowed' : 'pointer',
            }}
          >
            {enCours ? 'Suppression…' : 'Supprimer'}
          </button>
        </div>
      </div>
    </div>
  )
}
