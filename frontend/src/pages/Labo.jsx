// ── LABO — Paramètres de l'activité par COUPLE (matière + niveau) ────────────────────────
// Bac à sable : on prépare ici, avec les vrais get, le bloc « Paramètres de l'activité » de
// l'écran prof « Créer une activité ». BRIQUE 1 (lecture seule) : choisir un couple
// (cycle → niveau → matière), afficher le Type d'activité et sa Précision tels qu'ils sortent
// AUJOURD'HUI de la base — pour constater que la précision est GLOBALE au type (pas filtrée
// par le couple). Aucune écriture, aucune migration à ce stade.
import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog.js'

const champ = { padding: '8px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: 13, background: 'white' }
const carte = { background: 'white', borderRadius: 12, border: '1px solid #e2e8f0', padding: 18, marginBottom: 16 }
const titre = { fontSize: 15, fontWeight: 700, color: '#1e293b', margin: '0 0 12px' }

export default function Labo() {
  const [niveauxParCycle, setNiveauxParCycle] = useState([])      // [{cycle, niveaux:[{id,nom}]}]
  const [matieresParNiveau, setMatieresParNiveau] = useState([])  // [{niveau, matieres:[{id,nom}]}]
  const [niveau, setNiveau] = useState('')                        // nom du niveau choisi (le couple)
  const [matiere, setMatiere] = useState('')                      // nom de la matière choisie
  const [activites, setActivites] = useState([])                  // [{id, label, sous_types, params}] du couple (get)
  const [typeId, setTypeId] = useState(null)                      // id du type d'activité sélectionné
  const [busy, setBusy] = useState(false)

  // Programmes : niveaux (par cycle) + matières (par niveau), lus en base (get).
  useEffect(() => {
    fetchWithTimeout('/api/programmes', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) { setNiveauxParCycle(d.niveaux_par_cycle || []); setMatieresParNiveau(d.matieres_par_niveau || []) } })
      .catch(() => {})
  }, [])

  // Matières disponibles pour le niveau choisi (get, zéro copie : on relit la liste programmes).
  const matieresDuNiveau = (matieresParNiveau.find(x => x.niveau === niveau)?.matieres) || []

  // Quand le couple (matière + niveau) est complet → GET des types d'activité + leurs précisions.
  useEffect(() => {
    if (!niveau || !matiere) { setActivites([]); setTypeKey(''); return }
    setBusy(true)
    fetchWithTimeout(`/api/activites/${encodeURIComponent(matiere)}?niveau=${encodeURIComponent(niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => {
        const list = Array.isArray(d) ? d : []
        setActivites(list)
        setTypeId(list[0]?.id ?? null)
      })
      .catch(() => showError('Lecture des types d’activité impossible.'))
      .finally(() => setBusy(false))
  }, [niveau, matiere])

  // Quand on change de niveau : la matière du couple précédent n'a plus forcément de sens → on la vide.
  function choisirNiveau(nom) {
    setNiveau(nom)
    setMatiere('')
  }

  const typeCourant = activites.find(a => a.id === typeId) || null

  return (
    <div style={{ maxWidth: 760 }}>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">🧪 Labo — Paramètres de l'activité par couple</h2>
        <span className="text-xs text-gray-400">brique 1 · lecture seule</span>
      </div>
      <p className="text-xs text-gray-500 mb-4" style={{ lineHeight: 1.6 }}>
        Choisis un <b>couple</b> (niveau + matière). On affiche le <b>Type d'activité</b> et sa <b>Précision</b>
        {' '}tels qu'ils sortent de la base aujourd'hui. Constat visé : la précision <b>ne change pas</b> selon le couple
        {' '}(elle est globale au type). Aucune écriture ici.
      </p>

      {/* 1) Le couple : niveau (par cycle) + matière (du niveau) — get /api/programmes */}
      <div style={carte}>
        <h3 style={titre}>1. Couple</h3>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Niveau</label>
            <select value={niveau} onChange={e => choisirNiveau(e.target.value)} style={{ ...champ, minWidth: 240 }}>
              <option value="">— choisir un niveau —</option>
              {niveauxParCycle.map(grp => (
                <optgroup key={grp.cycle} label={grp.cycle}>
                  {grp.niveaux.map(n => <option key={n.id} value={n.nom}>{n.nom}</option>)}
                </optgroup>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Matière</label>
            <select value={matiere} onChange={e => setMatiere(e.target.value)} disabled={!niveau} style={{ ...champ, minWidth: 240 }}>
              <option value="">{niveau ? '— choisir une matière —' : '— choisis d’abord un niveau —'}</option>
              {matieresDuNiveau.map(m => <option key={m.id} value={m.nom}>{m.nom}</option>)}
            </select>
          </div>
        </div>
        {niveau && matiere && (
          <div style={{ marginTop: 10, fontSize: 13, color: '#334155' }}>
            Couple sélectionné : <b>{matiere}</b> · <b>{niveau}</b>
          </div>
        )}
      </div>

      {/* 2) Paramètres de l'activité (reproduction du bloc prof) — get /api/activites */}
      {niveau && matiere && (
      <div style={carte}>
        <h3 style={titre}>2. Paramètres de l'activité</h3>
        {busy ? (
          <p className="text-sm" style={{ color: '#94a3b8' }}>Lecture…</p>
        ) : activites.length === 0 ? (
          <p className="text-sm" style={{ color: '#94a3b8' }}>Aucun type d'activité pour ce couple.</p>
        ) : (
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Type d'activité</label>
              <select value={typeId ?? ''} onChange={e => setTypeId(Number(e.target.value))} style={{ ...champ, minWidth: 240 }}>
                {activites.map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Précision (lue sur le COUPLE)</label>
              {typeCourant && typeCourant.sous_types.length > 0 ? (
                <select style={{ ...champ, minWidth: 240 }} defaultValue={typeCourant.sous_types[0]}>
                  {typeCourant.sous_types.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              ) : (
                <div className="text-sm" style={{ color: '#94a3b8', paddingTop: 6 }}>ce type n'a pas de précision</div>
              )}
            </div>
          </div>
        )}

        {typeCourant && (
          <div style={{ marginTop: 14, padding: '10px 12px', background: '#f0fdf4', border: '1px solid #bbf7d0',
            borderRadius: 8, fontSize: 12.5, color: '#166534', lineHeight: 1.5 }}>
            Ces précisions viennent du <b>couple × type</b> (table <code>referentiel_type_precisions</code>) :
            change le niveau ci-dessus et, pour le même type, la liste suit le couple — chaque couple a SES précisions.
          </div>
        )}
      </div>
      )}
    </div>
  )
}
