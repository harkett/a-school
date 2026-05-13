import { useState, useRef } from 'react'
import { fetchWithTimeout, TIMEOUT_GROQ } from '../utils/api.js'

const IconTxt = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
)

const IconImage = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
    <polyline points="21 15 16 10 5 21"/>
  </svg>
)

const IconPdf = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
    <polyline points="10 9 9 9 8 9"/>
  </svg>
)

const IconMic = ({ active }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
)

const EXEMPLES_TEXTE = {
  'Français': () => `Au XIXe siècle, le naturalisme prolonge le réalisme en s'appuyant sur les théories scientifiques de l'époque. Émile Zola définit le roman naturaliste comme une expérience conduite sur des personnages déterminés par l'hérédité et le milieu social. Dans Germinal (1885), il décrit la vie des mineurs du Nord avec une précision documentaire saisissante : les corons, la descente dans la mine, la misère des familles et les luttes syndicales naissantes.\n\nLa phrase zolienne, longue et rythmée, accumule les détails sensoriels pour immerger le lecteur dans un univers concret. Le regard du narrateur, froid et clinique, traduit l'ambition scientifique du projet : observer l'homme comme un objet d'étude soumis aux lois de la nature et de la société.`,
  'Mathématiques': () => `Dans un triangle ABC rectangle en A, on donne AB = 6 cm et BC = 10 cm.\n\n1. Calculer la longueur AC à l'aide du théorème de Pythagore.\n2. Calculer sin(B̂), cos(B̂) et tan(B̂), puis donner la valeur de l'angle B en degrés (arrondir au dixième).\n3. Calculer l'aire du triangle ABC.\n4. On appelle H le pied de la hauteur issue de A. Calculer AH.`,
  'Histoire-Géographie': () => `La Grande Guerre (1914-1918) marque une rupture dans l'histoire mondiale. Pour la première fois, les États mobilisent toutes leurs ressources : c'est la guerre totale. Côté français, 8 millions d'hommes sont mobilisés. Les tranchées s'étendent sur 750 km.\n\nLe front arrière est tout aussi mobilisé : les femmes remplacent les hommes dans les usines. L'industrie de guerre tourne à plein régime. Au total, le conflit fait près de 10 millions de morts militaires et 7 millions de civils.`,
  'Physique-Chimie': () => `Lors de la combustion du méthane dans le dioxygène, on obtient du dioxyde de carbone et de l'eau :\n\nCH₄ + 2 O₂ → CO₂ + 2 H₂O\n\nCette équation respecte la loi de conservation de la matière : le nombre d'atomes de chaque élément est identique avant et après la réaction. La réaction est exothermique : elle libère de l'énergie sous forme de chaleur et de lumière (ΔH = −890 kJ/mol).`,
  'SVT': () => `La photosynthèse est le processus par lequel les végétaux chlorophylliens fabriquent leur matière organique à partir de matière minérale, en utilisant l'énergie lumineuse. Elle se déroule dans les chloroplastes.\n\nÉquation simplifiée :\n6 CO₂ + 6 H₂O + énergie lumineuse → C₆H₁₂O₆ + 6 O₂\n\nElle se déroule en deux phases : les réactions photochimiques (qui captent la lumière) et le cycle de Calvin (qui fixe le CO₂). Elle est à la base de toutes les chaînes alimentaires.`,
  'SES': () => `Le marché est un lieu de rencontre entre offreurs et demandeurs d'un bien. Le prix d'équilibre est celui pour lequel les quantités offertes égalent les quantités demandées.\n\nQuand le prix augmente, les producteurs souhaitent vendre davantage mais les consommateurs achètent moins. À l'inverse, quand le prix baisse, la demande augmente et l'offre diminue.\n\nCependant, ce mécanisme a des limites : monopoles, externalités négatives, biens publics, asymétries d'information. L'État intervient pour corriger ces défaillances.`,
  'NSI': () => `Un algorithme de tri permet de réorganiser les éléments d'une liste. Le tri par sélection : on cherche le plus petit élément, on le place en tête, puis on recommence sur le reste.\n\nImplémentation en Python :\n\ndef tri_selection(liste):\n    n = len(liste)\n    for i in range(n):\n        min_idx = i\n        for j in range(i+1, n):\n            if liste[j] < liste[min_idx]:\n                min_idx = j\n        liste[i], liste[min_idx] = liste[min_idx], liste[i]\n    return liste\n\nComplexité temporelle : O(n²) dans tous les cas.`,
  'Philosophie': () => `"L'homme est condamné à être libre" — Jean-Paul Sartre, L'existentialisme est un humanisme (1945)\n\nPour Sartre, l'être humain n'a pas d'essence préalable à son existence. L'homme n'est rien d'autre que ce qu'il se fait. Cette liberté radicale est une condamnation : nous sommes responsables de tout ce que nous faisons, sans pouvoir nous réfugier derrière la nature, Dieu ou la société.\n\nCette conception s'oppose au déterminisme, qui affirme que nos actions sont entièrement causées par des facteurs extérieurs. Pour Sartre, même dans les pires situations, il reste toujours une marge de liberté.`,
  'Langues Vivantes (LV)': () => `Climate change is one of the most pressing challenges of our time. Scientists agree that human activities, particularly the burning of fossil fuels, have significantly increased greenhouse gas concentrations.\n\nIn recent years, extreme weather events have become more frequent. Floods, droughts, and wildfires are affecting communities worldwide. Young people are increasingly worried and are taking action through movements like Fridays for Future.\n\nGovernments are under pressure to reduce carbon emissions and invest in renewables. However, experts warn that current commitments are insufficient to limit warming to 1.5°C.`,
  'Technologie': () => `Un système automatisé comprend trois parties fonctionnelles :\n\n— La partie opérative (PO) : effectue les actions mécaniques (moteurs, vérins, capteurs)\n— La partie commande (PC) : traite les informations et envoie les ordres (automate programmable)\n— La partie relation homme-machine (HMI) : interface entre l'opérateur et le système\n\nExemple : une machine à laver. Le tambour (PO) tourne grâce au moteur. L'automate (PC) gère les cycles selon le programme. Le tableau de bord (HMI) permet à l'utilisateur de choisir le programme.`,
  'Arts': () => `Claude Monet peint La Cathédrale de Rouen en trente tableaux entre 1892 et 1894. Revenant au même motif à différentes heures, il saisit les effets changeants de la lumière sur la pierre.\n\nLa touche est fragmentée, nerveuse, souvent appliquée en couches épaisses. Les couleurs varient radicalement : bleus froids à l'aube, orangés dorés en plein soleil, gris laiteux dans la brume. L'architecture disparaît presque, dissoute dans la vibration lumineuse.\n\nCette série illustre les principes impressionnistes : primauté de la sensation visuelle, intérêt pour l'éphémère plutôt que pour la forme permanente.`,
  'EPS': () => `La nage libre (crawl) repose sur la coordination de quatre éléments techniques :\n\n1. Position du corps : horizontale, tête dans l'axe, hanches hautes pour réduire la résistance\n2. Mouvement des bras : traction en S sous l'eau, sortie du coude, entrée de la main dans le prolongement de l'épaule\n3. Battements de jambes : alternés, réguliers, chevilles souples — 6 battements par cycle de bras en sprint\n4. Respiration : rotation de la tête vers le côté, inspiration rapide, expiration sous l'eau\n\nL'erreur la plus fréquente : lever la tête pour respirer, ce qui casse la position et augmente la résistance.`,
}

const IconExemple = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4m0 0h18"/>
  </svg>
)

export default function TexteSource({ texte, onChange, objet, onObjetChange, matiere }) {
  const [isListening, setIsListening] = useState(false)
  const [ocrLoading, setOcrLoading] = useState(null) // 'image' | 'pdf' | null
  const [ocrErreur, setOcrErreur] = useState(null)
  const recognitionRef = useRef(null)
  const activeRef = useRef(false)
  const accumulatedRef = useRef('')
  const textareaRef = useRef(null)

  function handleTxt(e) {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => onChange(ev.target.result)
    reader.readAsText(file, 'utf-8')
    e.target.value = ''
  }

  async function handleOcr(e, type) {
    const file = e.target.files[0]
    if (!file) return
    e.target.value = ''
    setOcrErreur(null)
    setOcrLoading(type)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetchWithTimeout('/api/ocr', {
        method: 'POST',
        credentials: 'include',
        body: form,
      }, TIMEOUT_GROQ)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `Erreur ${res.status}`)
      onChange(data.texte)
    } catch (err) {
      setOcrErreur(err.message)
    } finally {
      setOcrLoading(null)
    }
  }

  function startRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = 'fr-FR'
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript
        if (event.results[i].isFinal) final += t
        else interim += t
      }
      if (final) {
        accumulatedRef.current = accumulatedRef.current + (accumulatedRef.current ? ' ' : '') + final.trim()
        onChange(accumulatedRef.current)
      } else if (interim) {
        onChange(accumulatedRef.current + (accumulatedRef.current ? ' ' : '') + interim)
      }
    }

    recognition.onerror = (e) => {
      if (e.error === 'not-allowed') {
        alert('Accès au microphone refusé — autorisez-le dans les paramètres du navigateur.')
        activeRef.current = false
        setIsListening(false)
      }
    }

    recognition.onend = () => {
      if (activeRef.current) {
        startRecognition()
      } else {
        setIsListening(false)
      }
    }

    recognitionRef.current = recognition
    recognition.start()
  }

  function toggleDicte() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Dictée vocale non supportée par ce navigateur.')
      return
    }
    if (activeRef.current) {
      activeRef.current = false
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }
    activeRef.current = true
    accumulatedRef.current = texte
    setIsListening(true)
    textareaRef.current?.focus()
    startRecognition()
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      <div className="mb-3" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Texte source</div>
        <button
          type="button"
          title="Pré-remplir avec un texte exemple adapté à votre matière — pour tester aSchool sans avoir de texte sous la main"
          onClick={() => onChange((EXEMPLES_TEXTE[matiere] || EXEMPLES_TEXTE['Français'])())}
          style={{ fontSize: '11px', color: '#6366f1', background: 'none', border: '1px solid #c7d2fe',
            borderRadius: '5px', padding: '3px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
        >
          <IconExemple />
          Tester un exemple
        </button>
      </div>

      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-500 mb-1">
          Objet <span className="font-normal text-gray-400">(optionnel — pour retrouver l'activité facilement)</span>
        </label>
        <input
          type="text"
          value={objet || ''}
          onChange={e => onObjetChange && onObjetChange(e.target.value)}
          placeholder="Ex : Dictée sur les accords, QCM chapitre 3 photosynthèse…"
          maxLength={150}
          className="w-full border border-gray-200 rounded px-3 py-2 text-sm text-gray-700 focus:outline-none focus:border-blue-400"
        />
      </div>

      <textarea
        ref={textareaRef}
        className="w-full border border-gray-300 rounded p-3 text-sm resize-y"
        rows={8}
        value={texte}
        onChange={e => onChange(e.target.value)}
        placeholder={"Collez un extrait de texte ici\n— ou importez un fichier TXT\n— ou extrayez le texte d'une image (scan, photo)\n— ou extrayez le texte d'un PDF\n— ou dictez avec le micro"}
        style={isListening ? { borderColor: '#fca5a5', outline: 'none', boxShadow: '0 0 0 2px #fecaca' } : {}}
      />

      {isListening && (
        <div style={{
          marginTop: 6,
          padding: '7px 12px',
          background: '#fff1f2',
          border: '1px solid #fca5a5',
          borderRadius: 6,
          fontSize: 12,
          color: '#dc2626',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{ fontSize: 16, lineHeight: 1 }}>🎤</span>
          <span>Dictée active — parlez maintenant. Le texte s'affiche automatiquement. Cliquez <strong>Arrêter</strong> pour terminer.</span>
        </div>
      )}

      {ocrErreur && (
        <div className="mt-2 bg-red-50 border border-red-200 text-red-700 rounded p-2 text-xs">
          {ocrErreur}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2">

        <label
          className="btn-action"
          title="Importer un fichier texte .txt"
        >
          <IconTxt />
          Fichier TXT
          <input type="file" accept=".txt,text/plain" className="hidden" onChange={handleTxt} />
        </label>

        <label
          className="btn-action"
          title="Extraire le texte d'une image (scan, photo de document)"
          style={ocrLoading === 'image' ? { opacity: 0.6, pointerEvents: 'none' } : {}}
        >
          <IconImage />
          {ocrLoading === 'image' ? 'Extraction…' : 'Image / Scan'}
          <input type="file" accept="image/jpeg,image/png,.jpg,.jpeg,.png" className="hidden"
            onChange={e => handleOcr(e, 'image')} disabled={!!ocrLoading} />
        </label>

        <label
          className="btn-action"
          title="Extraire le texte d'un PDF (PDF numérique uniquement — pas les PDF scannés)"
          style={ocrLoading === 'pdf' ? { opacity: 0.6, pointerEvents: 'none' } : {}}
        >
          <IconPdf />
          {ocrLoading === 'pdf' ? 'Extraction…' : 'PDF'}
          <input type="file" accept="application/pdf,.pdf" className="hidden"
            onChange={e => handleOcr(e, 'pdf')} disabled={!!ocrLoading} />
        </label>

        <button
          className="btn-action"
          title={isListening ? 'Cliquez pour arrêter la dictée' : 'Cliquer pour dicter — parlez en français, cliquez à nouveau pour arrêter'}
          onClick={toggleDicte}
          style={isListening ? { color: '#dc2626', borderColor: '#fca5a5', background: '#fff1f2' } : {}}
        >
          <IconMic active={isListening} />
          {isListening ? 'Arrêter' : 'Dicter'}
        </button>


      </div>
    </section>
  )
}
