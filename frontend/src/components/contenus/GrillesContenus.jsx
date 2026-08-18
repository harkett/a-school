// Page « Mes évals → Grilles » — la LISTE, au moule des trois pages de Mes contenus
// (ActivitesContenus, SeancesContenus, SequencesContenus) : deux onglets « Niveau en cours » /
// « Toutes mes grilles », regroupement par couple matière × niveau, deux colonnes
// redimensionnables (liste à gauche, détail à droite) et le bouton qui escamote le détail.
//
// LA CRÉATION N'EST PAS ICI. « Nouvelle grille » ouvre un ÉCRAN — la liste disparaît, comme
// « Nouvelle activité » fait disparaître la liste des activités. Le formulaire a d'abord été
// posé en tête de cette page : il repoussait les grilles vers le bas à chaque visite, et ça ne
// se fait nulle part dans la maison.
//
// LE DÉTAIL EST EN LECTURE, comme celui d'une activité montre son résultat sans l'éditer : il
// affiche le TABLEAU de la grille choisie, et « Ouvrir » l'ouvre dans l'éditeur (GrilleEcran) —
// exactement le geste de « Reprendre » sur une activité.
//
// IL N'Y A PAS DE RECHERCHE, et ce n'est pas un oubli : aucune des trois pages voisines n'en a.
// En poser une ici ferait de la quatrième liste la seule à se lire autrement.
//
// LA LISTE NE CHARGE PAS LES CASES : /api/contenus/grilles rend un titre, un couple et deux
// compteurs par ligne. Le tableau complet n'est lu QUE pour la grille choisie, à la demande.
import { useCallback, useEffect, useState } from 'react'
import InfoGuide from '../InfoGuide.jsx'
import SplitPane from '../SplitPane.jsx'
import { aideGrilles } from '../../utils/aideGrilles.js'
import { astucesEcran } from '../../utils/astuces.js'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../../utils/api.js'
import { showError } from '../../errorDialog.js'
import { coupleKey, correspondProfil, formatDateActivite, grouperParCouple } from '../../utils/activites.js'
import { TYPES_CONTENUS } from '../../utils/typesContenus.js'
import { IconGrille } from '../icones.jsx'

// Les astuces de cet écran, lues une fois (catalogue figé) : le « a » ne bouge pas d'un rendu à
// l'autre. Même branchement que les trois pages voisines.
const astucesContenus = astucesEcran('contenus')

// Identité du type Grille (bleu ardoise) — fichier commun, appliquée en petites touches : icône
// du titre, pastille compteur, onglet actif, liseré de la ligne choisie.
const TYPE_GRI = TYPES_CONTENUS.grille

const LABEL_STYLE = {
  fontSize: 11, fontWeight: 600, color: '#94a3b8',
  textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8,
}


export default function GrillesContenus({ onOuvrirGrille, onNouvelleGrille, sessionMatiere, sessionNiveau }) {
  const [grilles, setGrilles] = useState(null)
  const [chargementRate, setChargementRate] = useState(false)
  const [choisie, setChoisie] = useState(null)          // id CLIQUÉ dans la liste
  const [tableau, setTableau] = useState(null)          // la grille choisie, EN ENTIER
  const [vue, setVue] = useState('courant')             // 'courant' | 'toutes'
  const [detailCache, setDetailCache] = useState(false)

  const charger = useCallback(async () => {
    try {
      const res = await apiFetch('/api/contenus/grilles', {}, TIMEOUT_STD)
      setGrilles(await lireReponse(res))
      setChargementRate(false)
    } catch (e) {
      showError(messagePourEcran(e))
      setGrilles([])
      setChargementRate(true)
    }
  }, [])

  useEffect(() => { charger() }, [charger])

  // Le TABLEAU de la grille choisie, lu à la demande. La liste ne le porte pas : afficher trente
  // descripteurs par ligne serait payé à chaque ouverture de la page, pour une seule qu'on lit.
  //
  // `vivant` : si le professeur clique une deuxième grille avant que la première soit revenue,
  // la réponse en retard ne doit pas écraser la bonne.
  useEffect(() => {
    if (!choisie) { setTableau(null); return }
    let vivant = true
    ;(async () => {
      try {
        const res = await apiFetch(`/api/contenus/grilles/${choisie}`, {}, TIMEOUT_STD)
        const d = await lireReponse(res)
        if (vivant) setTableau(d)
      } catch (e) {
        if (vivant) { setTableau(null); showError(messagePourEcran(e)) }
      }
    })()
    return () => { vivant = false }
  }, [choisie])

  const toutes = grilles || []
  const duCouple = toutes.filter(g => correspondProfil(g, sessionMatiere, sessionNiveau))
  const sections = vue === 'toutes'
    ? grouperParCouple(toutes, coupleKey(sessionMatiere, sessionNiveau))
    : null
  const labelProfil = [sessionMatiere, sessionNiveau].filter(Boolean).join(' — ')

  // ── Une ligne de la liste ──
  const ligne = (g) => (
    <button
      key={g.id}
      type="button"
      onClick={() => setChoisie(g.id)}
      onDoubleClick={() => onOuvrirGrille(g.id)}
      title={`${g.titre} — cliquez pour la lire, double-cliquez pour l'ouvrir`}
      style={{
        textAlign: 'left', background: '#fff', cursor: 'pointer', fontFamily: 'inherit',
        border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 14px',
        borderLeft: `3px solid ${choisie === g.id ? TYPE_GRI.accent : 'transparent'}`,
        display: 'flex', alignItems: 'center', gap: 12, width: '100%',
      }}
    >
      <IconGrille taille={16} couleur={TYPE_GRI.accent} />
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#1e293b',
                       overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {g.titre}
        </span>
        <span style={{ display: 'block', fontSize: 11.5, color: '#94a3b8', marginTop: 2 }}>
          {g.nb_criteres} critère{g.nb_criteres > 1 ? 's' : ''} ×{' '}
          {g.nb_niveaux} niveau{g.nb_niveaux > 1 ? 'x' : ''} de maîtrise
        </span>
      </span>
      <span style={{ fontSize: 11.5, color: '#cbd5e1', whiteSpace: 'nowrap' }}>
        {formatDateActivite(g.updated_at).court}
      </span>
    </button>
  )

  const colonneListe = (
    <div style={{ padding: '4px 4px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
      {vue === 'courant' && duCouple.length === 0 && (
        <p className="text-sm text-gray-400 py-4">
          Aucune grille en {labelProfil || 'ce couple'} — l'onglet « Toutes mes grilles » montre le reste.
        </p>
      )}
      {vue === 'courant' && duCouple.map(ligne)}
      {vue === 'toutes' && sections.map(s => (
        <div key={s.key} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ ...LABEL_STYLE, marginBottom: 0, marginTop: 6 }}>{s.label}</div>
          {s.items.map(ligne)}
        </div>
      ))}
    </div>
  )

  // ── La colonne de détail : LE TABLEAU, en lecture ──
  const colonnes = tableau?.niveaux_maitrise || []
  const lignes = tableau?.criteres || []

  const colonneDetail = (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      {!tableau ? (
        <p className="text-sm text-gray-400" style={{ padding: '18px 22px' }}>
          {choisie ? 'Lecture…' : 'Choisissez une grille pour en voir le détail.'}
        </p>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
                        padding: '14px 22px', borderBottom: '1px solid #f1f5f9', flexShrink: 0 }}>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
              {tableau.titre}
            </h3>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              {[tableau.matiere, tableau.niveau].filter(Boolean).join(' — ')}
            </span>
            {/* Le geste de « Reprendre » sur une activité : le détail LIT, l'éditeur MODIFIE. */}
            <button
              type="button"
              className="btn-primary"
              onClick={() => onOuvrirGrille(tableau.id)}
              title="Ouvrir cette grille dans l'éditeur (modifier, imprimer, exporter, dupliquer)"
              style={{ marginLeft: 'auto' }}
            >
              Ouvrir
            </button>
          </div>

          <div style={{ flex: 1, overflow: 'auto', padding: '16px 22px', minHeight: 0 }}>
            {tableau.contexte && (
              <div style={{ marginBottom: 14 }}>
                <div style={LABEL_STYLE}>Ce que vous évaluez</div>
                <p style={{ margin: 0, fontSize: 13, color: '#64748b', fontStyle: 'italic',
                            lineHeight: 1.6, background: '#f8fafc', border: '1px solid #e2e8f0',
                            borderRadius: 6, padding: '10px 14px', whiteSpace: 'pre-wrap' }}>
                  {tableau.contexte}
                </p>
              </div>
            )}

            <div style={LABEL_STYLE}>Le tableau</div>
            {/* Le tableau défile DANS SON CADRE, jamais la page. */}
            <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 8,
                          background: '#fff' }}>
              <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 560 }}>
                <thead>
                  <tr>
                    <th style={{ border: '1px solid #e2e8f0', background: '#f8fafc', padding: '6px 8px',
                                 textAlign: 'left', minWidth: 140, ...LABEL_STYLE, marginBottom: 0 }}>
                      Critère
                    </th>
                    {colonnes.map(n => (
                      <th key={n.id} style={{ border: '1px solid #e2e8f0', background: '#f8fafc',
                                              padding: '6px 8px', textAlign: 'left', minWidth: 130,
                                              verticalAlign: 'top' }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: '#1e293b' }}>{n.libelle}</div>
                        <div style={{ fontSize: 11, color: '#94a3b8' }}>{n.points} pt</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {lignes.map(c => (
                    <tr key={c.id}>
                      <th style={{ border: '1px solid #e2e8f0', background: '#fcfcfd', padding: '6px 8px',
                                   textAlign: 'left', verticalAlign: 'top' }}>
                        <div style={{ fontSize: 12.5, fontWeight: 600, color: '#1e293b' }}>
                          {c.libelle || <span style={{ color: '#cbd5e1' }}>(sans titre)</span>}
                        </div>
                        {Number(c.poids) !== 1 && (
                          <div style={{ fontSize: 11, color: '#94a3b8' }}>poids × {c.poids}</div>
                        )}
                      </th>
                      {colonnes.map(n => (
                        <td key={n.id} style={{ border: '1px solid #e2e8f0', padding: '6px 8px',
                                                verticalAlign: 'top', fontSize: 12, color: '#374151',
                                                lineHeight: 1.5 }}>
                          {(c.descripteurs || {})[String(n.id)] || ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p style={{ marginTop: 12, marginBottom: 0, fontSize: 12, color: '#94a3b8' }}>
              Dernière modification : {formatDateActivite(tableau.updated_at).complet}
            </p>
          </div>
        </>
      )}
    </div>
  )

  return (
    <div className="flex flex-col flex-1 min-h-0 w-full gap-3">

      {/* En-tête — même motif que les trois pages voisines. */}
      <div className="flex items-center gap-3" style={{ flexShrink: 0, justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div className="flex items-baseline gap-3">
          <h2 className="text-lg font-semibold text-gray-800" style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
            <IconGrille couleur={TYPE_GRI.accent} />
            Grilles
            <InfoGuide {...aideGrilles('descripteur')} />
            {astucesContenus && <InfoGuide {...astucesContenus} />}
          </h2>
          {toutes.length > 0 && (
            <span style={{ fontSize: 12, color: TYPE_GRI.accent, background: TYPE_GRI.fond, border: `1px solid ${TYPE_GRI.bord}`, borderRadius: 99, padding: '1px 10px', fontWeight: 600 }}>
              {toutes.length} grille{toutes.length > 1 ? 's' : ''} créée{toutes.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onNouvelleGrille}
          title="Écrire une nouvelle grille d'évaluation"
          style={{ background: 'var(--bleu)', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 6 }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Nouvelle grille
        </button>
      </div>

      {/* Onglets — visibles dès qu'il y a au moins une grille */}
      {toutes.length > 0 && (
        <div style={{ display: 'flex', gap: 2, borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
          {[['courant', 'Niveau en cours'], ['toutes', 'Toutes mes grilles']].map(([id, label]) => (
            <button
              key={id}
              onClick={() => setVue(id)}
              title={id === 'courant'
                ? (labelProfil ? `Vos grilles en ${labelProfil}` : 'Les grilles de votre matière et niveau actuels')
                : 'Toutes vos grilles, regroupées par matière et niveau'}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 13, padding: '6px 12px', marginBottom: -1,
                color: vue === id ? TYPE_GRI.accent : '#6b7280',
                fontWeight: vue === id ? 600 : 400,
                borderBottom: vue === id ? `2px solid ${TYPE_GRI.accent}` : '2px solid transparent',
              }}
            >
              {label}{id === 'toutes' ? ` (${toutes.length})` : ''}
            </button>
          ))}
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setDetailCache(c => !c)}
            title={detailCache
              ? 'Réafficher la colonne de détail à droite'
              : 'Cacher la colonne de détail — la liste prend toute la largeur'}
            style={{ marginLeft: 'auto', alignSelf: 'center', flexShrink: 0 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {detailCache
                ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
            </svg>
            {detailCache ? 'Afficher le détail' : 'Cacher le détail'}
          </button>
        </div>
      )}

      {grilles === null && <p className="text-sm text-gray-400 py-4">Chargement…</p>}

      {/* Lecture ratée : jamais « Aucune grille ». Le message est déjà parti en boîte de dialogue
          (règle maison) — l'écran ne garde que le bouton pour relancer. */}
      {grilles !== null && chargementRate && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <button onClick={charger} className="btn-primary" title="Recharger vos grilles">
            Réessayer
          </button>
        </div>
      )}

      {grilles !== null && !chargementRate && toutes.length === 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-10 text-center">
          <p className="text-sm text-gray-500">Aucune grille pour l'instant.</p>
          <p className="text-xs text-gray-400 mt-1">Créez votre première grille avec le bouton « Nouvelle grille ».</p>
        </div>
      )}

      {/* Deux colonnes redimensionnables : liste à gauche | détail à droite. */}
      {grilles !== null && toutes.length > 0 && (
        <div style={{ flex: 1, minHeight: 0 }}>
          {detailCache
            ? <div className="split-pane"><div className="split-col split-col-flex">{colonneListe}</div></div>
            : <SplitPane storageKey="eval-grilles-split-v1" defautGauche={44} gauche={colonneListe} droite={colonneDetail} />}
        </div>
      )}
    </div>
  )
}
