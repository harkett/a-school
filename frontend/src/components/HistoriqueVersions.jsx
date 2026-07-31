// « Historique des versions » — la moitié LECTURE de la règle 0, partagée par l'écran Activité
// et l'écran Séance (mêmes endpoints, mêmes gestes : une seule fenêtre, deux appelants).
//
// Ce que le prof y fait : il relit les versions empilées par chaque jalon (génération, retour
// à une version précédente), en ouvre une pour la lire en entier, et peut y REVENIR. Revenir
// n'efface rien : la version restaurée redevient l'état courant ET s'empile à son tour — la
// version qu'on quitte reste dans la liste, on peut donc revenir en arrière d'un retour en
// arrière (c'est ce que promettent les infobulles « L'ancienne version reste dans l'historique »).
//
// Contrat d'appel :
//  - base       : '/api/contenus/activites/12' ou '/api/contenus/seances/7' (le serveur vérifie
//                 l'appartenance : un contenu qui n'est pas à soi = 404) ;
//  - variante   : 'ton' (activité) ou 'style' (séance) — le nom du champ qui accompagne la version ;
//  - onRestaure : reçoit la réponse du serveur ({ resultat, ton|style }) pour que l'écran
//                 appelant remette son affichage sur l'état courant tout juste restauré ;
//  - aide       : l'entrée « i » de l'écran appelant (facultative).
import { useState, useEffect, useCallback } from 'react'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import InfoGuide from './InfoGuide.jsx'

const LIBELLE_VARIANTE = {
  academique: 'Ton académique',
  operationnel: 'Ton opérationnel',
}

// Date lisible par un prof : « 31 juillet 2026 à 14:05 ».
function dateLisible(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
    + ' à ' + d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

export default function HistoriqueVersions({ base, variante = 'ton', titre, aide, onFermer, onRestaure }) {
  const [versions, setVersions] = useState(null)      // null = chargement en cours
  const [chargementRate, setChargementRate] = useState(false)
  const [choisie, setChoisie] = useState(null)        // id de la version ouverte à droite
  const [contenu, setContenu] = useState(null)        // { resultat, … } de la version ouverte
  const [contenuRate, setContenuRate] = useState(false)
  const [restauration, setRestauration] = useState(null)   // version en attente de confirmation
  const [enCours, setEnCours] = useState(false)

  const charger = useCallback(async () => {
    setChargementRate(false)
    try {
      const d = await lireReponse(await apiFetch(`${base}/versions`, {}, TIMEOUT_STD))
      setVersions(d.versions || [])
    } catch (e) {
      setChargementRate(true)
      showError(messagePourEcran(e))
    }
  }, [base])

  useEffect(() => { charger() }, [charger])

  // Échap ferme la fenêtre (même geste que les autres modales de l'appli).
  useEffect(() => {
    const onEsc = e => { if (e.key === 'Escape') onFermer() }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [onFermer])

  // Ouvrir une version = lire son contenu COMPLET (la liste, elle, ne porte qu'un extrait).
  async function ouvrir(version) {
    setChoisie(version.id)
    setContenu(null)
    setContenuRate(false)
    try {
      setContenu(await lireReponse(await apiFetch(`${base}/versions/${version.id}`, {}, TIMEOUT_STD)))
    } catch (e) {
      setContenuRate(true)
      showError(messagePourEcran(e))
    }
  }

  // Restaurer : on demande d'abord, en disant ce qui se passe vraiment (rien n'est perdu).
  async function restaurer(version) {
    setEnCours(true)
    try {
      const d = await lireReponse(await apiFetch(
        `${base}/versions/${version.id}/restaurer`, { method: 'POST' }, TIMEOUT_STD))
      setRestauration(null)
      onRestaure(d)
      await charger()          // la restauration vient elle-même d'empiler une version
      setChoisie(null)
      setContenu(null)
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setEnCours(false)
    }
  }

  const versionChoisie = versions?.find(v => v.id === choisie) || null

  return (
    <div
      onClick={e => { if (e.target === e.currentTarget) onFermer() }}
      style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(15,23,42,0.55)',
               display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
    >
      <div
        style={{ background: '#fff', borderRadius: 10, maxWidth: 900, width: '100%', maxHeight: '88vh',
                 display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}
      >
        {/* En-tête */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
                      padding: '14px 18px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, color: '#0f172a', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M3 3v5h5"/>
                <path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/>
                <polyline points="12 7 12 12 15 14"/>
              </svg>
              Historique des versions
              {aide && <InfoGuide {...aide} />}
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>
              {titre ? `${titre} — ` : ''}revenir à une version ne supprime rien : celle d'aujourd'hui reste dans la liste.
            </div>
          </div>
          <button type="button" onClick={onFermer} title="Fermer l'historique"
            style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff',
                     color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                     cursor: 'pointer', padding: 0, flexShrink: 0 }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* Corps : la liste à gauche, la version ouverte à droite */}
        <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
          <div style={{ width: 320, flexShrink: 0, borderRight: '1px solid #e2e8f0', overflowY: 'auto' }}>
            {chargementRate ? (
              <div style={{ padding: 20, textAlign: 'center' }}>
                <button type="button" onClick={charger} className="btn-primary" title="Recharger l'historique">
                  Réessayer
                </button>
              </div>
            ) : versions === null ? (
              <p style={{ padding: 20, fontSize: 13, color: '#94a3b8' }}>Chargement…</p>
            ) : versions.length === 0 ? (
              <p style={{ padding: 20, fontSize: 13, color: '#94a3b8' }}>
                Aucune version pour l'instant — la première génération en fige une.
              </p>
            ) : versions.map((v, i) => (
              <button
                key={v.id}
                type="button"
                onClick={() => ouvrir(v)}
                title={v.courante ? "C'est la version actuellement affichée" : 'Lire cette version'}
                style={{
                  display: 'block', width: '100%', textAlign: 'left', cursor: 'pointer',
                  border: 'none', borderBottom: i === versions.length - 1 ? 'none' : '1px solid #f1f5f9',
                  borderLeft: choisie === v.id ? '3px solid var(--bordeaux)' : '3px solid transparent',
                  background: choisie === v.id ? '#fdf2f4' : '#fff',
                  padding: '11px 14px', font: 'inherit',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#1e293b' }}>{v.jalon_label}</span>
                  {v.courante && (
                    <span style={{ fontSize: 10, fontWeight: 700, color: '#166534', background: '#dcfce7',
                                   border: '1px solid #86efac', borderRadius: 99, padding: '1px 7px' }}>
                      Version actuelle
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                  {dateLisible(v.created_at)}
                  {v[variante] ? ` · ${LIBELLE_VARIANTE[v[variante]] || v[variante]}` : ''}
                </div>
                <div style={{ fontSize: 11, color: '#64748b', marginTop: 4, overflow: 'hidden',
                              textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {v.extrait}
                </div>
              </button>
            ))}
          </div>

          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
            {!versionChoisie ? (
              <div style={{ margin: 'auto', color: '#94a3b8', fontSize: 13, padding: 24, textAlign: 'center' }}>
                Cliquez une version à gauche pour la lire.
              </div>
            ) : (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                              padding: '12px 18px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>{versionChoisie.jalon_label}</div>
                    <div style={{ fontSize: 11, color: '#94a3b8' }}>{dateLisible(versionChoisie.created_at)}</div>
                  </div>
                  {versionChoisie.courante ? (
                    <span style={{ fontSize: 12, color: '#94a3b8', flexShrink: 0 }}>Déjà affichée</span>
                  ) : (
                    <button type="button" className="btn-primary" style={{ flexShrink: 0 }}
                      onClick={() => setRestauration(versionChoisie)}
                      title="Remettre cette version en place — la version actuelle restera dans l'historique">
                      Revenir à cette version
                    </button>
                  )}
                </div>
                <div style={{ flex: 1, overflowY: 'auto', padding: '16px 18px' }}>
                  {contenuRate ? (
                    <button type="button" onClick={() => ouvrir(versionChoisie)} className="btn-primary"
                      title="Recharger cette version">
                      Réessayer
                    </button>
                  ) : contenu === null ? (
                    <p style={{ fontSize: 13, color: '#94a3b8' }}>Chargement…</p>
                  ) : (
                    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13,
                                  color: '#374151', lineHeight: 1.7, margin: 0, fontFamily: 'inherit' }}>
                      {contenu.resultat}
                    </pre>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation — dit ce qui se passe VRAIMENT : rien n'est perdu. */}
      {restauration && (
        <div
          onClick={e => e.stopPropagation()}
          style={{ position: 'fixed', inset: 0, zIndex: 2100, background: 'rgba(15,23,42,0.45)',
                   display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
        >
          <div style={{ background: '#fff', borderRadius: 10, padding: '24px 28px', maxWidth: 460, width: '90%',
                        boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 10, color: '#1e293b' }}>
              Revenir à cette version ?
            </div>
            <p style={{ fontSize: 13.5, color: '#374151', margin: '0 0 18px', lineHeight: 1.6 }}>
              La version du <strong>{dateLisible(restauration.created_at)}</strong> redevient celle de
              votre {variante === 'style' ? 'séance' : 'activité'}. Rien n'est supprimé : la version
              actuelle reste dans l'historique, vous pourrez y retourner.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button type="button" className="btn-secondary" disabled={enCours}
                onClick={() => setRestauration(null)} title="Annuler — ne rien changer">
                Annuler
              </button>
              <button type="button" className="btn-primary" disabled={enCours}
                onClick={() => restaurer(restauration)} title="Remettre cette version en place">
                {enCours ? 'Restauration…' : 'Revenir à cette version'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
