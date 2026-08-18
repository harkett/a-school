import { useEffect, useRef, useState } from 'react'

// ============================================================================================
// LA FENÊTRE DE RECETTE — ce qui se passe quand on coche une note du carnet.
//
// LA RÈGLE QU'ELLE APPLIQUE : une tâche ne devient « faite » que si la recette est verte. On ne
// demande donc l'avis de personne — cocher LANCE. La fenêtre annonce, montre l'avancement, puis
// donne le résultat. Un seul bouton, à la fin.
//
// ELLE NE SE FERME PAS PENDANT. Ni croix, ni Échap, ni clic dehors : c'est ce sondage-ci qui
// fait écrire le verdict dans la note (le backend le pose à la première réponse « terminé »).
// Fermer en route laisserait le passage sans lecteur — la note resterait à faire, ce qui est
// l'état sûr, mais on aurait attendu trois minutes pour rien.
//
// MÊME BOÎTE que ConfirmDialog et ErrorDialog : voile sombre, carte blanche, barre de titre avec
// pictogramme, pied sur fond doux et bouton à droite. Ce qui change ici, c'est le corps — il
// raconte trois moments différents.
// ============================================================================================

const SONDAGE_MS = 1200

// Les animations, écrites une fois. Une jauge qui saute d'un coup de 20 % à 40 % donne
// l'impression que la machine hoquette ; la même transition en 400 ms donne l'impression qu'elle
// travaille. C'est toute la différence entre un écran d'amateur et un écran de métier.
const ANIMATIONS = `
@keyframes recetteEntree  { from { opacity: 0; transform: translateY(12px) scale(0.97); }
                              to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes recetteVoile   { from { opacity: 0; } to { opacity: 1; } }
@keyframes recetteSablier { 0%, 45% { transform: rotate(0deg); }
                            55%, 100% { transform: rotate(180deg); } }
@keyframes recetteNavette { 0% { margin-left: -35%; } 100% { margin-left: 100%; } }
@keyframes recetteTrace   { from { stroke-dashoffset: 32; } to { stroke-dashoffset: 0; } }
@keyframes recettePouls   { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }
`

function Sablier() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--bleu)" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"
         style={{ flexShrink: 0, animation: 'recetteSablier 2.4s ease-in-out infinite' }}>
      <path d="M5 22h14M5 2h14M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22" />
      <path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2" />
    </svg>
  )
}

function Pastille({ couleur, fond, children }) {
  return (
    <div style={{ width: 52, height: 52, borderRadius: '50%', background: fond, color: couleur,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      {children}
    </div>
  )
}

function Coche() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 6 9 17l-5-5" strokeDasharray="32"
            style={{ animation: 'recetteTrace 0.5s ease-out forwards' }} />
    </svg>
  )
}

function Croix() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6"
         strokeLinecap="round" aria-hidden="true">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  )
}

// LA JAUGE. Tant que Playwright n'a pas annoncé combien de scénarios il va jouer, on ne connaît
// pas la fin : c'est une navette qui va et vient — jamais un pourcentage inventé. Dès que le
// total est connu, elle devient une vraie jauge qui se remplit.
function Jauge({ faits, total }) {
  const connu = total > 0
  const part = connu ? Math.min(100, Math.round((faits / total) * 100)) : 0
  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                    fontSize: 12, color: '#64748b', marginBottom: 6 }}>
        <span>{connu ? `${faits} scénario${faits > 1 ? 's' : ''} sur ${total}` : 'Préparation'}</span>
        {connu && <span style={{ fontWeight: 700, color: 'var(--bleu)', fontSize: 13 }}>{part} %</span>}
      </div>
      <div style={{ height: 8, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
        {connu ? (
          <div style={{ height: '100%', width: `${part}%`, borderRadius: 999,
                        background: 'linear-gradient(90deg, #3b82f6, #2563eb)',
                        transition: 'width 400ms ease-out' }} />
        ) : (
          <div style={{ height: '100%', width: '35%', borderRadius: 999, background: '#93c5fd',
                        animation: 'recetteNavette 1.6s linear infinite' }} />
        )}
      </div>
    </div>
  )
}

export default function FenetreRecette({ tacheId, titre, onFini }) {
  const [etat, setEtat] = useState(null)
  const [erreur, setErreur] = useState(null)
  const [secondes, setSecondes] = useState(0)
  const boutonRef = useRef(null)
  const arretRef = useRef(false)

  // LE PASSAGE. On lance, puis on sonde. Le backend écrit le verdict dans la note au moment où
  // il le lit — ce sondage n'est donc pas qu'un affichage, c'est lui qui clôt l'affaire.
  useEffect(() => {
    arretRef.current = false
    let minuteur = null

    const sonder = async () => {
      if (arretRef.current) return
      try {
        const r = await fetch(`/api/admin/taches-a-faire/${tacheId}/recette`, { credentials: 'include' })
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || 'Le suivi ne répond pas.')
        const e = await r.json()
        if (arretRef.current) return
        setEtat(e)
        if (e.enCours) minuteur = setTimeout(sonder, SONDAGE_MS)
      } catch (err) {
        if (!arretRef.current) setErreur(err.message)
      }
    }

    ;(async () => {
      try {
        const r = await fetch(`/api/admin/taches-a-faire/${tacheId}/recette`, {
          method: 'POST', credentials: 'include',
        })
        // UN PASSAGE DÉJÀ EN COURS N'EST PAS UN REFUS. Le lanceur n'en accepte qu'un à la fois —
        // deux navigateurs dans la même base se marchent dessus. Mais du point de vue de qui
        // regarde, une recette tourne : on s'y raccroche et on suit son avancement, au lieu de
        // renvoyer une porte fermée. C'est le même écran, la même jauge, le même verdict.
        if (r.status === 409) {
          if (arretRef.current) return
          minuteur = setTimeout(sonder, 0)
          return
        }
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || 'La recette n’a pas pu démarrer.')
        if (arretRef.current) return
        setEtat(await r.json())
        minuteur = setTimeout(sonder, SONDAGE_MS)
      } catch (err) {
        if (!arretRef.current) setErreur(err.message)
      }
    })()

    return () => { arretRef.current = true; clearTimeout(minuteur) }
  }, [tacheId])

  // Le compteur de secondes : il tourne tant qu'on attend. Sans lui, une fenêtre qui met trois
  // minutes ressemble à une fenêtre bloquée.
  const attente = !erreur && (!etat || etat.enCours)
  useEffect(() => {
    if (!attente) return
    const t = setInterval(() => setSecondes(s => s + 1), 1000)
    return () => clearInterval(t)
  }, [attente])

  // Le bouton prend le focus dès qu'il apparaît : Entrée ferme, comme dans toute boîte de la
  // maison. Échap ne fait rien tant que la recette tourne — il n'y a rien à annuler.
  useEffect(() => { if (!attente) boutonRef.current?.focus() }, [attente])
  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape' && !attente) onFini(etat?.tache) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [attente, etat, onFini])

  // « LA RECETTE A RATÉ » ET « ELLE N'A PAS TOURNÉ » SONT DEUX CHOSES. Ratée : elle a parcouru
  // l'application et quelque chose a lâché — la note reste à faire, et c'est mérité. Pas tournée :
  // le service était éteint, le réseau coupé, un passage occupait déjà la place — rien n'a été
  // parcouru, donc la note n'a rien fait de mal. Les confondre affichait « Recette à refaire »
  // sur un travail que personne n'avait regardé.
  const verdict = erreur ? null : etat?.verdict
  const fini = !attente
  const total = etat?.total || 0

  const bandeau = erreur
    ? { fond: '#fef2f2', bord: '#fecaca', couleur: '#dc2626', titre: 'La recette n’a pas pu tourner' }
    : verdict === 'verte'
      ? { fond: '#f0fdf4', bord: '#bbf7d0', couleur: '#16a34a', titre: 'Recette verte' }
      : verdict === 'ratee'
        ? { fond: '#fef2f2', bord: '#fecaca', couleur: '#dc2626', titre: 'Recette ratée' }
        : { fond: '#eff6ff', bord: '#bfdbfe', couleur: 'var(--bleu)', titre: 'Recette en cours' }

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-busy={attente}
      style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.55)',
               backdropFilter: 'blur(2px)', zIndex: 2200, display: 'flex', alignItems: 'center',
               justifyContent: 'center', padding: 16, animation: 'recetteVoile 180ms ease-out' }}
    >
      <style>{ANIMATIONS}</style>
      <div style={{ background: '#fff', borderRadius: 12, maxWidth: 520, width: '100%',
                    boxShadow: '0 24px 70px rgba(0,0,0,0.34)', overflow: 'hidden',
                    animation: 'recetteEntree 220ms cubic-bezier(0.16, 1, 0.3, 1)' }}>

        {/* ── Barre de titre. PAS DE CROIX : on ne ferme pas une recette en route, et une fois
               finie le bouton du pied est le seul geste qui reste. ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '13px 16px',
                      borderBottom: '1px solid #e2e8f0' }}>
          {attente ? <Sablier /> : (
            <span style={{ color: bandeau.couleur, display: 'flex' }}>
              {verdict === 'verte' ? <Coche /> : <Croix />}
            </span>
          )}
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a', flex: 1 }}>
            {bandeau.titre}
          </span>
          {attente && (
            <span style={{ fontSize: 12, color: '#64748b', fontVariantNumeric: 'tabular-nums' }}>
              {Math.floor(secondes / 60)}:{String(secondes % 60).padStart(2, '0')}
            </span>
          )}
        </div>

        <div style={{ padding: '18px 20px' }}>
          {/* La note concernée, toujours rappelée : la fenêtre couvre l'écran, on doit savoir sur
              quelle ligne on a cliqué. */}
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 14 }}>
            <span style={{ color: '#94a3b8' }}>Note&nbsp;:</span>{' '}
            <span style={{ color: '#0f172a', fontWeight: 600 }}>{titre}</span>
          </div>

          {/* ── 1. PENDANT — ce qu'elle fait, où elle en est ── */}
          {attente && (
            <>
              <div style={{ padding: '12px 14px', borderRadius: 10, fontSize: 13,
                            color: '#1e3a8a', lineHeight: 1.6,
                            background: bandeau.fond, border: `1px solid ${bandeau.bord}` }}>
                Un navigateur parcourt l’application comme un utilisateur : il se connecte, ouvre
                les écrans et vérifie ce qui s’affiche. La note ne sera cochée que si tout passe.
              </div>
              <Jauge faits={etat?.faits || 0} total={total} />
              <div style={{ marginTop: 12, fontSize: 13, color: '#475569',
                            display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--bleu)',
                               animation: 'recettePouls 1.4s ease-in-out infinite', flexShrink: 0 }} />
                {etat?.etape || 'Démarrage du navigateur'}
              </div>
            </>
          )}

          {/* ── 2. VERTE — ce qui a été parcouru, et ce que ça change ── */}
          {fini && verdict === 'verte' && (
            <div style={{ display: 'flex', gap: 14, alignItems: 'center', padding: '14px 16px',
                          borderRadius: 10, background: bandeau.fond, border: `1px solid ${bandeau.bord}` }}>
              <Pastille couleur="#16a34a" fond="#dcfce7"><Coche /></Pastille>
              <div style={{ fontSize: 14, color: '#14532d', lineHeight: 1.6 }}>
                <strong>{total} scénario{total > 1 ? 's' : ''} parcouru{total > 1 ? 's' : ''}, rien de cassé.</strong>
                <div style={{ marginTop: 4, color: '#166534' }}>La note passe dans « Faites ».</div>
              </div>
            </div>
          )}

          {/* ── 3. RATÉE, ou PAS TOURNÉ — deux fins rouges, deux sens différents. Ratée : la
                 recette a parcouru l'application et quelque chose a lâché. Pas tournée : elle
                 n'a rien parcouru du tout, et la note en ressort intacte. ── */}
          {fini && verdict !== 'verte' && (
            <>
              <div style={{ display: 'flex', gap: 14, alignItems: 'center', padding: '14px 16px',
                            borderRadius: 10, background: bandeau.fond, border: `1px solid ${bandeau.bord}` }}>
                <Pastille couleur="#dc2626" fond="#fee2e2"><Croix /></Pastille>
                <div style={{ fontSize: 14, color: '#7f1d1d', lineHeight: 1.6 }}>
                  {erreur ? (
                    <>
                      <strong>La recette n’a pas tourné.</strong>
                      <div style={{ marginTop: 4, color: '#991b1b' }}>
                        Rien n’a changé. La note est comme avant.
                      </div>
                    </>
                  ) : (
                    <>
                      <strong>La recette a raté.</strong>
                      <div style={{ marginTop: 4, color: '#991b1b' }}>
                        La note reste à faire, avec « Recette à refaire » en face.
                      </div>
                    </>
                  )}
                </div>
              </div>
              <div style={{ marginTop: 14 }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.4, color: '#94a3b8',
                              textTransform: 'uppercase', marginBottom: 6 }}>
                  {erreur ? 'Ce qui s’est passé' : 'Ce qui a lâché'}
                </div>
                <div style={{ padding: '11px 13px', borderRadius: 8, background: '#f8fafc',
                              border: '1px solid #e2e8f0', fontSize: 13, color: '#334155',
                              lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                  {erreur || etat?.detail || 'Aucun motif n’a été rapporté.'}
                </div>
              </div>
            </>
          )}
        </div>

        {/* ── Pied. Le bouton n'apparaît qu'à la fin : pendant, il n'y a rien à faire, et un
               bouton grisé qui attend trois minutes n'aide personne. ── */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 10,
                      padding: '12px 16px', borderTop: '1px solid #e2e8f0', background: '#f8fafc',
                      minHeight: 56 }}>
          {attente ? (
            <span style={{ fontSize: 12, color: '#94a3b8', marginRight: 'auto' }}>
              Vous pouvez laisser cette fenêtre ouverte, elle vous préviendra.
            </span>
          ) : (
            <button
              ref={boutonRef}
              type="button"
              onClick={() => onFini(etat?.tache)}
              title="Fermer et revenir au carnet"
              style={{ background: verdict === 'verte' ? '#16a34a' : 'var(--bleu)', color: '#fff',
                       border: 'none', borderRadius: 8, padding: '8px 28px', fontSize: 13,
                       fontWeight: 600, cursor: 'pointer' }}
            >
              OK
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
