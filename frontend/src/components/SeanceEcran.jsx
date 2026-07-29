// Écran « Séance » du monde MES CONTENUS — même mécanique que l'écran Activité du monde neuf :
// DEUX COLONNES (formulaire à gauche, déroulé généré à droite), pastilles d'étape numérotées
// (bordeaux clignotant tant que l'étape est à faire, vert quand c'est acquis), frise en haut,
// génération en STREAMING (sablier + jauge, règle IA) et RÈGLE 0 native : la séance s'écrit en
// base à la génération même (POST à la 1re, PUT + version aux suivantes) — aucun bouton
// d'enregistrement, badge « Enregistrée » / « Réessayer l'enregistrement ».
//
// La colonne de gauche suit la CHRONOLOGIE donnée par l'utilisateur (30/07) :
// ① Texte de départ (thème + contexte) → ② Cadre général (mode puis durée) → ③ Ce qu'on vise
// (compétences) → ④ Ce qu'il faut prévoir (matériel) → ⑤ Déroulé dans le temps (esquisse A/B/C,
// contraintes, style de production) → ⑥ Générer la séance. Les groupes ③④⑤ sont facultatifs :
// leur pastille passe au vert quand ils sont remplis, mais ne clignote jamais.
import { useRef, useState } from 'react'
import SplitPane from './SplitPane.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import EtapeBadge from './EtapeBadge.jsx'
import ApportTexte from './contenus/ApportTexte.jsx'
import { corpsHtml, imprimerApercu } from '../utils/apercuHtml.js'
import { apiFetch, lireReponse, refreshSession, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'

const MSG_ECHEC_GENERATION =
  'La génération de votre séance n\'a pas pu aboutir. Merci de réessayer.\n' +
  'Si le problème persiste, cliquez ici pour nous le signaler.'

const DUREES = [30, 45, 50, 55, 60, 90, 120]

const MODES = [
  { id: 'standard', label: 'Séance standard', desc: 'Nouvelle séance sur le thème' },
  { id: 'remediation', label: 'Remédiation', desc: "La classe n'a pas compris, on recommence autrement" },
  { id: 'approfondissement', label: 'Approfondissement', desc: 'Aller plus loin sur un thème déjà acquis' },
  { id: 'autonomie', label: 'Autonomie guidée', desc: 'Les élèves travaillent seuls, la séance les guide' },
]

const STYLES = [
  { id: 'classique', label: 'Classique' },
  { id: 'ludique', label: 'Ludique' },
  { id: 'structure', label: 'Structuré' },
  { id: 'concis', label: 'Très concis' },
]

const CARTE = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 10 }
const LABEL = { fontSize: 12, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }
const CHAMP = { width: '100%', padding: '9px 12px', fontSize: 13, lineHeight: 1.6, color: '#1e293b', border: '1px solid #cbd5e1', borderRadius: 6, fontFamily: 'inherit', boxSizing: 'border-box', background: '#fff' }

const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)

// Titre de groupe : pastille d'étape (même EtapeBadge que l'écran Activité) + libellé.
function TitreGroupe({ n, fait, actif, children }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <EtapeBadge n={n} fait={fait} actif={actif} />
      <span style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>{children}</span>
    </div>
  )
}

// Pastille radio maison (même motif que les boutons de mode de l'outil existant).
function Pastille({ actif, label, title, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={title || label}
      style={{
        padding: '5px 12px', fontSize: 12, fontWeight: actif ? 700 : 400,
        border: `1.5px solid ${actif ? 'var(--bordeaux)' : '#e2e8f0'}`,
        borderRadius: 5, cursor: disabled ? 'default' : 'pointer',
        background: actif ? '#fff0f0' : '#f8fafc',
        color: actif ? 'var(--bordeaux)' : '#64748b',
      }}
    >
      {label}
    </button>
  )
}

// Frise du haut — même dessin que la frise de l'écran Activité (FriseProgression), avec les
// étapes PROPRES à la séance : seules les étapes OBLIGATOIRES y figurent.
function FriseSeance({ texteOk, cadreOk, loading, resultat }) {
  const termine = !!resultat && !loading
  const etapes = [
    { n: 1, label: 'Texte de départ', fait: !!texteOk },
    { n: 2, label: 'Cadre général', fait: !!cadreOk },
    { n: 3, label: 'Générer', fait: termine },
  ]
  const courant = loading ? 2 : etapes.findIndex(e => !e.fait)
  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', rowGap: 8 }}>
      {etapes.map((e, i) => {
        const estCourant = i === courant
        const bg = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#fff'
        const fg = (e.fait || estCourant) ? '#fff' : '#94a3b8'
        const bord = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#cbd5e1'
        return (
          <span key={e.n} style={{ display: 'flex', alignItems: 'center' }}>
            {i > 0 && (
              <span style={{ width: 30, height: 2, borderRadius: 2, margin: '0 9px',
                             background: etapes[i - 1].fait ? '#16a34a' : '#e2e8f0' }} />
            )}
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                             display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                             fontSize: 12, fontWeight: 800, fontVariantNumeric: 'tabular-nums',
                             background: bg, color: fg, border: `1.5px solid ${bord}`,
                             boxShadow: estCourant ? '0 0 0 4px rgba(140,29,64,0.14)' : 'none' }}>
                {e.fait ? '✓' : e.n}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
                             color: estCourant ? '#1e293b' : e.fait ? '#64748b' : '#94a3b8' }}>
                {e.label}
              </span>
            </span>
          </span>
        )
      })}
    </div>
  )
}

export default function SeanceEcran({ seance, matiere, niveau, onNavigate }) {
  // ── Le formulaire entier (reprise complète si une séance est rouverte) ──
  const [theme, setTheme] = useState(seance?.titre || '')
  const [contexte, setContexte] = useState(seance?.contexte || '')
  const dureeConnue = seance?.duree && DUREES.includes(seance.duree)
  const [dureeListe, setDureeListe] = useState(dureeConnue ? String(seance.duree) : '')
  const [dureeLibre, setDureeLibre] = useState(seance?.duree && !dureeConnue ? String(seance.duree) : '')
  const [mode, setMode] = useState(seance?.mode || null)          // AUCUN mode pré-coché (règle maison)
  const [competences, setCompetences] = useState(Array.isArray(seance?.competences) ? seance.competences : [])
  const [competenceSaisie, setCompetenceSaisie] = useState('')
  const [materiel, setMateriel] = useState(seance?.materiel || '')
  const [esquisse, setEsquisse] = useState({
    a: seance?.esquisse?.a || '', b: seance?.esquisse?.b || '', c: seance?.esquisse?.c || '',
  })
  const [contraintes, setContraintes] = useState(seance?.contraintes || '')
  const [style, setStyle] = useState(seance?.style || null)       // AUCUN style pré-coché

  // ── Génération + règle 0 (mêmes états que l'écran Activité) ──
  const [resultat, setResultat] = useState(seance?.resultat || null)
  const [loading, setLoading] = useState(false)
  const [seanceId, setSeanceId] = useState(seance?.id || null)
  const [enregistrement, setEnregistrement] = useState(seance ? 'ok' : null)   // null | 'ok' | 'echec'
  const resultatRef = useRef(null)

  // La durée LIBRE prime sur la liste (règle de la maquette).
  const duree = parseInt(dureeLibre || dureeListe, 10) || 0
  const texteOk = !!theme.trim()
  const cadreOk = !!mode && duree >= 5 && duree <= 300
  const pretAGenerer = texteOk && cadreOk

  function ajouterCompetence() {
    const c = competenceSaisie.trim()
    if (!c) return
    setCompetences(prev => [...prev, c])
    setCompetenceSaisie('')
  }

  function corpsFormulaire() {
    return {
      theme: theme.trim(),
      contexte: contexte.trim(),
      duree,
      mode,
      competences,
      materiel: materiel.trim(),
      esquisse,
      contraintes: contraintes.trim(),
      style: style || null,
    }
  }

  // ── Règle 0 : l'écriture en base suit CHAQUE génération réussie ──
  async function sauver(complet) {
    const corps = { ...corpsFormulaire(), resultat: complet }
    try {
      if (seanceId) {
        await lireReponse(await apiFetch(`/api/contenus/seances/${seanceId}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
        }, TIMEOUT_STD))
      } else {
        const d = await lireReponse(await apiFetch('/api/contenus/seances', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
        }, TIMEOUT_STD))
        setSeanceId(d.id)
      }
      setEnregistrement('ok')
    } catch {
      // Un échec d'auto-save DOIT se voir (règle 0 : rien n'attend en mémoire « pour plus tard »).
      setEnregistrement('echec')
      showError("Votre séance est affichée mais n'a pas pu être enregistrée.\n\nCliquez sur « Réessayer l'enregistrement » en haut de l'écran.")
    }
  }

  // ── Génération en STREAMING — même mécanique que l'écran Activité (SSE delta/error/done). ──
  async function generer() {
    if (!theme.trim()) {
      showError('Décrivez d\'abord le thème ou l\'objectif de la séance.')
      return
    }
    if (!mode) {
      showError('Choisissez un mode de séance avant de générer.')
      return
    }
    if (!(duree >= 5 && duree <= 300)) {
      showError('Indiquez une durée entre 5 et 300 minutes (liste ou durée libre).')
      return
    }
    setResultat(null)
    setEnregistrement(null)
    setLoading(true)
    try {
      const opts = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(corpsFormulaire()),
      }
      let res = await fetch('/api/contenus/seances/generer', opts)
      if (res.status === 401 && await refreshSession()) {
        res = await fetch('/api/contenus/seances/generer', opts)
      }
      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}))
        if (err.detail) showError(err.detail)
        else showError(MSG_ECHEC_GENERATION, { feedback: true })
        return
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let tampon = '', complet = '', erreurFlux = false, termine = false, refIncident = null
      setResultat('')
      setTimeout(() => resultatRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        tampon += decoder.decode(value, { stream: true })
        let sep
        while ((sep = tampon.indexOf('\n\n')) >= 0) {
          const bloc = tampon.slice(0, sep)
          tampon = tampon.slice(sep + 2)
          const evt  = (bloc.split('\n').find(l => l.startsWith('event:')) || '').slice(6).trim()
          const data = (bloc.split('\n').find(l => l.startsWith('data:'))  || '').slice(5).trim()
          if (evt === 'delta') {
            try { complet += JSON.parse(data).text; setResultat(complet) } catch { /* bloc partiel ignoré */ }
          } else if (evt === 'error') {
            erreurFlux = true
            try { refIncident = JSON.parse(data).ref || null } catch { /* pas de réf */ }
          } else if (evt === 'done') {
            termine = true
          }
        }
      }

      if (erreurFlux || !termine || !complet) {
        setResultat(null)
        showError(MSG_ECHEC_GENERATION, { feedback: true, ref: refIncident })
        return
      }

      // RÈGLE 0 : la génération réussie s'écrit TOUT DE SUITE en base (tables neuves).
      await sauver(complet)
    } catch (e) {
      console.error('génération séance (Mes contenus) :', e)
      setResultat(null)
      showError(MSG_ECHEC_GENERATION, { feedback: true })
    } finally {
      setLoading(false)
    }
  }

  const titreBarre = seance
    ? `Reprise : ${seance.titre || 'séance'}`
    : 'Nouvelle séance'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* ── Barre du haut : retour + titre + couple + état d'enregistrement (règle 0 visible) ── */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', flexShrink: 0, alignItems: 'center', gap: 8 }}>
        <button
          type="button"
          onClick={() => onNavigate('mes-contenus')}
          title="Revenir à Mes contenus"
          style={{ margin: '0 0 0 8px', fontSize: 12, color: '#475569', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 6, padding: '4px 10px', cursor: 'pointer', flexShrink: 0 }}
        >
          ← Mes contenus
        </button>
        <div style={{ padding: '10px 12px', fontSize: '13px', fontWeight: 700, color: 'var(--bordeaux)', borderBottom: '2px solid var(--bordeaux)', marginBottom: '-1px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {titreBarre}
        </div>
        <span style={{ fontSize: 12, fontWeight: 600, color: '#1e293b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 6, padding: '3px 10px', flexShrink: 0 }}>
          {(seance?.matiere || matiere || '—')} · {(seance?.niveau || niveau || '—')}
        </span>

        {enregistrement === 'ok' && (
          <span title="Votre séance est écrite en base — retrouvez-la dans Mes contenus"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#166534', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 99, padding: '3px 10px', flexShrink: 0 }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Enregistrée
          </span>
        )}
        {enregistrement === 'echec' && (
          <button
            type="button"
            onClick={() => resultat && sauver(resultat)}
            title="L'enregistrement automatique a échoué — cliquez pour réessayer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 99, padding: '3px 10px', cursor: 'pointer', flexShrink: 0 }}
          >
            Réessayer l'enregistrement
          </button>
        )}
      </div>

      {/* ── Frise de progression (les étapes OBLIGATOIRES) — même dessin que l'écran Activité. ── */}
      <div style={{ padding: '14px 20px 12px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
        <FriseSeance texteOk={texteOk} cadreOk={cadreOk} loading={loading} resultat={resultat} />
      </div>

      <div className="creer-corps">
        {(() => {
          // ── Colonne GAUCHE : le formulaire, dans la chronologie validée (30/07). ──
          const formulaire = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

              {/* ① Texte de départ */}
              <section style={CARTE}>
                <TitreGroupe n={1} fait={texteOk} actif={!texteOk && !loading}>Texte de départ</TitreGroupe>
                <label style={LABEL}>Thème / objectif de la séance</label>
                {/* Même procédé d'apport que la zone texte de l'activité : TXT / Image / PDF /
                    Dicter (copiés tels quels) + « Propose-moi un thème » (version séance). */}
                <ApportTexte texte={theme} onChange={setTheme} disabled={loading} />
                <textarea
                  value={theme}
                  onChange={e => setTheme(e.target.value)}
                  placeholder={"Décrivez le thème ou l'objectif de la séance…\n— ou importez un fichier TXT, une image scannée ou un PDF\n— ou dictez avec le micro\n— ou laissez « Propose-moi un thème » l'écrire à votre place"}
                  rows={4}
                  disabled={loading}
                  style={{ ...CHAMP, resize: 'vertical' }}
                />
                <label style={LABEL}>Contexte rapide <span style={{ textTransform: 'none', fontWeight: 400, color: '#94a3b8' }}>(optionnel)</span></label>
                <input
                  type="text"
                  value={contexte}
                  onChange={e => setContexte(e.target.value)}
                  placeholder="Infos contextuelles…"
                  disabled={loading}
                  style={CHAMP}
                />
              </section>

              {/* ② Cadre général : le MODE d'abord, la durée ensuite (chronologie utilisateur) */}
              <section style={CARTE}>
                <TitreGroupe n={2} fait={cadreOk} actif={texteOk && !cadreOk && !loading}>Cadre général de la séance</TitreGroupe>
                <label style={LABEL}>Mode de séance</label>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {MODES.map(m => (
                    <Pastille key={m.id} actif={mode === m.id} label={m.label} title={m.desc}
                      onClick={() => setMode(m.id)} disabled={loading} />
                  ))}
                </div>
                <label style={LABEL}>Durée</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <select
                    value={dureeListe}
                    onChange={e => setDureeListe(e.target.value)}
                    disabled={loading}
                    title="Choisir une durée courante"
                    style={{ ...CHAMP, width: 160, color: dureeListe ? '#1e293b' : '#94a3b8' }}
                  >
                    <option value="">Choisissez…</option>
                    {DUREES.map(d => <option key={d} value={d}>{d} min</option>)}
                  </select>
                  <span style={{ fontSize: 12, color: '#94a3b8' }}>ou</span>
                  <input
                    type="number"
                    min="5"
                    max="300"
                    value={dureeLibre}
                    onChange={e => setDureeLibre(e.target.value)}
                    placeholder="durée libre"
                    disabled={loading}
                    title="Durée libre en minutes — si remplie, c'est elle qui compte"
                    style={{ ...CHAMP, width: 110 }}
                  />
                  <span style={{ fontSize: 12, color: '#64748b' }}>min</span>
                </div>
              </section>

              {/* ③ Ce qu'on vise (facultatif) */}
              <section style={CARTE}>
                <TitreGroupe n={3} fait={competences.length > 0} actif={false}>Ce qu'on vise</TitreGroupe>
                <label style={LABEL}>Compétences / attendus</label>
                {competences.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {competences.map((c, i) => (
                      <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#1e293b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '3px 10px' }}>
                        {c}
                        <button type="button" onClick={() => setCompetences(prev => prev.filter((_, j) => j !== i))}
                          title="Retirer cette compétence"
                          style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 0, fontSize: 13, lineHeight: 1 }}>
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="text"
                    value={competenceSaisie}
                    onChange={e => setCompetenceSaisie(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); ajouterCompetence() } }}
                    placeholder="Ex : identifier les personnages d'un récit…"
                    disabled={loading}
                    style={{ ...CHAMP, flex: 1 }}
                  />
                  <button type="button" onClick={ajouterCompetence} disabled={loading} title="Ajouter cette compétence à la liste"
                    style={{ fontSize: 12, fontWeight: 600, color: '#475569', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 6, padding: '0 14px', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                    + Ajouter
                  </button>
                </div>
              </section>

              {/* ④ Ce qu'il faut prévoir (facultatif) */}
              <section style={CARTE}>
                <TitreGroupe n={4} fait={!!materiel.trim()} actif={false}>Ce qu'il faut prévoir</TitreGroupe>
                <label style={LABEL}>Matériel nécessaire</label>
                <input
                  type="text"
                  value={materiel}
                  onChange={e => setMateriel(e.target.value)}
                  placeholder="Liste du matériel…"
                  disabled={loading}
                  style={CHAMP}
                />
              </section>

              {/* ⑤ Déroulé dans le temps (facultatif) : esquisse A/B/C + contraintes + style */}
              <section style={CARTE}>
                <TitreGroupe
                  n={5}
                  fait={!!(esquisse.a.trim() || esquisse.b.trim() || esquisse.c.trim() || contraintes.trim() || style)}
                  actif={false}
                >
                  Déroulé dans le temps
                </TitreGroupe>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
                  {[
                    ['a', 'A. Mise en route', 'Ex : 2-5 min, réactivation…'],
                    ['b', 'B. Activité principale', 'Activité centrale…'],
                    ['c', 'C. Retour / trace écrite', 'Synthèse ou évaluation…'],
                  ].map(([cle, titreCol, placeholder]) => (
                    <div key={cle} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: '#1e293b' }}>{titreCol}</span>
                      <textarea
                        value={esquisse[cle]}
                        onChange={e => setEsquisse(prev => ({ ...prev, [cle]: e.target.value }))}
                        placeholder={placeholder}
                        rows={2}
                        disabled={loading}
                        title="Esquisse facultative — aSchool la respectera à la génération"
                        style={{ ...CHAMP, resize: 'vertical' }}
                      />
                    </div>
                  ))}
                </div>
                <label style={LABEL}>Contraintes / consignes spéciales</label>
                <input
                  type="text"
                  value={contraintes}
                  onChange={e => setContraintes(e.target.value)}
                  placeholder="Notes particulières…"
                  disabled={loading}
                  style={CHAMP}
                />
                <label style={LABEL}>Style de production</label>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {STYLES.map(s => (
                    <Pastille key={s.id} actif={style === s.id} label={s.label}
                      onClick={() => setStyle(style === s.id ? null : s.id)} disabled={loading} />
                  ))}
                </div>
              </section>

              {/* ⑥ Générer la séance */}
              <section style={CARTE}>
                <TitreGroupe n={6} fait={!!resultat && !loading} actif={pretAGenerer && !loading && !resultat}>
                  Générer la séance
                </TitreGroupe>
                {loading ? (
                  <span className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: 0.75, cursor: 'wait', alignSelf: 'flex-start' }}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
                    Génération en cours…
                  </span>
                ) : (
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={generer}
                    disabled={!pretAGenerer}
                    title={pretAGenerer
                      ? (resultat ? 'Régénérer la séance — l\'ancienne version reste dans l\'historique' : 'Générer la séance — elle s\'enregistrera automatiquement dans Mes contenus')
                      : 'Complétez d\'abord le thème, le mode et la durée'}
                    style={{ alignSelf: 'flex-start', opacity: pretAGenerer ? 1 : 0.55, cursor: pretAGenerer ? 'pointer' : 'not-allowed' }}
                  >
                    {resultat ? 'Régénérer la séance' : 'Générer la séance'}
                  </button>
                )}
              </section>
            </div>
          )

          // ── Colonne DROITE : le déroulé généré (texte en direct pendant le flux, mis en
          // forme à la fin) — même logique que la colonne résultat de l'écran Activité. ──
          const colonneResultat = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {loading && (
                <JaugeAttente libelle="aSchool construit votre séance, phase par phase…" />
              )}
              {!loading && !resultat && (
                <div style={{
                  border: '1px dashed #cbd5e1', borderRadius: 8, background: '#f8fafc',
                  color: '#94a3b8', fontSize: 14, textAlign: 'center', minHeight: 340,
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  justifyContent: 'center', gap: 12, padding: '48px 24px',
                }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
                  </svg>
                  <span>Ici s'affichera le déroulé de votre séance.</span>
                </div>
              )}
              {resultat !== null && (loading ? (
                // Pendant le flux : le texte brut défile en direct.
                <div ref={resultatRef} className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed rounded p-4"
                  style={{ background: '#f8faff', border: '1px solid #e2e8f0', borderLeftWidth: 4, borderLeftColor: 'var(--bordeaux)' }}>
                  {resultat}
                </div>
              ) : (
                // Flux terminé : le déroulé mis en forme + Imprimer.
                <section ref={resultatRef} className="bg-white rounded border border-gray-200 p-4" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: '#16a34a', color: '#fff' }}>
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                      </span>
                      <span className="section-title" style={{ fontWeight: 700 }}>Déroulé généré</span>
                    </div>
                    <button type="button" onClick={() => imprimerApercu(corpsHtml(resultat))}
                      title="Imprimer cette séance mise en forme" className="btn-secondary">
                      <IconPrint /> Imprimer
                    </button>
                  </div>
                  <div className="apercu-corps" style={{ color: '#1e293b', lineHeight: 1.7, fontSize: 14 }}
                    dangerouslySetInnerHTML={{ __html: corpsHtml(resultat) }} />
                  <style>{`
                    .apercu-corps h1,.apercu-corps h2,.apercu-corps h3{color:#0f172a;line-height:1.3;margin:1.4em 0 .4em}
                    .apercu-corps h1{font-size:1.4rem}.apercu-corps h2{font-size:1.15rem}.apercu-corps h3{font-size:1.05rem}
                    .apercu-corps p{margin:.6em 0}
                    .apercu-corps ul,.apercu-corps ol{margin:.6em 0 .6em 1.4em;padding:0}.apercu-corps li{margin:.3em 0}
                    .apercu-corps hr{border:none;border-top:1px solid #e2e8f0;margin:1.4em 0}
                    .apercu-corps strong{color:#0f172a}
                  `}</style>
                </section>
              ))}
            </div>
          )

          return <SplitPane storageKey="contenus-seance-split-v1" gauche={formulaire} droite={colonneResultat} />
        })()}
      </div>

    </div>
  )
}
