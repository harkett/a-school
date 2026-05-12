import { useState, useRef } from 'react'
import { fetchWithTimeout, TIMEOUT_GROQ, TIMEOUT_STD } from '../utils/api.js'

const DUREES = [30, 45, 50, 55, 60, 90, 120]

const _LYCEE   = ['Seconde', '1ère', 'Terminale', 'CAP', 'Bac Pro']
const _COL_BAS = ['6e', '5e']

const _EX = {
  'Français': {
    bas:   ['Le conte merveilleux', 'La fable de La Fontaine', 'Décrire un personnage'],
    haut:  ['Le point de vue narratif', 'Le texte argumentatif', 'La nouvelle réaliste au XIXe'],
    lycee: ['Le commentaire littéraire', 'La dissertation sur un texte de Camus', 'L\'analyse d\'un poème de Rimbaud'],
  },
  'Mathématiques': {
    bas:   ['La proportionnalité', 'Les fractions', 'La symétrie axiale'],
    haut:  ['Les fonctions affines', 'Le théorème de Pythagore', 'Les probabilités'],
    lycee: ['Les dérivées de fonctions', 'Les suites arithmétiques et géométriques', 'Les probabilités conditionnelles'],
  },
  'Histoire-Géographie': {
    bas:   ['L\'Antiquité grecque et romaine', 'Les grandes découvertes', 'La ville et ses quartiers'],
    haut:  ['La Première Guerre mondiale', 'La Révolution française', 'Les espaces ruraux en France'],
    lycee: ['La Seconde Guerre mondiale et ses mémoires', 'La mondialisation', 'Les territoires ultramarins français'],
  },
  'Physique-Chimie': {
    bas:   ['La lumière et les ombres', 'Les mélanges et corps purs', 'La matière et ses états'],
    haut:  ['Les réactions chimiques', 'Le circuit électrique en série et en dérivation', 'Les forces et la résultante'],
    lycee: ['La cinématique et les lois de Newton', 'La thermodynamique', 'L\'électrochimie et les piles'],
  },
  'SVT': {
    bas:   ['La cellule végétale', 'Les êtres vivants dans leur milieu', 'L\'alimentation et la digestion'],
    haut:  ['La division cellulaire', 'L\'hérédité et la génétique', 'La photosynthèse'],
    lycee: ['La génétique moléculaire et l\'ADN', 'L\'évolution des espèces', 'L\'immunologie et les défenses de l\'organisme'],
  },
  'SES': {
    bas:   ['Le marché et la formation des prix', 'L\'entreprise et sa valeur ajoutée', 'Le chômage et ses causes'],
    haut:  ['Le marché et la formation des prix', 'L\'entreprise et sa valeur ajoutée', 'Le chômage et ses causes'],
    lycee: ['La formation des prix sur un marché concurrentiel', 'Les inégalités sociales et la mobilité', 'Le rôle économique de l\'État'],
  },
  'NSI': {
    bas:   ['L\'algorithmique et les tris', 'Les bases de données relationnelles', 'La récursivité'],
    haut:  ['L\'algorithmique et les tris', 'Les bases de données relationnelles', 'La récursivité'],
    lycee: ['L\'algorithmique et les tris', 'Les bases de données relationnelles', 'La récursivité en Python'],
  },
  'Philosophie': {
    bas:   ['La liberté et le déterminisme', 'La conscience et l\'inconscient', 'Le travail et la technique'],
    haut:  ['La liberté et le déterminisme', 'La conscience et l\'inconscient', 'Le travail et la technique'],
    lycee: ['La liberté et le déterminisme', 'La conscience et l\'inconscient', 'Le bonheur et le devoir moral'],
  },
  'Langues Vivantes (LV)': {
    bas:   ['Se présenter et parler de sa famille', 'Les activités quotidiennes et les loisirs', 'Les animaux et la nature'],
    haut:  ['Les voyages et les transports', 'L\'environnement et le développement durable', 'Les médias et la presse'],
    lycee: ['L\'identité et la diversité culturelle', 'Les mythes fondateurs', 'Les progrès scientifiques et leurs enjeux'],
  },
  'Technologie': {
    bas:   ['Les matériaux et leurs propriétés', 'Les systèmes mécaniques simples', 'La programmation en Scratch'],
    haut:  ['La conception d\'un objet technique', 'Les systèmes automatisés', 'L\'électronique et les capteurs'],
    lycee: ['La CAO et le prototypage numérique', 'L\'électronique numérique', 'Les systèmes embarqués et l\'IoT'],
  },
  'Arts': {
    bas:   ['La couleur et ses propriétés', 'La perspective et la représentation de l\'espace', 'L\'abstraction et la figuration'],
    haut:  ['L\'impressionnisme', 'La photographie comme pratique artistique', 'L\'installation et le land art'],
    lycee: ['L\'art et le politique', 'Le corps dans l\'art contemporain', 'La matière, la forme et le geste'],
  },
  'EPS': {
    bas:   ['La course de vitesse et les départs', 'La natation — flottaison et propulsion', 'Les jeux collectifs et coopération'],
    haut:  ['La natation — nage libre 50 m', 'L\'athlétisme — saut en hauteur', 'Le handball — attaque/défense'],
    lycee: ['L\'escalade — voies de niveau 4 à 5', 'La danse contemporaine', 'Le badminton en tournoi'],
  },
}

function getPlaceholder(matiere, niveau) {
  const groupe = _LYCEE.includes(niveau) ? 'lycee' : _COL_BAS.includes(niveau) ? 'bas' : 'haut'
  const exemples = (_EX[matiere] || _EX['Français'])[groupe]
  return `Ex : ${exemples.join(' · ')}`
}

function IconGenerer() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  )
}

function IconCopy() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  )
}

function IconSave() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
      <polyline points="17 21 17 13 7 13 7 21"/>
      <polyline points="7 3 7 8 15 8"/>
    </svg>
  )
}

export default function SequenceForm({ matiere, niveau, onNavigate }) {
  const [theme, setTheme]                 = useState('')
  const [duree, setDuree]                 = useState(55)
  const [mode, setMode]                   = useState('standard')
  const [descClasse, setDescClasse]       = useState('')
  const [loading, setLoading]             = useState(false)
  const [erreur, setErreur]               = useState(null)
  const [resultat, setResultat]           = useState(null)
  const [copied, setCopied]               = useState(false)
  const [saved, setSaved]                 = useState(false)
  const resultRef = useRef(null)

  async function generer() {
    if (!theme.trim()) {
      setErreur('Saisissez le thème ou l\'objectif de la séance.')
      return
    }
    if (mode === 'remediation' && !descClasse.trim()) {
      setErreur('Décrivez la situation de votre classe pour le mode remédiation.')
      return
    }
    setErreur(null)
    setResultat(null)
    setSaved(false)
    setLoading(true)
    try {
      const res = await fetchWithTimeout('/api/generate-sequence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          theme: theme.trim(),
          matiere,
          niveau,
          duree,
          mode,
          description_classe: descClasse.trim(),
        }),
      }, TIMEOUT_GROQ)
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || `Erreur ${res.status}`)
      }
      const data = await res.json()
      setResultat(data.resultat)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    } catch (e) {
      setErreur(`Erreur : ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  function copier() {
    if (!resultat) return
    navigator.clipboard.writeText(resultat).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  async function sauvegarder() {
    if (!resultat) return
    try {
      await fetchWithTimeout('/api/mes-activites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          activite_key: 'sequence',
          activite_label: 'Séquence pédagogique',
          matiere,
          niveau,
          sous_type: mode === 'remediation' ? 'remédiation' : 'standard',
          nb: null,
          avec_correction: false,
          objet: theme.trim().substring(0, 150),
          texte_source: mode === 'remediation' ? descClasse.trim() : theme.trim(),
          resultat,
        }),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch {
      setErreur('Erreur lors de la sauvegarde.')
    }
  }

  function reinitialiser() {
    setResultat(null)
    setErreur(null)
    setSaved(false)
  }

  const canGenerer = theme.trim() && (mode !== 'remediation' || descClasse.trim())

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* Formulaire */}
      <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

        {/* Thème */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Thème / objectif de la séance
          </label>
          <textarea
            value={theme}
            onChange={e => setTheme(e.target.value)}
            placeholder={getPlaceholder(matiere, niveau)}
            disabled={loading}
            rows={2}
            style={{
              width: '100%', padding: '9px 12px', fontSize: '13px', lineHeight: 1.6,
              color: '#1e293b', border: '1px solid #cbd5e1', borderRadius: '6px',
              resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
              background: loading ? '#f8fafc' : '#fff',
            }}
          />
        </div>

        {/* Durée + Mode */}
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'flex-start' }}>

          {/* Durée */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Durée
            </label>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {DUREES.map(d => (
                <button
                  key={d}
                  onClick={() => setDuree(d)}
                  title={`Séance de ${d} minutes`}
                  disabled={loading}
                  style={{
                    padding: '5px 12px', fontSize: '12px', fontWeight: duree === d ? 700 : 400,
                    border: `1.5px solid ${duree === d ? 'var(--bordeaux)' : '#e2e8f0'}`,
                    borderRadius: '5px', cursor: loading ? 'default' : 'pointer',
                    background: duree === d ? '#fff0f0' : '#f8fafc',
                    color: duree === d ? 'var(--bordeaux)' : '#64748b',
                  }}
                >
                  {d} min
                </button>
              ))}
            </div>
          </div>

          {/* Mode */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Mode
            </label>
            <div style={{ display: 'flex', gap: '6px' }}>
              {[
                { id: 'standard',    label: 'Séance standard',        desc: 'Nouvelle séance sur le thème' },
                { id: 'remediation', label: 'Remédiation',             desc: 'La classe n\'a pas compris, on recommence autrement' },
              ].map(m => (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  title={m.desc}
                  disabled={loading}
                  style={{
                    padding: '5px 12px', fontSize: '12px', fontWeight: mode === m.id ? 700 : 400,
                    border: `1.5px solid ${mode === m.id ? 'var(--bordeaux)' : '#e2e8f0'}`,
                    borderRadius: '5px', cursor: loading ? 'default' : 'pointer',
                    background: mode === m.id ? '#fff0f0' : '#f8fafc',
                    color: mode === m.id ? 'var(--bordeaux)' : '#64748b',
                  }}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Description classe (mode remédiation uniquement) */}
        {mode === 'remediation' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Situation de la classe
            </label>
            <textarea
              value={descClasse}
              onChange={e => setDescClasse(e.target.value)}
              placeholder="Ex : Ma classe est fatiguée, ils n'ont pas compris la photosynthèse, et ils adorent le jeu vidéo."
              disabled={loading}
              rows={2}
              style={{
                width: '100%', padding: '9px 12px', fontSize: '13px', lineHeight: 1.6,
                color: '#1e293b', border: '1px solid #c4b5fd', borderRadius: '6px',
                resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
                background: loading ? '#f8fafc' : '#faf5ff',
              }}
            />
          </div>
        )}

        {/* Matière + Niveau */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#1e293b', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '6px 12px' }}>
            {matiere} · {niveau}
          </span>
          <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>
            Pour changer →{' '}
            <button
              onClick={() => onNavigate?.('mon-profil')}
              title="Aller dans Mon profil pour modifier la matière ou le niveau"
              style={{ background: 'none', border: 'none', padding: 0, color: '#6366f1', cursor: 'pointer', fontSize: '11.5px', textDecoration: 'underline' }}
            >
              Mon profil
            </button>
          </span>
          {resultat && (
            <button
              onClick={reinitialiser}
              title="Effacer le résultat et créer une nouvelle séquence"
              style={{ padding: '5px 12px', fontSize: '12px', background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer' }}
            >
              Nouvelle séquence
            </button>
          )}
        </div>

        {/* Bouton générer — bas à droite */}
        <div className="flex justify-end">
          <button
            className="btn-primary"
            onClick={generer}
            disabled={loading || !canGenerer}
            title={!canGenerer ? 'Saisissez le thème de la séance pour générer' : 'Lancer la génération de la séquence avec A-SCHOOL'}
          >
            <IconGenerer />
            {loading ? 'Génération en cours…' : 'Générer la séquence'}
          </button>
        </div>

      </div>

      {/* Erreur */}
      {erreur && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '10px 14px', fontSize: '13px', color: '#dc2626' }}>
          {erreur}
        </div>
      )}

      {/* Résultat */}
      {resultat && (
        <div ref={resultRef} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Séquence générée
            </span>
            <div style={{ display: 'flex', gap: '7px' }}>
              <button
                onClick={copier}
                title="Copier la séquence dans le presse-papier"
                style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  padding: '5px 10px', fontSize: '12px',
                  background: copied ? '#dcfce7' : '#f1f5f9',
                  color: copied ? '#166534' : '#475569',
                  border: `1px solid ${copied ? '#86efac' : '#cbd5e1'}`,
                  borderRadius: '5px', cursor: 'pointer',
                }}
              >
                <IconCopy />
                {copied ? 'Copié' : 'Copier'}
              </button>
              <button
                onClick={sauvegarder}
                title="Sauvegarder dans Mes activités"
                style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  padding: '5px 10px', fontSize: '12px',
                  background: saved ? '#dcfce7' : '#fff0f0',
                  color: saved ? '#166534' : 'var(--bordeaux)',
                  border: `1px solid ${saved ? '#86efac' : '#fca5a5'}`,
                  borderRadius: '5px', cursor: 'pointer', fontWeight: 600,
                }}
              >
                <IconSave />
                {saved ? 'Sauvegardé' : 'Sauvegarder'}
              </button>
            </div>
          </div>
          <div style={{
            fontSize: '13px', color: '#1e293b', lineHeight: 1.8,
            whiteSpace: 'pre-wrap', fontFamily: 'inherit',
            background: '#f8fafc', borderRadius: '6px',
            padding: '14px 16px', border: '1px solid #f1f5f9',
          }}>
            {resultat}
          </div>
        </div>
      )}
    </div>
  )
}
