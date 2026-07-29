// Écran « Séance » du chantier Mes contenus — la maquette utilisateur du 29/07, corrigée
// des règles maison : AUCUNE valeur pré-cochée (mode, style), rappel matière · niveau du
// profil, durée = liste OU minutes libres (le champ libre prime).
//
// Deux usages :
//  - `seance` fourni (ligne cliquée dans Mes contenus)  → LECTURE SEULE : champs pré-remplis,
//    le déroulé affiche le contenu généré mis en forme (+ Imprimer).
//  - `seance` absent (« + Créer → Une séance »)         → formulaire vierge ; « Générer la
//    séance » est visible mais « bientôt » : son branchement (tables neuves, nouveaux modes)
//    est l'étape suivante du chantier. Rien n'écrit nulle part pour l'instant.
import { useState } from 'react'
import { corpsHtml, imprimerApercu } from '../utils/apercuHtml.js'

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
const CHAMP_FIGE = { ...CHAMP, background: '#f8fafc', color: '#475569' }

const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)

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

export default function SeanceEcran({ seance, matiere, niveau, onNavigate }) {
  const lecture = !!seance   // séance existante = lecture seule (la modification arrive avec la génération)

  const [theme, setTheme] = useState(seance?.titre || '')
  const [contexte, setContexte] = useState(seance?.contexte || '')
  const dureeConnue = seance?.duree && DUREES.includes(seance.duree)
  const [dureeListe, setDureeListe] = useState(dureeConnue ? String(seance.duree) : '')
  const [dureeLibre, setDureeLibre] = useState(seance?.duree && !dureeConnue ? String(seance.duree) : '')
  const [mode, setMode] = useState(seance?.mode || null)          // AUCUN mode pré-coché (règle maison)
  const [style, setStyle] = useState(null)                        // idem pour le style
  const [competences, setCompetences] = useState([])
  const [competenceSaisie, setCompetenceSaisie] = useState('')
  const [materiel, setMateriel] = useState('')
  const [deroule, setDeroule] = useState({ a: '', b: '', c: '' }) // esquisse A/B/C (création)
  const [contraintes, setContraintes] = useState('')

  const champStyle = lecture ? CHAMP_FIGE : CHAMP

  function ajouterCompetence() {
    const c = competenceSaisie.trim()
    if (!c) return
    setCompetences(prev => [...prev, c])
    setCompetenceSaisie('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

      {/* En-tête : retour + titre + matière · niveau du profil (ou de la séance affichée) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={() => onNavigate('mes-contenus')}
          title="Revenir à Mes contenus"
          style={{ fontSize: 12, color: '#475569', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 6, padding: '5px 12px', cursor: 'pointer' }}
        >
          ← Mes contenus
        </button>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: '#1e293b', margin: 0 }}>Séance</h2>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 6, padding: '4px 10px' }}>
          {(seance?.matiere || matiere || '—')} · {(seance?.niveau || niveau || '—')}
        </span>
        {lecture && (
          <span title="La modification d'une séance arrive avec le branchement de la génération"
            style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', background: '#f1f5f9', borderRadius: 99, padding: '2px 10px' }}>
            Lecture seule
          </span>
        )}
      </div>

      {/* Thème / objectif */}
      <div style={CARTE}>
        <label style={LABEL}>Thème / objectif de la séance</label>
        <textarea
          value={theme}
          onChange={e => setTheme(e.target.value)}
          placeholder="Décrivez le thème ou l'objectif de la séance…"
          rows={2}
          disabled={lecture}
          style={{ ...champStyle, resize: 'vertical' }}
        />
      </div>

      {/* Contexte rapide */}
      <div style={CARTE}>
        <label style={LABEL}>Contexte rapide <span style={{ textTransform: 'none', fontWeight: 400, color: '#94a3b8' }}>(optionnel)</span></label>
        <input
          type="text"
          value={contexte}
          onChange={e => setContexte(e.target.value)}
          placeholder="Infos contextuelles…"
          disabled={lecture}
          style={champStyle}
        />
      </div>

      {/* Durée : liste OU minutes libres (le champ libre prime) */}
      <div style={CARTE}>
        <label style={LABEL}>Durée</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <select
            value={dureeListe}
            onChange={e => setDureeListe(e.target.value)}
            disabled={lecture}
            title="Choisir une durée courante"
            style={{ ...champStyle, width: 160, color: dureeListe ? '#1e293b' : '#94a3b8' }}
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
            disabled={lecture}
            title="Durée libre en minutes — si remplie, c'est elle qui compte"
            style={{ ...champStyle, width: 110 }}
          />
          <span style={{ fontSize: 12, color: '#64748b' }}>min</span>
        </div>
      </div>

      {/* Mode de séance — rien de pré-coché */}
      <div style={CARTE}>
        <label style={LABEL}>Mode de séance</label>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {MODES.map(m => (
            <Pastille key={m.id} actif={mode === m.id} label={m.label} title={m.desc}
              onClick={() => setMode(m.id)} disabled={lecture} />
          ))}
        </div>
      </div>

      {/* Compétences / attendus */}
      <div style={CARTE}>
        <label style={LABEL}>Compétences / attendus</label>
        {competences.length > 0 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {competences.map((c, i) => (
              <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#1e293b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 99, padding: '3px 10px' }}>
                {c}
                {!lecture && (
                  <button type="button" onClick={() => setCompetences(prev => prev.filter((_, j) => j !== i))}
                    title="Retirer cette compétence"
                    style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: 0, fontSize: 13, lineHeight: 1 }}>
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>
        )}
        {!lecture && (
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={competenceSaisie}
              onChange={e => setCompetenceSaisie(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); ajouterCompetence() } }}
              placeholder="Ex : identifier les personnages d'un récit…"
              style={{ ...CHAMP, flex: 1 }}
            />
            <button type="button" onClick={ajouterCompetence} title="Ajouter cette compétence à la liste"
              style={{ fontSize: 12, fontWeight: 600, color: '#475569', background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: 6, padding: '0 14px', cursor: 'pointer', whiteSpace: 'nowrap' }}>
              + Ajouter
            </button>
          </div>
        )}
        {lecture && competences.length === 0 && (
          <p style={{ fontSize: 12.5, color: '#94a3b8', margin: 0 }}>Aucune compétence renseignée sur cette séance.</p>
        )}
      </div>

      {/* Matériel nécessaire */}
      <div style={CARTE}>
        <label style={LABEL}>Matériel nécessaire</label>
        <input
          type="text"
          value={materiel}
          onChange={e => setMateriel(e.target.value)}
          placeholder="Liste du matériel…"
          disabled={lecture}
          style={champStyle}
        />
      </div>

      {/* Déroulé : séance existante = le contenu généré ; création = l'esquisse A/B/C */}
      <div style={CARTE}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <label style={LABEL}>Déroulé de la séance</label>
          {lecture && seance?.resultat && (
            <button type="button" onClick={() => imprimerApercu(corpsHtml(seance.resultat))}
              title="Imprimer cette séance mise en forme" className="btn-secondary">
              <IconPrint /> Imprimer
            </button>
          )}
        </div>
        {lecture ? (
          seance?.resultat ? (
            <>
              <div className="apercu-corps" style={{ color: '#1e293b', lineHeight: 1.7, fontSize: 14, background: '#f8fafc', border: '1px solid #f1f5f9', borderRadius: 6, padding: '14px 18px' }}
                dangerouslySetInnerHTML={{ __html: corpsHtml(seance.resultat) }} />
              <style>{`
                .apercu-corps h1,.apercu-corps h2,.apercu-corps h3{color:#0f172a;line-height:1.3;margin:1.4em 0 .4em}
                .apercu-corps h1{font-size:1.4rem}.apercu-corps h2{font-size:1.15rem}.apercu-corps h3{font-size:1.05rem}
                .apercu-corps p{margin:.6em 0}
                .apercu-corps ul,.apercu-corps ol{margin:.6em 0 .6em 1.4em;padding:0}.apercu-corps li{margin:.3em 0}
                .apercu-corps hr{border:none;border-top:1px solid #e2e8f0;margin:1.4em 0}
                .apercu-corps strong{color:#0f172a}
              `}</style>
            </>
          ) : (
            <p style={{ fontSize: 12.5, color: '#94a3b8', margin: 0 }}>Cette séance n'a pas de déroulé enregistré.</p>
          )
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
            {[
              ['a', 'A. Mise en route', 'Ex : 2-5 min, réactivation…'],
              ['b', 'B. Activité principale', 'Activité centrale…'],
              ['c', 'C. Retour / trace écrite', 'Synthèse ou évaluation…'],
            ].map(([cle, titreCol, placeholder]) => (
              <div key={cle} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#1e293b' }}>{titreCol}</span>
                <textarea
                  value={deroule[cle]}
                  onChange={e => setDeroule(prev => ({ ...prev, [cle]: e.target.value }))}
                  placeholder={placeholder}
                  rows={2}
                  title="Esquisse facultative — aSchool la respectera à la génération"
                  style={{ ...CHAMP, resize: 'vertical' }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Contraintes / consignes spéciales */}
      <div style={CARTE}>
        <label style={LABEL}>Contraintes / consignes spéciales</label>
        <input
          type="text"
          value={contraintes}
          onChange={e => setContraintes(e.target.value)}
          placeholder="Notes particulières…"
          disabled={lecture}
          style={champStyle}
        />
      </div>

      {/* Style de production — rien de pré-coché */}
      <div style={CARTE}>
        <label style={LABEL}>Style de production</label>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {STYLES.map(s => (
            <Pastille key={s.id} actif={style === s.id} label={s.label}
              onClick={() => setStyle(s.id)} disabled={lecture} />
          ))}
        </div>
      </div>

      {/* Générer — visible, pas encore branché (étape suivante : écriture dans les tables neuves) */}
      {!lecture && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '6px 0 18px' }}>
          <span
            title="Bientôt — le branchement de la génération (enregistrement dans Mes contenus) est l'étape suivante du chantier"
            style={{ fontSize: 14, fontWeight: 700, color: '#94a3b8', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 28px', cursor: 'not-allowed', display: 'inline-flex', alignItems: 'center', gap: 8 }}
          >
            Générer la séance
            <span style={{ fontSize: 9, fontWeight: 600, color: '#94a3b8', background: '#fff', borderRadius: 99, padding: '1px 6px' }}>bientôt</span>
          </span>
        </div>
      )}

    </div>
  )
}
