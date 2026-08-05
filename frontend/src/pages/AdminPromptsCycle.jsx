import { useEffect, useState } from 'react'
import OngletsPrompts from '../components/OngletsPrompts'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import SplitPane from '../components/SplitPane.jsx'

// Écran des PROMPTS RANGÉS SUR LE CYCLE — un seul composant pour les deux (« Matières par cycle »
// et « Découpe par cycle »), parce que c'est rigoureusement le même geste sur une autre colonne :
// une entrée par cycle, une zone de texte, un bouton « Enregistrer le prompt ». Les deux écrans ne
// peuvent donc pas diverger.
//
// Ces prompts ne sont PAS dans le registre des prompts d'outils (llm_prompts) : ils sont rangés sur
// le CYCLE, en base (`cycles.prompt_matieres`, `cycles.prompt_decoupe`), parce qu'un cycle est une
// famille de documents bâtis pareil — tous les BTS, tous les programmes de collège. D'où une entrée
// par cycle, et non un texte unique.
//
// C'est ICI qu'on les écrit, et nulle part ailleurs : l'écran Référentiels ne fait plus que les
// montrer. Deux éditeurs sur la même colonne finissaient par s'écraser sans prévenir.
//
// Deux colonnes comme les autres sous-options de Prompts : la liste des cycles à gauche, le prompt
// du cycle choisi à droite. Le bouton « Cacher le détail » est permanent (règle maison).
const SUJETS = {
  matieres: {
    titre: 'Prompts — Matières par cycle',
    route: 'prompt-matieres',
    colonne: 'cycles.prompt_matieres',
    detail: 'Prompt de lecture des matières',
    intro: 'Le texte qui lit les matières d’un référentiel. Un cycle est une famille de documents '
      + 'bâtis pareil : le prompt est rangé sur le cycle et sert à tous ses référentiels — d’où une '
      + 'entrée par cycle. L’écran Référentiels ne fait que le montrer, il se corrige ici.',
    role: 'il lira les matières de tous les référentiels de ce cycle',
    ecritQuand: 'au premier « Proposer les matières » du cycle',
    vide: 'Le prompt des matières est vide.',
  },
  decoupe: {
    titre: 'Prompts — Découpe (chunk) par cycle',
    route: 'prompt-decoupe',
    colonne: 'cycles.prompt_decoupe',
    detail: 'Prompt de découpe du document',
    intro: 'Le texte qui découpe un référentiel en unités. L’ossature d’un référentiel (activités, '
      + 'compétences, unités certificatives, ce qu’on écarte) est celle de toute la famille : le '
      + 'prompt est rangé sur le cycle et sert à tous ses référentiels. L’écran Référentiels ne fait '
      + 'que le montrer, il se corrige ici.',
    role: 'il découpera tous les référentiels de ce cycle',
    ecritQuand: 'à la première découpe du cycle',
    vide: 'Le prompt de découpe est vide.',
  },
}

export default function AdminPromptsCycle({ sujet }) {
  const meta = SUJETS[sujet] || SUJETS.matieres
  const [cycles, setCycles] = useState([])       // [{ id, nom, ordre, prompt, valide }]
  const [cycleId, setCycleId] = useState(0)      // 0 = rien de choisi (on ne présélectionne pas)
  const [texte, setTexte] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [panne, setPanne] = useState(false)
  const [detailCache, setDetailCache] = useState(false)

  useEffect(() => { charger() }, [])   // eslint-disable-line react-hooks/exhaustive-deps

  // Lecture en base, get direct : la table des cycles, puis LE prompt de chacun. Une lecture par
  // cycle (la route serveur en prend un) — elles partent ensemble, et l'état de chaque cycle est
  // ainsi connu dès la liste, sans avoir à l'ouvrir.
  async function charger(selectId) {
    try {
      const r = await fetchWithTimeout('/api/admin/cycles', { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error('lecture des cycles')
      const d = await r.json()
      const liste = d.cycles || []
      const avecPrompt = await Promise.all(liste.map(async c => {
        try {
          const rp = await fetchWithTimeout(`/api/admin/cycles/${meta.route}?cycle_id=${c.id}`,
            { credentials: 'include' }, TIMEOUT_STD)
          const dp = rp.ok ? await rp.json().catch(() => null) : null
          return { ...c, prompt: (dp && dp.prompt) || '', valide: !!(dp && dp.valide) }
        } catch { return { ...c, prompt: '', valide: false } }
      }))
      setCycles(avecPrompt)
      setPanne(false)
      const cible = selectId || cycleId
      const actif = avecPrompt.find(c => c.id === cible)
      setCycleId(actif ? cible : 0)
      setTexte(actif ? actif.prompt : '')
    } catch {
      setPanne(true)
      showError('Lecture des cycles impossible — vérifiez que le backend tourne.')
    } finally {
      setChargement(false)
    }
  }

  const cycleActif = cycles.find(c => c.id === cycleId)
  // Miroir du garde-fou backend : sans {texte}, le document ne serait jamais inséré dans le prompt.
  const repereManquant = !!cycleActif && !texte.includes('{texte}')
  const invalide = !cycleActif || texte.trim() === '' || repereManquant

  function choisirCycle(c) {
    setCycleId(c.id)
    setTexte(c.prompt)
    setMessage(null)
    setDetailCache(false)   // cliquer une ligne veut dire « montre-moi le détail »
  }

  // Enregistrer = enregistrer ET valider : c'est le même geste que dans Référentiels. Le prompt
  // écrit par l'IA sert déjà ; ce clic dit « je l'ai relu ». Il reste donc actif même si le texte
  // n'a pas été retouché — sinon on ne pourrait jamais valider un prompt IA tel quel.
  async function enregistrer() {
    if (invalide) {
      showError(texte.trim() === ''
        ? meta.vide
        : 'Le prompt doit contenir le repère {texte} : c’est là que le document est inséré. '
          + 'Remettez-le tel quel avant d’enregistrer.')
      return
    }
    setSaving(true)
    setMessage(null)
    try {
      const r = await fetchWithTimeout(`/api/admin/cycles/${meta.route}/valider`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: cycleId, prompt: texte }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) { showError(d.detail || 'L’enregistrement du prompt a échoué.'); return }
      setMessage({ type: 'ok', text: 'Prompt enregistré et validé.' })
      await charger(cycleId)   // read-after-write : l'écran raconte l'état réel de la base
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSaving(false)
    }
  }

  // Étiquette d'état d'un cycle — le prompt SERT dès qu'il existe, le voyant dit seulement s'il a
  // été relu (mêmes mots que dans Référentiels, pour que ce soit la même chose aux deux endroits).
  function etat(c) {
    if (c.valide) return { texte: 'Relu et validé', fond: '#f0fdf4', trait: '#bbf7d0', encre: '#166534' }
    if ((c.prompt || '').trim()) return { texte: 'À relire', fond: '#fffbeb', trait: '#fde68a', encre: '#b45309' }
    return { texte: 'Pas encore écrit', fond: '#f3f4f6', trait: '#e5e7eb', encre: '#6b7280' }
  }

  // ── Colonne gauche : un cycle par ligne, avec son étiquette d'état. ──
  const colonneListe = (
    <div
      className="bg-white rounded-lg border border-gray-200"
      style={{ overflow: 'hidden', height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {chargement && (
          <p className="text-sm text-gray-400" style={{ padding: '24px 16px', textAlign: 'center' }}>
            Chargement…
          </p>
        )}
        {!chargement && panne && (
          <div style={{ padding: '24px 16px', textAlign: 'center' }}>
            <button
              type="button"
              onClick={() => { setChargement(true); charger() }}
              title="Relancer la lecture des cycles et de leurs prompts"
              style={{ padding: '8px 20px', borderRadius: 7, border: '1px solid #e5e7eb',
                       background: '#fff', color: '#6b7280', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}
            >
              Réessayer
            </button>
          </div>
        )}
        {!chargement && !panne && cycles.length === 0 && (
          <p className="text-sm text-gray-400" style={{ padding: '24px 16px', textAlign: 'center' }}>
            Aucun cycle en base.
          </p>
        )}
        {cycles.map(c => {
          const active = c.id === cycleId
          const e = etat(c)
          return (
            <button
              key={c.id}
              onClick={() => choisirCycle(c)}
              title={`Voir et régler le prompt du cycle « ${c.nom} » — ${meta.role}`}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '10px 14px', cursor: 'pointer',
                border: 'none', borderBottom: '1px solid #f1f5f9',
                borderLeft: active ? '3px solid #A63045' : '3px solid transparent',
                background: active ? '#fdf2f4' : 'white',
              }}
            >
              <span style={{
                display: 'flex', alignItems: 'baseline', gap: 8, fontSize: 13,
                color: active ? '#A63045' : '#374151', fontWeight: active ? 600 : 400,
              }}>
                <span style={{ flex: 1, minWidth: 0 }}>{c.nom}</span>
                <span style={{
                  flexShrink: 0, fontSize: 10, padding: '1px 7px', borderRadius: 5,
                  background: e.fond, color: e.encre, border: `1px solid ${e.trait}`,
                }}>
                  {e.texte}
                </span>
              </span>
              <span style={{
                display: 'block', marginTop: 3, fontSize: 11, color: '#94a3b8',
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
              }}>
                {meta.colonne}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )

  // ── Colonne droite : le prompt du cycle choisi — la zone de texte et son bouton, rien d'autre. ──
  const colonneDetail = !cycleActif ? (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <p className="text-sm text-gray-500">Choisissez un cycle dans la liste pour ouvrir son prompt ici.</p>
      <p className="text-xs text-gray-400 mt-2">
        Ce prompt est écrit par l’IA {meta.ecritQuand}, à partir du référentiel déposé, puis
        réutilisé par tous les référentiels du même cycle. Il doit garder le repère
        {' '}<code>{'{texte}'}</code> — c’est là que le document est inséré.
      </p>
    </div>
  ) : (
    <div
      className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5"
      style={{ height: '100%', minHeight: 420 }}
    >
      <div style={{ flexShrink: 0 }}>
        <h3 className="text-sm font-semibold text-gray-700">
          {meta.detail} — cycle « {cycleActif.nom} »
        </h3>
        <p className="text-xs text-gray-400 mt-1" style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
          cycles.prompt_matieres
        </p>
      </div>

      <div className="flex items-center gap-2 flex-wrap" style={{ flexShrink: 0 }}>
        <span className="text-xs font-medium text-gray-600">Repère obligatoire :</span>
        <code
          title={repereManquant ? 'Repère manquant — à remettre dans le texte' : 'Présent dans le texte'}
          style={{
            fontSize: 12, padding: '2px 7px', borderRadius: 5,
            background: repereManquant ? '#fef2f2' : '#f0fdf4',
            color: repereManquant ? '#dc2626' : '#166534',
            border: `1px solid ${repereManquant ? '#fecaca' : '#bbf7d0'}`,
          }}
        >
          {'{texte}'}
        </code>
        <span style={{
          marginLeft: 'auto', fontSize: 11, padding: '2px 8px', borderRadius: 5,
          background: etat(cycleActif).fond, color: etat(cycleActif).encre,
          border: `1px solid ${etat(cycleActif).trait}`,
        }}>
          {etat(cycleActif).texte}
        </span>
      </div>

      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        <label className="block text-xs font-medium text-gray-600 mb-1" style={{ flexShrink: 0 }}>Prompt</label>
        <textarea
          value={texte}
          onChange={e => setTexte(e.target.value)}
          spellCheck={false}
          placeholder={`Ce cycle n’a pas encore de prompt : il sera écrit par l’IA ${meta.ecritQuand}, ou vous pouvez l’écrire ici.`}
          className="w-full border rounded px-3 py-2"
          style={{
            flex: 1, minHeight: 160,
            borderColor: invalide ? '#dc2626' : '#d1d5db',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            fontSize: 12, lineHeight: 1.5, resize: 'none',
          }}
        />
        {/* Pas de consigne sur les accolades doublées ici : le document est inséré par un simple
            remplacement de {texte}, pas par un format() — un exemple JSON s'écrit tel quel. */}
        <p className="text-xs text-gray-400 mt-1" style={{ flexShrink: 0 }}>
          Enregistrer ce prompt vaut relecture : {meta.role}.
        </p>
      </div>

      <div className="flex items-center gap-3 flex-wrap" style={{ flexShrink: 0 }}>
        <button
          onClick={enregistrer}
          disabled={saving || invalide}
          title={`Enregistrer ce prompt : ${meta.role}`}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: '#1F6EEB', color: 'white', border: '1px solid #1F6EEB',
            borderRadius: 7, padding: '8px 20px', fontSize: 13, fontWeight: 500,
            cursor: (saving || invalide) ? 'not-allowed' : 'pointer',
            opacity: (saving || invalide) ? 0.6 : 1,
          }}
        >
          {saving ? 'Enregistrement…' : '✓ Enregistrer le prompt'}
        </button>
        {message && (
          <div style={{
            background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
            borderRadius: 8, padding: '10px 14px', fontSize: 13,
          }}>
            {message.text}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="flex flex-col gap-4">

      <OngletsPrompts />

      <div className="flex items-start gap-3" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="text-sm font-semibold text-gray-700 mb-1">
            {meta.titre}
            {cycles.length > 0 && (
              <span style={{
                marginLeft: 8, fontSize: 11, fontWeight: 600, padding: '1px 8px', borderRadius: 99,
                background: '#f3f4f6', color: '#6b7280', border: '1px solid #e5e7eb',
              }}>
                {cycles.length} cycle{cycles.length > 1 ? 's' : ''}
              </span>
            )}
          </h2>
          <p className="text-xs text-gray-400">{meta.intro}</p>
        </div>
        <button
          onClick={() => setDetailCache(c => !c)}
          title={detailCache
            ? 'Réafficher la colonne de détail à droite'
            : 'Cacher la colonne de détail — la liste prend toute la largeur'}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, flexShrink: 0,
            background: 'white', color: '#6b7280', border: '1px solid #e5e7eb',
            borderRadius: 7, padding: '7px 14px', fontSize: 12, fontWeight: 500, cursor: 'pointer',
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {detailCache
              ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
              : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
          </svg>
          {detailCache ? 'Afficher le détail' : 'Cacher le détail'}
        </button>
      </div>

      <div className="admin-prompts-corps">
        {detailCache
          ? <div className="split-pane"><div className="split-col split-col-flex">{colonneListe}</div></div>
          : <SplitPane
              storageKey={`admin-prompts-cycle-${sujet}-split-v1`}
              defautGauche={38}
              gauche={colonneListe}
              droite={colonneDetail}
            />}
      </div>
    </div>
  )
}
