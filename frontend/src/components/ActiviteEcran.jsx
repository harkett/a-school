// Écran « Activité » du monde MES CONTENUS — reproduction FIDÈLE de l'écran « Créer une
// activité » existant (même ergonomie, mêmes composants réutilisés : Parametres, TexteSource,
// ZoneResultat, FriseProgression, SplitPane, JaugeAttente), avec UNE différence de fond :
// la règle 0 est NATIVE. Plus de bouton Valider/Sauvegarder — l'activité est écrite en base
// à la génération même (POST à la 1re, PUT + version aux suivantes), dans les tables NEUVES
// (`activites` + `activite_versions`). L'écran existant n'est PAS touché : il reste le
// modèle dans Mes outils jusqu'à la suppression finale de l'ancien monde.
import { useCallback, useEffect, useRef, useState } from 'react'
import Parametres from './Parametres'
import TexteSource from './TexteSource'
import ZoneResultat from './ZoneResultat'
import SplitPane from './SplitPane.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import FriseProgression from './FriseProgression.jsx'
import EtapeBadge from './EtapeBadge.jsx'
import InfoGuide from './InfoGuide.jsx'
import HistoriqueVersions from './HistoriqueVersions.jsx'
import { aideActivite } from '../utils/aideActivite.js'
import { typeVierge } from '../utils/activites.js'
import { apiFetch, detailPourEcran, lireReponse, messagePourEcran, refreshSession, TIMEOUT_STD } from '../utils/api.js'
import { showError, openFeedbackFromError } from '../errorDialog'
import { TYPES_CONTENUS } from '../utils/typesContenus.js'

// Identités de type (fichier commun) : le retour standard porte l'ambre activité ; le
// retour vers la séance mère porte le vert séance — on voit vers quel étage on remonte.
const TYPE_ACT = TYPES_CONTENUS.activite
const TYPE_SEA = TYPES_CONTENUS.seance

const MSG_ECHEC_GENERATION =
  'La génération de votre activité n\'a pas pu aboutir. Merci de réessayer.\n' +
  'Si le problème persiste, cliquez ici pour nous le signaler.'

// Même filet que l'écran modèle : détecte un texte sans rapport avec un contenu pédagogique.
function isTexteGibberish(t) {
  const words = t.trim().split(/\s+/).filter(w => w.length > 2)
  if (words.length < 2) return false
  const vowels = /[aeiouyàâäéèêëîïôöùûüæœAEIOUYÀÂÄÉÈÊËÎÏÔÖÙÛÜÆŒ]/
  let suspect = 0
  for (const word of words) {
    const alpha = word.replace(/[^a-zA-ZÀ-ÿ]/g, '')
    if (alpha.length > 8) {
      const vRatio = alpha.split('').filter(c => vowels.test(c)).length / alpha.length
      if (vRatio < 0.15) suspect++
    }
  }
  return suspect / words.length > 0.25
}

const libelleTon = t => (t === 'academique' ? 'académique' : t === 'operationnel' ? 'opérationnel' : '')

// `seanceParente` : id de la séance depuis laquelle « Créer une activité ici » a été cliqué
// (écran Séance) — l'activité NAÎTRA rattachée à cette séance, et l'écran REVIENT tout seul
// à la séance dès la génération enregistrée (onRetourSeance). Null = création libre.
export default function ActiviteEcran({ activite, seanceParente = null, onRetourSeance, matiere, niveau, email, onNavigate }) {
  // ── État miroir de l'écran modèle (types, params, texte, résultat…) ──
  const [typesActivite, setTypesActivite] = useState([])
  const [typesRate, setTypesRate] = useState(false)   // catalogue des types illisible (panne) ≠ aucun type
  const [params, setParams] = useState(() => ({
    ...typeVierge(),
    niveau,
    ...(activite ? {
      activite_type_id: activite.activite_type_id ?? null,
      sous_type: activite.sous_type || null,
      nb: activite.nb || null,
      avec_correction: !!activite.avec_correction,
    } : {}),
  }))
  const [texte, setTexte] = useState(activite?.texte_source || '')
  const [objet, setObjet] = useState(activite?.objet || '')
  const [resultat, setResultat] = useState(activite?.resultat || null)
  const [tonActuel, setTonActuel] = useState(activite?.ton || null)
  const [loading, setLoading] = useState(false)
  const [genererReplie, setGenererReplie] = useState(false)
  const [entreeDeverrouillee, setEntreeDeverrouillee] = useState(false)
  const [cahierPresent, setCahierPresent] = useState(false)
  // Règle 0 : l'identité EN BASE de l'activité de ce plan de travail (null = pas encore née).
  const [activiteId, setActiviteId] = useState(activite?.id || null)
  const [enregistrement, setEnregistrement] = useState(activite ? 'ok' : null)   // null | 'ok' | 'echec'
  const [historiqueOuvert, setHistoriqueOuvert] = useState(false)   // fenêtre « Historique des versions »
  const resultatRef = useRef(null)

  // Catalogue des types (même endpoint que l'écran modèle — un référentiel partagé, en lecture).
  // Lecture ratée : la cartouche ① ne disparaît PAS en silence (le prof croirait qu'aucun type
  // n'existe pour son couple) — message en boîte de dialogue + bouton « Réessayer » à sa place.
  const chargerTypes = useCallback(async () => {
    if (!matiere) return
    setTypesRate(false)
    try {
      const liste = await lireReponse(await apiFetch(
        `/api/activites/${encodeURIComponent(matiere)}?niveau=${encodeURIComponent(niveau || '')}`, {}, TIMEOUT_STD))
      setTypesActivite(Array.isArray(liste) ? liste : [])
    } catch (e) {
      setTypesRate(true)
      showError(messagePourEcran(e))
    }
  }, [matiere, niveau])

  useEffect(() => { chargerTypes() }, [chargerTypes])

  // Cahier des charges déposé ? (get, zéro copie — adapte les bulles d'aide, comme le modèle.)
  useEffect(() => {
    apiFetch('/api/user/cahier', {}, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => setCahierPresent(!!(d && d.present)))
      .catch(() => setCahierPresent(false))
  }, [])

  const pretAGenerer = !!texte.trim() && !!params.activite_type_id

  // ── Règle 0 : l'écriture en base suit CHAQUE génération réussie ──
  async function sauver(complet, ton) {
    const corps = {
      activite_type_id: params.activite_type_id,
      // Pas d'`activite_label` : le serveur le relit en base depuis le type (il alimente
      // « Mes stats », donc l'instantané est pris par lui, pas par l'écran).
      sous_type: params.sous_type || null,
      nb: params.nb || null,
      avec_correction: !!params.avec_correction,
      objet: objet.trim() || null,
      ton: ton || null,
      texte_source: texte,
      resultat: complet,
      // Rattachement à la naissance seulement : le serveur l'écrit au POST (création) et
      // l'ignore au PUT (une régénération ne déplace jamais l'activité).
      seance_id: seanceParente || null,
    }
    try {
      if (activiteId) {
        await lireReponse(await apiFetch(`/api/contenus/activites/${activiteId}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
        }, TIMEOUT_STD))
      } else {
        const d = await lireReponse(await apiFetch('/api/contenus/activites', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps),
        }, TIMEOUT_STD))
        setActiviteId(d.id)
      }
      setEnregistrement('ok')
      return true
    } catch {
      // Un échec d'auto-save DOIT se voir (règle 0 : rien n'attend en mémoire « pour plus tard »).
      setEnregistrement('echec')
      showError("Votre activité est affichée mais n'a pas pu être enregistrée.\n\nCliquez sur « Réessayer l'enregistrement » en haut de l'écran.")
      return false
    }
  }

  // ── Génération en STREAMING — même mécanique que l'écran modèle (SSE /api/generate). ──
  async function generer(ton) {
    if (!params.activite_type_id) {
      showError('Sélectionnez un type d\'activité avant de générer.')
      return
    }
    if (!texte.trim()) {
      showError(
        'Saisissez un texte source avant de générer — collez un extrait, dictez ou importez un fichier.' +
        (!params.avec_correction ? '\n\nSaviez-vous que vous pouvez inclure un corrigé complet ? Cochez « Avec correction » dans les paramètres.' : '')
      )
      return
    }
    if (isTexteGibberish(texte)) {
      showError('Le texte saisi ne ressemble pas à un contenu pédagogique exploitable.\n\nCollez un extrait de cours ou d\'article, dictez à la voix, ou importez un fichier.')
      return
    }
    setResultat(null)
    setTonActuel(ton || null)
    setEntreeDeverrouillee(false)
    setEnregistrement(null)
    setLoading(true)
    try {
      const body = { ...params, texte }
      if (ton) body.ton = ton
      if (!body.nb) delete body.nb
      if (!body.sous_type) delete body.sous_type
      delete body.niveau        // le couple est lu EN BASE par le serveur (décision 25/07)

      const opts = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      }
      let res = await fetch('/api/generate', opts)
      if (res.status === 401 && await refreshSession()) {
        res = await fetch('/api/generate', opts)
      }
      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}))
        const message = detailPourEcran(err)   // un 422 renvoie un tableau : filtré, jamais affiché
        if (message) showError(message)
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
      const sauve = await sauver(complet, ton)
      // Créée DEPUIS une séance : retour automatique à la séance dès l'enregistrement réussi
      // (demande 30/07) — l'activité reste à un clic dans sa cartouche ⑤ (« Ouvrir »).
      if (sauve && seanceParente && onRetourSeance) onRetourSeance()
    } catch (e) {
      console.error('génération activité (Mes contenus) :', e)
      setResultat(null)
      showError(MSG_ECHEC_GENERATION, { feedback: true })
    } finally {
      setLoading(false)
    }
  }

  const titreBarre = activite
    ? `Reprise : ${activite.objet || activite.activite_label || 'activité'}`
    : 'Nouvelle activité'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* ── Barre du haut : retour + titre + état d'enregistrement + reprises ── */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', flexShrink: 0, alignItems: 'center', gap: 8 }}>
        {/* Retour : flèche SVG grande et pleine. Standard = « Mes activités » en ambre
            activité ; depuis une séance = vert séance (demande utilisateur 30/07). */}
        <button
          type="button"
          onClick={() => (seanceParente && onRetourSeance ? onRetourSeance() : onNavigate('contenus-activites'))}
          title={seanceParente ? 'Revenir à la séance qui a créé cette activité' : 'Revenir à la page Activités'}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 7, margin: '0 0 0 8px', fontSize: 13, fontWeight: 600,
                   color: seanceParente ? TYPE_SEA.accent : TYPE_ACT.accent,
                   background: seanceParente ? TYPE_SEA.fond : TYPE_ACT.fond,
                   border: `1px solid ${seanceParente ? TYPE_SEA.bord : TYPE_ACT.bord}`,
                   borderRadius: 6, padding: '5px 12px', cursor: 'pointer', flexShrink: 0 }}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          {seanceParente ? 'Retour à la séance' : 'Mes activités'}
        </button>
        {/* Titre CENTRÉ au milieu de la barre (demande 30/07) — le filet bordeaux suit le texte. */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', justifyContent: 'center' }}>
          <span style={{ padding: '10px 12px', fontSize: '13px', fontWeight: 700, color: 'var(--bordeaux)', borderBottom: '2px solid var(--bordeaux)', marginBottom: '-1px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>
            {titreBarre}
          </span>
        </div>

        {/* Règle 0 rendue VISIBLE : l'état d'enregistrement en base, jamais un bouton Sauvegarder. */}
        {enregistrement === 'ok' && (
          <span title="Votre activité est écrite en base — retrouvez-la dans Mes contenus"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#166534', background: '#dcfce7', border: '1px solid #86efac', borderRadius: 99, padding: '3px 10px', flexShrink: 0, marginRight: 8 }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            Enregistrée
          </span>
        )}
        {enregistrement === 'echec' && (
          <button
            type="button"
            onClick={() => resultat && sauver(resultat, tonActuel)}
            title="L'enregistrement automatique a échoué — cliquez pour réessayer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: '#b91c1c', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 99, padding: '3px 10px', cursor: 'pointer', flexShrink: 0, marginRight: 8 }}
          >
            Réessayer l'enregistrement
          </button>
        )}
      </div>

      {/* ── Frise de progression + reprises « Changer votre texte / ton » (descendues de la
          barre du haut le 30/07 : en gris, à droite de la frise — la barre respire). ── */}
      <div style={{ padding: '14px 20px 12px', borderBottom: '1px solid #e2e8f0', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <FriseProgression
            typeOk={!!params.activite_type_id}
            texteOk={!!texte.trim()}
            loading={loading}
            resultat={resultat}
          />
        </div>
        {resultat && !loading && (
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setEntreeDeverrouillee(true)}
              title="Changer votre texte : rouvre votre texte source pour le modifier (réécrire, réimporter un document, redicter…), puis vous régénérez."
              style={{ flexShrink: 0 }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              Changer votre texte
            </button>
            {tonActuel && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => generer(tonActuel === 'academique' ? 'operationnel' : 'academique')}
                title={`Changer votre ton : reprend le même texte et régénère l'activité en ton ${tonActuel === 'academique' ? 'opérationnel (clair, phrases courtes)' : 'académique (formel, phrases longues)'}. L'ancienne version reste dans l'historique.`}
                style={{ flexShrink: 0 }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                Changer votre ton
              </button>
            )}
            {/* L'historique promis par les infobulles, enfin lisible : chaque jalon a figé une
                version, celle-ci s'ouvre et se restaure (règle 0). Disponible dès que l'activité
                existe en base — avant, il n'y a rien à relire. */}
            {activiteId && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setHistoriqueOuvert(true)}
                title="Historique : relire les versions précédentes de cette activité et revenir à l'une d'elles. Rien n'est jamais supprimé."
                style={{ flexShrink: 0 }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><polyline points="12 7 12 12 15 14"/></svg>
                Historique
              </button>
            )}
          </div>
        )}
      </div>

      {historiqueOuvert && activiteId && (
        <HistoriqueVersions
          base={`/api/contenus/activites/${activiteId}`}
          variante="ton"
          titre={objet.trim() || 'Votre activité'}
          aide={aideActivite('historique')}
          onFermer={() => setHistoriqueOuvert(false)}
          onRestaure={d => { setResultat(d.resultat); setTonActuel(d.ton); setEnregistrement('ok') }}
        />
      )}

      <div className="creer-corps">
        {(() => {
          const pilotage = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Catalogue illisible : la cartouche ① laisse place au bouton qui relance la
                  lecture (le message est déjà passé en boîte de dialogue — règle maison). */}
              {typesRate && typesActivite.length === 0 && (
                <section className="bg-white rounded border border-gray-200 p-4">
                  <button type="button" onClick={chargerTypes} className="btn-primary"
                    title="Recharger les types d'activité de votre matière et de votre niveau">
                    Réessayer
                  </button>
                </section>
              )}
              {typesActivite.length > 0 && (
                <Parametres
                  activites={typesActivite}
                  params={params}
                  onChange={setParams}
                  onGenerer={generer}
                  loading={loading}
                  hasResultat={!!resultat}
                  canGenerer={pretAGenerer}
                  onFeedback={() => openFeedbackFromError()}
                  verrouille={(loading || !!resultat) && !entreeDeverrouillee}
                />
              )}
              {params.activite_type_id && (
                <TexteSource
                  texte={texte} onChange={setTexte}
                  objet={objet} onObjetChange={setObjet}
                  matiere={matiere} niveau={niveau}
                  activiteTypeId={params.activite_type_id} sousType={params.sous_type}
                  verrouille={(loading || !!resultat) && !entreeDeverrouillee}
                  cahierPresent={cahierPresent}
                />
              )}
              {/* Étape ③ — les DEUX boutons de ton (le clic choisit le ton ET lance), comme le modèle. */}
              {params.activite_type_id && (
                <section className="bg-white rounded border border-gray-200 p-4">
                  <div className="section-title" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <EtapeBadge n={3} fait={!!resultat && !loading} actif={pretAGenerer && !loading && (!resultat || entreeDeverrouillee)} />
                    <span style={{ display: 'inline-flex', alignItems: 'center', fontWeight: 700 }}>
                      Générer l'activité
                      <InfoGuide {...aideActivite('generer', { cahier: cahierPresent })} />
                    </span>
                    <button
                      type="button"
                      onClick={() => setGenererReplie(r => !r)}
                      title={genererReplie ? 'Déplier' : 'Replier'}
                      style={{ marginLeft: 6, width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: genererReplie ? 'rotate(-90deg)' : 'none' }}>
                        <polyline points="6 9 12 15 18 9"/>
                      </svg>
                    </button>
                    {genererReplie && tonActuel && (
                      <span title={`Ton choisi : ${libelleTon(tonActuel)}`}
                        style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 10px', fontSize: 12, fontWeight: 600, color: '#475569', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 999, flexShrink: 0 }}>
                        Ton {libelleTon(tonActuel)}
                      </span>
                    )}
                  </div>
                  {!genererReplie && (
                    <div style={{ fontSize: 13, color: '#64748b', display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {loading ? (
                        <span className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: 0.75, cursor: 'wait', alignSelf: 'flex-start' }}>
                          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}><path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/></svg>
                          {tonActuel === 'academique' ? 'Génération en cours — ton académique…'
                            : tonActuel === 'operationnel' ? 'Génération en cours — ton opérationnel…'
                            : 'Génération en cours…'}
                        </span>
                      ) : (!resultat || entreeDeverrouillee) ? (
                        <>
                          <span style={{ fontSize: 12.5, color: '#64748b' }}>Choisissez le ton — c'est lui qui lance la génération :</span>
                          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                            <button
                              type="button"
                              className="btn-primary"
                              onClick={() => generer('academique')}
                              disabled={!pretAGenerer}
                              title={pretAGenerer ? "Générer dans un ton académique : formel, phrases longues, style « documents officiels »." : "Écrivez d'abord votre demande dans la zone de texte"}
                              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: pretAGenerer ? 1 : 0.55, cursor: pretAGenerer ? 'pointer' : 'not-allowed' }}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                              Générer — ton académique
                            </button>
                            <button
                              type="button"
                              className="btn-primary"
                              onClick={() => generer('operationnel')}
                              disabled={!pretAGenerer}
                              title={pretAGenerer ? "Générer dans un ton opérationnel : clair, phrases courtes, consignes directes, style « prof en classe »." : "Écrivez d'abord votre demande dans la zone de texte"}
                              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, opacity: pretAGenerer ? 1 : 0.55, cursor: pretAGenerer ? 'pointer' : 'not-allowed' }}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                              Générer — ton opérationnel
                            </button>
                          </div>
                        </>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#16a34a', fontWeight: 600 }}>
                          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                          Activité générée{tonActuel === 'academique' ? ' — ton académique' : tonActuel === 'operationnel' ? ' — ton opérationnel' : ''} — enregistrée automatiquement.
                        </span>
                      )}
                    </div>
                  )}
                </section>
              )}
            </div>
          )

          const colonneResultat = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {loading && (
                <JaugeAttente libelle="aSchool lit le programme officiel et rédige votre activité…" />
              )}
              {!loading && !resultat ? (
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
                  <span>Ici s'affichera votre résultat.</span>
                </div>
              ) : (
                <div ref={resultatRef}>
                  <ZoneResultat
                    resultat={resultat}
                    loading={loading}
                    email={email}
                    cahierPresent={cahierPresent}
                  />
                </div>
              )}
            </div>
          )

          return <SplitPane storageKey="contenus-activite-split-v1" gauche={pilotage} droite={colonneResultat} />
        })()}
      </div>

    </div>
  )
}
