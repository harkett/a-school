import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import InfoGuide from '../components/InfoGuide'

// Aide « i » des réglages — même principe que les bulles du profil (survol = court, clic = fiche
// complète épinglée). Copie d'écran centralisée ici, hors du JSX : ce n'est pas une donnée métier,
// donc elle vit dans le code (comme utils/aideProfil.js), jamais en base (RÈGLE 25).
const AIDE = {
  stream: {
    titre: 'Coupure du flux',
    court: 'Temps maximal sans nouveau texte avant d’interrompre une génération jugée bloquée.',
    long:
      'Ce paramètre correspond au temps maximal sans nouveau token avant que la génération soit ' +
      'considérée comme bloquée, et donc interrompue. Dès qu’un nouveau morceau de texte arrive, ' +
      'le compteur repart à zéro : une génération lente mais régulière n’est jamais coupée.\n\n' +
      '🎯 Valeur conseillée\n' +
      '• 30 s : la plus sûre dans 99 % des cas.\n' +
      '• 60 s : si tu fais souvent des générations longues ou complexes.\n' +
      '• > 120 s : seulement pour des modèles très lents ou des environnements saturés.\n\n' +
      '📌 Pourquoi 30 s est le meilleur compromis\n' +
      '• En dessous de 10–15 s, tu risques de couper des générations normales qui ont juste un petit délai interne.\n' +
      '• Au-dessus de 60–90 s, tu ne gagnes rien : tu attends inutilement quand un blocage réel survient.\n' +
      '• 30 s détecte vite les vraies interruptions tout en laissant respirer les modèles.',
  },
}

export default function AdminParametresGeneration() {
  const [onglet, setOnglet] = useState('modele')
  const [aiModel, setAiModel] = useState('')
  // Le modèle en service accepte-t-il `temperature` ? Certains Claude la REFUSENT (erreur 400).
  const [tempSupportee, setTempSupportee] = useState(true)
  const [tempModele, setTempModele] = useState('')
  const [supportedModels, setSupportedModels] = useState([])
  const [recommandeModel, setRecommandeModel] = useState('') // modèle marqué « recommandé » (affiché entre parenthèses)
  const [saving, setSaving]   = useState(false)
  const [message, setMessage] = useState(null) // { type: 'ok', text }

  // Fournisseur — la combo affiche TOUS les fournisseurs connus du moteur (champ `all` du backend,
  // LU EN BASE) ; les non-opérationnels sont grisés « pas encore disponible ». Source UNIQUE : la
  // base. Aucun repli en dur : `all` vide → message d'erreur clair, jamais de faux libellés.
  const [aiProvider, setAiProvider] = useState('')
  const [allProviders, setAllProviders] = useState([]) // [{ name, label, available }]
  const [providersLoaded, setProvidersLoaded] = useState(false) // distingue « en cours » de « vide »

  // Température (Phase 4.1.d) — GLOBALE. Vide = défaut du fournisseur (non réglée), sinon 0.0–2.0.
  const [temperature, setTemperature] = useState('')
  const [tempBounds, setTempBounds] = useState({ min: 0, max: 2 })
  const [savingTemp, setSavingTemp] = useState(false)
  const [messageTemp, setMessageTemp] = useState(null)

  // Coupure de SILENCE du flux de génération (streaming) — secondes, réglage admin en base.
  const [streamTimeout, setStreamTimeout] = useState('')
  const [streamBounds, setStreamBounds]   = useState({ min: 5, max: 300 })
  const [savingStream, setSavingStream]   = useState(false)
  const [messageStream, setMessageStream] = useState(null)

  // Résilience — re-tentatives automatiques quand le service d'IA est momentanément saturé (réponse
  // « trop de demandes »). Deux réglages admin en base : nb d'essais + plafond d'attente par essai.
  const [retryMax, setRetryMax]         = useState('')
  const [retryWaitMax, setRetryWaitMax] = useState('')
  const [retryBounds, setRetryBounds]   = useState({ retry_max: { min: 0, max: 5 }, retry_wait_max: { min: 1, max: 60 } })
  const [savingRetry, setSavingRetry]   = useState(false)
  const [messageRetry, setMessageRetry] = useState(null)

  useEffect(() => {
    fetch('/api/admin/ai-models', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setAiModel(data.current || '')
        setSupportedModels(data.supported || [])
        setRecommandeModel(data.recommande || '')
      })
      .catch(() => {})

    fetch('/api/admin/ai-providers', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setAiProvider(data.current || '')
        setAllProviders(data.all || [])
      })
      .catch(() => {})
      .finally(() => setProvidersLoaded(true))

    fetch('/api/admin/temperature', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setTemperature(data.temperature == null ? '' : String(data.temperature))
        if (data.bounds) setTempBounds(data.bounds)
        // `supportee` vient de la fiche du modèle en service. On le montre au lieu de laisser
        // régler une valeur que le moteur ne transmettra pas.
        setTempSupportee(data.supportee !== false)
        setTempModele(data.modele || '')
      })
      .catch(() => {})

    fetch('/api/admin/stream-timeout', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setStreamTimeout(String(data.timeout ?? ''))
        if (data.bounds) setStreamBounds(data.bounds)
      })
      .catch(() => {})

    fetch('/api/admin/retry', { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setRetryMax(String(data.retry_max ?? ''))
        setRetryWaitMax(String(data.retry_wait_max ?? ''))
        if (data.bounds) setRetryBounds(data.bounds)
      })
      .catch(() => {})
  }, [])

  // Fournisseur & modèle groupés : le modèle DÉPEND du fournisseur (l'endpoint filtre les
  // modèles par fournisseur). Changer de fournisseur recharge SES modèles (?fournisseur=)
  // et présélectionne le recommandé.
  async function onChangeFournisseur(code) {
    setAiProvider(code)
    setMessage(null)
    try {
      const res = await fetch(`/api/admin/ai-models?fournisseur=${encodeURIComponent(code)}`, { credentials: 'include' })
      const data = await res.json()
      const liste = data.supported || []
      setSupportedModels(liste)
      setRecommandeModel(data.recommande || '')
      setAiModel(data.recommande || liste[0]?.modele || '')  // présélectionne le recommandé (meilleur défaut)
    } catch {
      setSupportedModels([]); setRecommandeModel(''); setAiModel('')
    }
  }

  // Un seul enregistrement pour les deux : le fournisseur D'ABORD (le backend valide le
  // modèle contre le fournisseur ENREGISTRÉ), puis le modèle.
  async function saveFournisseurModele() {
    setSaving(true)
    setMessage(null)
    try {
      let res = await fetchWithTimeout('/api/admin/ai-provider', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ provider: aiProvider }),
      }, TIMEOUT_STD)
      let data = await res.json().catch(() => ({}))
      if (!res.ok) { showError(data.detail || 'Erreur lors de l\'enregistrement du fournisseur.'); return }

      res = await fetchWithTimeout('/api/admin/ai-model', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ model: aiModel }),
      }, TIMEOUT_STD)
      data = await res.json().catch(() => ({}))
      if (!res.ok) { showError(data.detail || 'Erreur lors de l\'enregistrement du modèle.'); return }

      setMessage({ type: 'ok', text: 'Fournisseur et modèle enregistrés.' })
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSaving(false)
    }
  }

  // Température : vide = valide (= défaut fournisseur) ; sinon nombre dans [min, max].
  const tempInvalide = v => {
    if (v === '') return false
    const n = Number(v)
    return !Number.isFinite(n) || n < tempBounds.min || n > tempBounds.max
  }

  async function saveTemperature() {
    if (tempInvalide(temperature)) {
      showError(
        `La température doit être un nombre entre ${tempBounds.min} et ${tempBounds.max}, ` +
        `ou laissée vide pour utiliser le défaut du fournisseur. Rappel : une température élevée ` +
        `rend les générations moins fiables (réponses fausses, format cassé) — pour du pédagogique, restez bas à modéré.`
      )
      return
    }
    setSavingTemp(true)
    setMessageTemp(null)
    try {
      const res = await fetchWithTimeout('/api/admin/temperature', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ temperature: temperature === '' ? null : Number(temperature) }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) setMessageTemp({ type: 'ok', text: 'Température enregistrée.' })
      else showError(data.detail || 'Erreur lors de l\'enregistrement de la température.')
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingTemp(false)
    }
  }

  // Coupure de silence : entier dans [min, max]. Vide / non entier / hors bornes = invalide.
  const streamInvalide = v => {
    const n = Number(v)
    return v === '' || !Number.isInteger(n) || n < streamBounds.min || n > streamBounds.max
  }

  async function saveStreamTimeout() {
    if (streamInvalide(streamTimeout)) {
      showError(
        `Le délai doit être un nombre entier de secondes entre ${streamBounds.min} et ${streamBounds.max}. ` +
        `C'est la coupure de SILENCE du flux (temps sans nouveau texte avant d'abandonner), pas la durée ` +
        `totale d'une génération : le compteur se remet à zéro à chaque morceau reçu.`
      )
      return
    }
    setSavingStream(true)
    setMessageStream(null)
    try {
      const res = await fetchWithTimeout('/api/admin/stream-timeout', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ timeout: Number(streamTimeout) }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) setMessageStream({ type: 'ok', text: 'Coupure du flux enregistrée.' })
      else showError(data.detail || 'Erreur lors de l\'enregistrement de la coupure du flux.')
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingStream(false)
    }
  }

  // Résilience : deux entiers dans leurs bornes. retry_max = 0 est VALIDE (aucune re-tentative).
  const retryMaxInvalide = v => {
    const n = Number(v)
    return v === '' || !Number.isInteger(n) || n < retryBounds.retry_max.min || n > retryBounds.retry_max.max
  }
  const retryWaitInvalide = v => {
    const n = Number(v)
    return v === '' || !Number.isInteger(n) || n < retryBounds.retry_wait_max.min || n > retryBounds.retry_wait_max.max
  }
  const retryInvalide = retryMaxInvalide(retryMax) || retryWaitInvalide(retryWaitMax)

  async function saveRetry() {
    if (retryInvalide) {
      showError(
        `Le nombre de re-tentatives doit être un entier entre ${retryBounds.retry_max.min} et ${retryBounds.retry_max.max} ` +
        `(0 = aucune), et l'attente maximale un entier de secondes entre ${retryBounds.retry_wait_max.min} et ${retryBounds.retry_wait_max.max}. ` +
        `Corrigez les champs en rouge avant d'enregistrer.`
      )
      return
    }
    setSavingRetry(true)
    setMessageRetry(null)
    try {
      const res = await fetchWithTimeout('/api/admin/retry', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ retry_max: Number(retryMax), retry_wait_max: Number(retryWaitMax) }),
      }, TIMEOUT_STD)
      const data = await res.json().catch(() => ({}))
      if (res.ok) setMessageRetry({ type: 'ok', text: 'Résilience enregistrée.' })
      else showError(data.detail || 'Erreur lors de l\'enregistrement de la résilience.')
    } catch {
      showError('Erreur réseau — vérifiez que le backend tourne.')
    } finally {
      setSavingRetry(false)
    }
  }

  // Ce que le bouton du bandeau fait, section par section. Une table plutôt que cinq boutons
  // recopiés : ajouter une section demain, c'est ajouter une ligne ici — et le bouton reste
  // seul, donc il ne peut pas y en avoir deux qui divergent.
  const ACTIONS = {
    modele:      { onClick: saveFournisseurModele, disabled: saving || !aiProvider || !aiModel, libelle: saving ? 'Enregistrement…' : 'Enregistrer',            titre: 'Enregistrer le fournisseur et le modèle' },
    temperature: { onClick: saveTemperature,       disabled: savingTemp || tempInvalide(temperature), libelle: savingTemp ? 'Enregistrement…' : 'Enregistrer',  titre: 'Enregistrer la température' },
    stream:      { onClick: saveStreamTimeout,     disabled: savingStream || streamInvalide(streamTimeout), libelle: savingStream ? 'Enregistrement…' : 'Enregistrer', titre: 'Enregistrer la coupure du flux' },
    retry:       { onClick: saveRetry,             disabled: savingRetry || retryInvalide,      libelle: savingRetry ? 'Enregistrement…' : 'Enregistrer',       titre: 'Enregistrer la résilience' },
  }
  const action = ACTIONS[onglet]

  return (
    <div className="flex flex-col gap-6">

      {/* Bandeau FIXE : le titre et le bouton d'enregistrement de la section ouverte, toujours
          visibles. Les cinq sections avaient chacune son bouton, posé sous ses champs — dans
          « Longueur », qui aligne dix-sept outils, il fallait dérouler tout l'écran pour le
          retrouver, et rien ne rappelait en cours de route qu'une modification attendait d'être
          enregistrée. Un seul bouton, à un seul endroit, qui ne s'en va jamais.
          `top: -24` : le conteneur de page a une marge haute ; sans ce décalage le bandeau se
          décollerait avec elle et laisserait passer les champs par-dessous. */}
      <div style={{
        position: 'sticky', top: -24, zIndex: 20, background: '#f0f4f8',
        padding: '24px 0 12px', marginBottom: -12,
        borderBottom: '1px solid #e2e8f0',
        display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap',
      }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Génération LLM</h2>
          <p className="text-xs text-gray-400">
            Réglages du moteur de génération des textes.
          </p>
        </div>
        <button
          onClick={action.onClick}
          disabled={action.disabled}
          title={action.titre}
          style={{
            background: '#1F6EEB', color: 'white', border: 'none',
            borderRadius: 7, height: 34, padding: '0 20px', fontSize: 13, fontWeight: 500,
            cursor: action.disabled ? 'not-allowed' : 'pointer',
            opacity: action.disabled ? 0.6 : 1,
            flexShrink: 0,
          }}
        >
          {action.libelle}
        </button>
      </div>

      {/* Maître-détail : liste verticale des sections à gauche, détail à droite (motif admin qui
          scale — jamais une rangée d'onglets en haut, ingérable quand le nombre de sections grandit). */}
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── Colonne gauche : liste verticale des sections ── */}
        <div style={{ width: 210, flexShrink: 0 }}>
          <div className="bg-white rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
            {/* « Longueur (tokens) » a été RETIRÉ : la longueur maximale n'est plus un réglage, elle
                vient du `max_tokens` de la fiche du modèle (IA › Fournisseurs & modèles). Laisser
                l'onglet aurait été pire que l'enlever — il aurait accepté des valeurs sans effet. */}
            {[
              ['modele', 'Fournisseur & modèle'],
              ['temperature', 'Température'],
              ['stream', 'Coupure du flux'],
              ['retry', 'Résilience'],
            ].map(([key, label]) => {
              const active = onglet === key
              return (
                <button
                  key={key}
                  onClick={() => setOnglet(key)}
                  title={label}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '10px 14px', fontSize: 13, cursor: 'pointer',
                    border: 'none', borderBottom: '1px solid #f1f5f9',
                    borderLeft: active ? '3px solid #A63045' : '3px solid transparent',
                    background: active ? '#fdf2f4' : 'white',
                    color: active ? '#A63045' : '#374151',
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  {label}
                </button>
              )
            })}
          </div>
        </div>

        {/* ── Colonne droite : détail de la section sélectionnée ── */}
        <div style={{ flex: 1, minWidth: 0 }} className="flex flex-col gap-6">

      {/* Section « Fournisseur & modèle » — REGROUPÉES car le modèle DÉPEND du fournisseur
          (l'endpoint /ai-models filtre par fournisseur). On choisit le fournisseur, ses modèles
          se rechargent dessous (?fournisseur=), un seul bouton enregistre les deux (fournisseur
          d'abord : le backend valide le modèle contre le fournisseur enregistré). */}
      {onglet === 'modele' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          {/* Fournisseur */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Fournisseur d'IA
            </label>
            <select
              value={aiProvider}
              onChange={e => onChangeFournisseur(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              {!providersLoaded && <option value="">Chargement…</option>}
              {providersLoaded && allProviders.length === 0 &&
                <option value="">Aucun fournisseur en base — vérifiez la table ai_fournisseurs</option>}
              {allProviders.map(p => (
                <option key={p.name} value={p.name} disabled={!p.available}>
                  {p.label}{p.available ? '' : ' — pas encore disponible'}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              Service d'IA qui exécute la génération. Les fournisseurs grisés ne sont pas encore
              disponibles (leur clé n'est pas configurée).
            </p>
          </div>

          {/* Modèle du fournisseur sélectionné */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Modèle de génération
            </label>
            <select
              value={aiModel}
              onChange={e => setAiModel(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            >
              {supportedModels.length === 0 && <option value="">Aucun modèle pour ce fournisseur</option>}
              {supportedModels.map(m => (
                <option key={m.modele} value={m.modele}>{m.label}{m.modele === recommandeModel ? ' (recommandé)' : ''}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              Modèle utilisé pour générer les activités. Pris en compte immédiatement, sans redémarrage.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-1">
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
      )}

      {/* L'onglet « Longueur (tokens) » a disparu ENTIÈREMENT le 10/08/2026. Son entrée avait
          déjà quitté la colonne de gauche, mais son formulaire, sa lecture et son enregistrement
          étaient restés : du code qu'aucun clic n'atteignait, et deux routes qui écrivaient des
          réglages que le moteur ne lit plus. La longueur maximale vient de la fiche du modèle
          (IA › Fournisseurs & modèles) — c'est là qu'elle se voit et qu'elle se règle. */}

      {/* Onglet Température (Phase 4.1.d) — GLOBALE. Vide = défaut du fournisseur, sinon 0.0–2.0.
          « Plus haut » N'EST PAS « mieux » : haute température = sorties moins fiables.
          Hors bornes -> bord rouge + modale + bouton off. */}
      {onglet === 'temperature' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          <p className="text-xs text-gray-500">
            Contrôle la variabilité des générations, entre {tempBounds.min} (stable, répétable) et {tempBounds.max} (très varié).
            Pour des activités fiables, rester bas à modéré : une valeur élevée rend les réponses moins sûres (erreurs, format cassé).
            Laisser vide = défaut du fournisseur. Pris en compte immédiatement, sans redémarrage.
          </p>

          {/* Le modèle en service refuse ce paramètre : on le DIT. Avant, la valeur était saisie,
              enregistrée, puis jetée en silence par le moteur — l'admin croyait avoir agi. */}
          {!tempSupportee && (
            <div style={{
              background: '#fffbeb', border: '1px solid #fde68a', color: '#92400e',
              borderRadius: 8, padding: '10px 14px', fontSize: 12,
            }}>
              Le modèle en service{tempModele ? ` (${tempModele})` : ''} <strong>n’accepte pas</strong> la
              température : elle ne lui sera pas envoyée. La valeur ci-dessous reste enregistrée et
              redeviendra active dès qu’un modèle qui l’accepte sera choisi.
              <br />
              Cela se règle sur la fiche du modèle, case <strong>supporte_temperature</strong>
              {' '}(IA → Fournisseurs).
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Température (vide = défaut du fournisseur)
            </label>
            <input
              type="number"
              step="0.1"
              min={tempBounds.min}
              max={tempBounds.max}
              value={temperature}
              onChange={e => setTemperature(e.target.value)}
              placeholder="Défaut du fournisseur"
              className="w-full border rounded px-3 py-2 text-sm"
              style={{ borderColor: tempInvalide(temperature) ? '#dc2626' : '#d1d5db' }}
            />
          </div>

          <div className="flex flex-col gap-3 pt-1">
            {messageTemp && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
                borderRadius: 8, padding: '10px 14px', fontSize: 13,
              }}>
                {messageTemp.text}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Onglet Coupure du flux — coupure de SILENCE du streaming de génération (secondes).
          Ce n'est PAS la durée totale : le compteur se réarme à chaque morceau reçu, seuls les
          silences anormaux coupent. Hors bornes -> bord rouge + modale + bouton off. */}
      {onglet === 'stream' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          <p className="text-xs text-gray-500">
            Coupure de <strong>silence</strong> du flux de génération : nombre de secondes sans nouveau
            texte avant d'abandonner. Ce n'est PAS la durée totale d'une génération — le compteur se
            remet à zéro à chaque morceau reçu, donc une génération qui progresse n'est jamais coupée.
            Entre {streamBounds.min} et {streamBounds.max} s. Pris en compte immédiatement, sans redémarrage.
          </p>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Coupure de silence (secondes)
              <InfoGuide titre={AIDE.stream.titre} court={AIDE.stream.court} long={AIDE.stream.long} />
            </label>
            <input
              type="number"
              min={streamBounds.min}
              max={streamBounds.max}
              value={streamTimeout}
              onChange={e => setStreamTimeout(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              style={{ borderColor: streamInvalide(streamTimeout) ? '#dc2626' : '#d1d5db' }}
            />
            <p className="text-xs text-gray-400 mt-1">
              Défaut 30 s. Trop bas = des générations lentes mais normales seraient coupées à tort.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-1">
            {messageStream && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
                borderRadius: 8, padding: '10px 14px', fontSize: 13,
              }}>
                {messageStream.text}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Onglet Résilience — re-tentatives automatiques quand le service d'IA répond « trop de
          demandes » (saturation momentanée). Le prof ne voit rien : le back attend le délai conseillé
          (plafonné) et ré-essaie. Hors bornes -> bord rouge + modale bloquante + bouton désactivé. */}
      {onglet === 'retry' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">
          <p className="text-xs text-gray-500">
            Quand le service d'IA est momentanément saturé et répond « trop de demandes », le moteur
            ré-essaie tout seul au lieu d'abandonner — l'enseignant ne voit rien. Il respecte le délai
            conseillé par le service, sans jamais dépasser le plafond ci-dessous.
            Pris en compte immédiatement, sans redémarrage.
          </p>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Nombre de re-tentatives
            </label>
            <input
              type="number"
              min={retryBounds.retry_max.min}
              max={retryBounds.retry_max.max}
              value={retryMax}
              onChange={e => setRetryMax(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              style={{ borderColor: retryMaxInvalide(retryMax) ? '#dc2626' : '#d1d5db' }}
            />
            <p className="text-xs text-gray-400 mt-1">
              Défaut 2. Mettre 0 désactive les re-tentatives (abandon au premier refus du service).
            </p>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Attente maximale par tentative (secondes)
            </label>
            <input
              type="number"
              min={retryBounds.retry_wait_max.min}
              max={retryBounds.retry_wait_max.max}
              value={retryWaitMax}
              onChange={e => setRetryWaitMax(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
              style={{ borderColor: retryWaitInvalide(retryWaitMax) ? '#dc2626' : '#d1d5db' }}
            />
            <p className="text-xs text-gray-400 mt-1">
              Défaut 10 s. Plafonne l'attente : si le service demande davantage, on n'attend jamais
              au-delà de cette valeur, pour ne pas faire patienter l'enseignant trop longtemps.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-1">
            {messageRetry && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534',
                borderRadius: 8, padding: '10px 14px', fontSize: 13,
              }}>
                {messageRetry.text}
              </div>
            )}
          </div>
        </div>
      )}

      </div>{/* fin colonne droite (détail) */}
      </div>{/* fin maître-détail */}
    </div>
  )
}
