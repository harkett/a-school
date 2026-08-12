import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, MSG_TIMEOUT } from '../utils/api.js'
import { showError } from '../errorDialog.js'

// IA › Fournisseurs & modèles — LE CATALOGUE, en liste + détail.
//
// Motif maison : la colonne de gauche liste les noms, le clic ouvre le détail à droite, et les
// modèles du fournisseur suivent dans ce même détail. Un tableau large obligeait à défiler
// horizontalement pour lire une ligne — on ne lit pas un catalogue en balayant de droite à gauche.
//
// Frontière avec l'écran Génération : ICI on gère ce qui est raccordé, LÀ-BAS on choisit dedans
// celui qui travaille.
//
// LA CLÉ N'EST PAS ICI. On saisit le NOM de sa variable d'environnement ; sa valeur reste dans le
// .env du serveur, et l'écran ne sait dire qu'une chose : présente ou absente. Un secret qui passe
// par un formulaire finit dans un journal.

const nombre = v => (v || v === 0 ? Number(v).toLocaleString('fr-FR') : '—')

// Boutons — norme maison : une icône, une bulle d'aide, la même hauteur, et le curseur « interdit »
// quand l'action est impossible. Le bleu valide, le rouge annule ou détruit, le vert ajoute.
const BTN = {
  display: 'inline-flex', alignItems: 'center', gap: 6, height: 30, padding: '0 12px',
  borderRadius: 7, fontSize: 12, fontWeight: 600, border: '1px solid transparent',
  cursor: 'pointer', whiteSpace: 'nowrap',
}
const BTN_VALIDER  = { ...BTN, background: '#2563eb', color: '#fff' }
const BTN_ANNULER  = { ...BTN, background: '#fef2f2', color: '#b91c1c', borderColor: '#fecaca' }
const BTN_AJOUTER  = { ...BTN, background: '#059669', color: '#fff' }
const BTN_NEUTRE   = { ...BTN, background: '#fff', color: '#374151', borderColor: '#d1d5db' }
const BTN_DETRUIRE = { ...BTN, background: '#fff', color: '#b91c1c', borderColor: '#fecaca' }
const grise = style => ({ ...style, opacity: 0.45, cursor: 'not-allowed' })

const IcoPlus    = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
const IcoCrayon  = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>
const IcoPoubelle= () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>
const IcoCheck   = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
const IcoCroix   = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>

function Pastille({ ok, oui, non }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600,
      padding: '2px 8px', borderRadius: 99,
      background: ok ? '#ecfdf5' : '#fef2f2', color: ok ? '#047857' : '#b91c1c',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: 99, background: ok ? '#10b981' : '#ef4444' }} />
      {ok ? oui : non}
    </span>
  )
}

function Champ({ nom, aide, children }) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: '1px solid #f3f4f6' }}>
      <span title={aide} style={{ width: 200, flexShrink: 0, fontSize: 12, color: '#6b7280' }}>{nom}</span>
      <span style={{ fontSize: 12, color: '#374151', wordBreak: 'break-all' }}>{children}</span>
    </div>
  )
}

// Champ de saisie du formulaire — même gabarit que Champ, pour que lecture et édition se
// superposent : l'œil retrouve chaque valeur à la place où il l'a lue.
function Saisie({ nom, aide, valeur, onChange, type = 'text', placeholder, options, fige }) {
  const style = { fontSize: 12, padding: '5px 8px', border: '1px solid #d1d5db', borderRadius: 6, width: '100%', maxWidth: 340 }
  return (
    <div style={{ display: 'flex', gap: 10, padding: '6px 0', borderBottom: '1px solid #f3f4f6', alignItems: 'center' }}>
      <label title={aide} style={{ width: 200, flexShrink: 0, fontSize: 12, color: '#6b7280' }}>{nom}</label>
      <div style={{ flex: 1 }}>
        {type === 'case' ? (
          <input type="checkbox" checked={!!valeur} onChange={e => onChange(e.target.checked)} style={{ cursor: 'pointer' }} />
        ) : options ? (
          <select value={valeur || ''} onChange={e => onChange(e.target.value)} style={{ ...style, cursor: 'pointer' }}>
            {options.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        ) : (
          <input
            type={type} value={valeur ?? ''} placeholder={placeholder} disabled={fige}
            onChange={e => onChange(type === 'number' ? (e.target.value === '' ? null : Number(e.target.value)) : e.target.value)}
            style={{ ...style, background: fige ? '#f9fafb' : '#fff', color: fige ? '#9ca3af' : '#111827' }}
          />
        )}
      </div>
    </div>
  )
}

const FOURNISSEUR_VIDE = { code: '', label: '', type_api: 'openai_compat', base_url: '', cle_env: '', max_tokens: null, actif: true, ordre: 0 }
const MODELE_VIDE = { modele: '', label: '', contexte_max: null, max_tokens: null, supporte_schema: true, supporte_stream: true, supporte_temperature: true, recommande: false, actif: true, ordre: 0 }

export default function AdminIAFournisseurs() {
  const [catalogue, setCatalogue] = useState(null)
  const [choisi, setChoisi]       = useState(null)
  const [erreur, setErreur]       = useState('')
  // Un seul formulaire ouvert à la fois : { quoi: 'fournisseur'|'modele', mode: 'creation'|'edition', valeurs }
  const [form, setForm]           = useState(null)
  const [occupe, setOccupe]       = useState(false)

  function charger(codeAOuvrir) {
    return fetchWithTimeout('/api/admin/ia/catalogue', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('Lecture du catalogue impossible.'))))
      .then(d => {
        setCatalogue(d)
        setChoisi(c => codeAOuvrir || c || d.courant?.fournisseur || d.fournisseurs[0]?.code || null)
      })
      .catch(e => setErreur(e.message === 'timeout' ? MSG_TIMEOUT : e.message))
  }

  useEffect(() => { charger() }, [])

  // Tout passe par ici : une seule façon d'appeler, une seule façon de dire l'échec. Le message
  // du serveur est affiché TEL QUEL — c'est lui qui sait pourquoi il a refusé.
  async function envoyer(url, methode, corps, codeAOuvrir) {
    setOccupe(true)
    try {
      const res = await fetchWithTimeout(url, {
        method: methode, credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: corps ? JSON.stringify(corps) : undefined,
      }, TIMEOUT_STD)
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        showError(d.detail || 'L’enregistrement a échoué.')
        return false
      }
      setForm(null)
      await charger(codeAOuvrir)
      return true
    } catch (e) {
      showError(e.message === 'timeout' ? MSG_TIMEOUT : 'L’enregistrement a échoué.')
      return false
    } finally {
      setOccupe(false)
    }
  }

  const courant     = catalogue?.courant || {}
  const fournisseur = catalogue?.fournisseurs.find(f => f.code === choisi) || null
  const modeles     = catalogue?.modeles.filter(m => m.fournisseur === choisi) || []
  const enService   = fournisseur && fournisseur.code === courant.fournisseur

  function validerFournisseur() {
    const v = form.valeurs
    if (form.mode === 'creation') return envoyer('/api/admin/ia/fournisseurs', 'POST', v, v.code.trim().toLowerCase())
    return envoyer(`/api/admin/ia/fournisseurs/${encodeURIComponent(v.code)}`, 'PUT', v, v.code)
  }

  function validerModele() {
    const v = { ...form.valeurs, fournisseur: choisi }
    if (form.mode === 'creation') return envoyer('/api/admin/ia/modeles', 'POST', v, choisi)
    return envoyer(`/api/admin/ia/modeles/${encodeURIComponent(choisi)}/${form.origine}`, 'PUT', v, choisi)
  }

  function supprimerFournisseur() {
    if (!confirm(`Supprimer définitivement le fournisseur « ${fournisseur.label} » ?`)) return
    envoyer(`/api/admin/ia/fournisseurs/${encodeURIComponent(fournisseur.code)}`, 'DELETE', null, null)
  }

  function supprimerModele(m) {
    if (!confirm(`Supprimer définitivement le modèle « ${m.modele} » ?`)) return
    envoyer(`/api/admin/ia/modeles/${encodeURIComponent(choisi)}/${m.modele}`, 'DELETE', null, choisi)
  }

  const maj = (cle, val) => setForm(f => ({ ...f, valeurs: { ...f.valeurs, [cle]: val } }))

  return (
    <div className="flex flex-col gap-4">

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Fournisseurs</h2>
        <p className="text-xs text-gray-400">
          Le catalogue des moteurs d’IA raccordés à l’application, et les bornes de chacun.
          Pour choisir celui qui travaille, c’est <strong>IA → Génération</strong>.
        </p>
      </div>

      {erreur && <p className="text-xs" style={{ color: '#b91c1c' }}>{erreur}</p>}
      {!catalogue && !erreur && <p className="text-xs text-gray-400">Chargement…</p>}

      {catalogue && (
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>

          {/* — Colonne de gauche : les noms — */}
          <div style={{ width: 240, flexShrink: 0 }}>
            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' }}>
              {catalogue.fournisseurs.map(f => {
                const actif = f.code === choisi
                return (
                  <div
                    key={f.code}
                    onClick={() => { setChoisi(f.code); setForm(null) }}
                    title={`Voir le détail de ${f.label}`}
                    style={{
                      padding: '11px 14px', cursor: 'pointer', borderBottom: '1px solid #f3f4f6',
                      borderLeft: actif ? '3px solid #A63045' : '3px solid transparent',
                      background: actif ? '#fdf2f4' : 'transparent',
                      fontSize: 13, fontWeight: actif ? 600 : 500,
                      color: actif ? '#A63045' : '#374151',
                    }}
                  >
                    <div>{f.label}</div>
                    <div style={{ marginTop: 3, display: 'flex', gap: 6 }}>
                      {f.code === courant.fournisseur && <span style={{ fontSize: 10, fontWeight: 700, color: '#7c3aed' }}>EN SERVICE</span>}
                      {!f.actif && <span style={{ fontSize: 10, fontWeight: 600, color: '#9ca3af' }}>désactivé</span>}
                    </div>
                  </div>
                )
              })}
            </div>
            <button
              onClick={() => setForm({ quoi: 'fournisseur', mode: 'creation', valeurs: { ...FOURNISSEUR_VIDE } })}
              title="Raccorder un nouveau service d’IA à l’application."
              style={{ ...BTN_AJOUTER, marginTop: 10, width: '100%', justifyContent: 'center' }}
            >
              <IcoPlus /> Ajouter un fournisseur
            </button>
          </div>

          {/* — Panneau de droite : détail, puis modèles — */}
          <div style={{ flex: 1, minWidth: 360, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '16px 18px' }}>

            {/* Formulaire fournisseur (création ou modification) */}
            {form?.quoi === 'fournisseur' && (
              <>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 10 }}>
                  {form.mode === 'creation' ? 'Nouveau fournisseur' : `Modifier « ${form.valeurs.label} »`}
                </h3>
                <Saisie nom="code" aide="Identifiant technique : le code utilisé par le moteur. Il ne change plus après création — les modèles et le réglage en service le référencent." valeur={form.valeurs.code} onChange={v => maj('code', v)} fige={form.mode === 'edition'} placeholder="ex. mistral" />
                <Saisie nom="label" aide="Nom affiché : ce que lit l’administrateur dans les listes." valeur={form.valeurs.label} onChange={v => maj('label', v)} placeholder="ex. Mistral AI" />
                <Saisie nom="type_api" aide="Type d’API : détermine quel client l’application construit. Seuls ces types sont compris par le moteur." valeur={form.valeurs.type_api} onChange={v => maj('type_api', v)} options={catalogue.types_api} />
                <Saisie nom="base_url" aide="Adresse d’appel : l’URL de base du service. Laisser vide pour le SDK Anthropic, qui connaît la sienne." valeur={form.valeurs.base_url} onChange={v => maj('base_url', v)} placeholder="https://…" />
                <Saisie nom="cle_env" aide="Variable de la clé : le NOM de la variable d’environnement qui porte la clé — jamais la clé elle-même." valeur={form.valeurs.cle_env} onChange={v => maj('cle_env', v)} placeholder="ex. MISTRAL_API_KEY" />
                <Saisie nom="max_tokens" aide="Réponse maximale, en tokens : ce que ce service accepte d’écrire au plus. Vide = aucun plafond connu." valeur={form.valeurs.max_tokens} onChange={v => maj('max_tokens', v)} type="number" />
                <Saisie nom="ordre" aide="Ordre d’affichage : position dans la liste de gauche." valeur={form.valeurs.ordre} onChange={v => maj('ordre', v)} type="number" />
                <Saisie nom="actif" aide="Décoché, il disparaît du choix du moteur sans être supprimé." valeur={form.valeurs.actif} onChange={v => maj('actif', v)} type="case" />
                <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                  <button onClick={validerFournisseur} disabled={occupe} title="Enregistrer ce fournisseur." style={occupe ? grise(BTN_VALIDER) : BTN_VALIDER}><IcoCheck /> Valider</button>
                  <button onClick={() => setForm(null)} disabled={occupe} title="Abandonner sans enregistrer." style={occupe ? grise(BTN_ANNULER) : BTN_ANNULER}><IcoCroix /> Annuler</button>
                </div>
              </>
            )}

            {/* Détail en lecture */}
            {!form && !fournisseur && <p className="text-xs text-gray-400">Choisissez un fournisseur à gauche.</p>}

            {form?.quoi !== 'fournisseur' && fournisseur && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', flex: 1 }}>{fournisseur.label}</h3>
                  <button
                    onClick={() => setForm({ quoi: 'fournisseur', mode: 'edition', valeurs: { ...fournisseur, base_url: fournisseur.base_url || '' } })}
                    title="Modifier les caractéristiques de ce fournisseur."
                    style={BTN_NEUTRE}
                  ><IcoCrayon /> Modifier</button>
                  <button
                    onClick={supprimerFournisseur}
                    disabled={enService || modeles.length > 0}
                    title={enService ? 'Impossible : ce fournisseur est en service.'
                          : modeles.length > 0 ? 'Impossible : supprimez d’abord ses modèles.'
                          : 'Supprimer définitivement ce fournisseur.'}
                    style={(enService || modeles.length > 0) ? grise(BTN_DETRUIRE) : BTN_DETRUIRE}
                  ><IcoPoubelle /> Supprimer</button>
                </div>

                <Champ nom="code" aide="Identifiant technique : le code utilisé par le moteur et stocké en base."><span style={{ fontFamily: 'monospace' }}>{fournisseur.code}</span></Champ>
                <Champ nom="type_api" aide="Type d’API : détermine quel client l’application construit pour lui parler.">{fournisseur.type_api}</Champ>
                <Champ nom="base_url" aide="Adresse d’appel : l’URL où partent les demandes. {produit} est remplacé par le numéro de produit du compte."><span style={{ fontFamily: 'monospace', fontSize: 11 }}>{fournisseur.base_url || '—'}</span></Champ>
                <Champ nom="cle_env" aide="Variable de la clé : seul le NOM de la variable d’environnement est connu de l’application ; la clé elle-même ne quitte jamais le serveur.">
                  <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{fournisseur.cle_env || '—'}</span>{' '}
                  <Pastille ok={fournisseur.cle_configuree} oui="présente" non="absente" />
                </Champ>
                <Champ nom="max_tokens" aide="Réponse maximale, en tokens : ce que ce fournisseur accepte d’écrire au plus. Ses modèles en héritent, sauf mention contraire.">
                  {nombre(fournisseur.max_tokens)} {fournisseur.max_tokens ? 'tokens' : ''}
                </Champ>
                <Champ nom="actif" aide="Un fournisseur désactivé n’apparaît pas dans le choix du moteur.">
                  <Pastille ok={fournisseur.actif} oui="actif" non="désactivé" />
                </Champ>

                {/* — Ses modèles, à la suite du détail — */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '20px 0 8px' }}>
                  <h4 style={{ fontSize: 12, fontWeight: 700, color: '#374151', flex: 1 }}>
                    Modèles
                    <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 600, padding: '1px 8px', borderRadius: 99, background: '#f3f4f6', color: '#6b7280', border: '1px solid #e5e7eb' }}>
                      {modeles.length}
                    </span>
                  </h4>
                  <button
                    onClick={() => setForm({ quoi: 'modele', mode: 'creation', valeurs: { ...MODELE_VIDE } })}
                    title="Offrir un modèle de plus chez ce fournisseur."
                    style={BTN_AJOUTER}
                  ><IcoPlus /> Ajouter un modèle</button>
                </div>

                {/* Formulaire modèle */}
                {form?.quoi === 'modele' && (
                  <div style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: 8, padding: '12px 14px', marginBottom: 10 }}>
                    <h5 style={{ fontSize: 12, fontWeight: 700, color: '#1e40af', marginBottom: 6 }}>
                      {form.mode === 'creation' ? 'Nouveau modèle' : `Modifier « ${form.origine} »`}
                    </h5>
                    <Saisie nom="modele" aide="Identifiant API : le nom EXACT attendu par l’API du fournisseur. Une approximation est refusée par lui, pas par nous. Il ne change plus après création." valeur={form.valeurs.modele} onChange={v => maj('modele', v)} fige={form.mode === 'edition'} placeholder="ex. mistral3" />
                    <Saisie nom="label" aide="Nom affiché : ce que lit l’administrateur dans le choix du modèle." valeur={form.valeurs.label} onChange={v => maj('label', v)} />
                    <Saisie nom="contexte_max" aide="Fenêtre totale, en tokens : le texte envoyé ET la réponse, ensemble. Au-delà, le fournisseur refuse l’appel." valeur={form.valeurs.contexte_max} onChange={v => maj('contexte_max', v)} type="number" />
                    <Saisie nom="max_tokens" aide="Réponse maximale, en tokens : ce que ce modèle accepte d’écrire au plus. Vide = celle du fournisseur s’applique." valeur={form.valeurs.max_tokens} onChange={v => maj('max_tokens', v)} type="number" />
                    <Saisie nom="supporte_schema" aide="Sait imposer un format : le modèle peut rendre du JSON contraint. Sans cela, les étapes qui l’exigent échouent." valeur={form.valeurs.supporte_schema} onChange={v => maj('supporte_schema', v)} type="case" />
                    <Saisie nom="supporte_stream" aide="Sait répondre au fil : le modèle accepte le streaming — indispensable aux appels longs." valeur={form.valeurs.supporte_stream} onChange={v => maj('supporte_stream', v)} type="case" />
                    <Saisie nom="supporte_temperature" aide="Accepte le réglage de température. Les Claude Opus 4.x et les modèles 5 la REFUSENT (erreur 400) : décoché, la température réglée dans Génération n'est pas envoyée à ce modèle." valeur={form.valeurs.supporte_temperature} onChange={v => maj('supporte_temperature', v)} type="case" />
                    <Saisie nom="recommande" aide="Le modèle mis en avant chez ce fournisseur. Un seul à la fois : le cocher le retire à l’autre." valeur={form.valeurs.recommande} onChange={v => maj('recommande', v)} type="case" />
                    <Saisie nom="ordre" aide="Ordre d’affichage : position dans la liste des modèles." valeur={form.valeurs.ordre} onChange={v => maj('ordre', v)} type="number" />
                    <Saisie nom="actif" aide="Décoché, il disparaît du choix du modèle sans être supprimé." valeur={form.valeurs.actif} onChange={v => maj('actif', v)} type="case" />
                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                      <button onClick={validerModele} disabled={occupe} title="Enregistrer ce modèle." style={occupe ? grise(BTN_VALIDER) : BTN_VALIDER}><IcoCheck /> Valider</button>
                      <button onClick={() => setForm(null)} disabled={occupe} title="Abandonner sans enregistrer." style={occupe ? grise(BTN_ANNULER) : BTN_ANNULER}><IcoCroix /> Annuler</button>
                    </div>
                  </div>
                )}

                {modeles.length === 0 && !form && (
                  <p className="text-xs text-gray-400">Aucun modèle enregistré pour ce fournisseur.</p>
                )}

                {modeles.map(m => {
                  const modeleEnService = enService && m.modele === courant.modele
                  return (
                    <div key={m.modele} style={{
                      border: '1px solid', borderColor: modeleEnService ? '#ddd6fe' : '#e5e7eb',
                      borderRadius: 8, padding: '10px 12px', marginBottom: 8,
                      background: modeleEnService ? '#f5f3ff' : '#fafafa',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 700, color: '#111827' }}>{m.modele}</span>
                        <span style={{ fontSize: 12, color: '#6b7280' }}>{m.label}</span>
                        {m.recommande && <span style={{ fontSize: 10, fontWeight: 600, color: '#6b7280' }}>(recommandé)</span>}
                        {modeleEnService && <span style={{ fontSize: 10, fontWeight: 700, color: '#7c3aed' }}>EN SERVICE</span>}
                        {!m.actif && <span style={{ fontSize: 10, fontWeight: 600, color: '#9ca3af' }}>désactivé</span>}
                        <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                          <button
                            onClick={() => setForm({ quoi: 'modele', mode: 'edition', origine: m.modele, valeurs: { ...m } })}
                            title="Modifier les caractéristiques de ce modèle."
                            style={{ ...BTN_NEUTRE, height: 26, padding: '0 9px' }}
                          ><IcoCrayon /> Modifier</button>
                          <button
                            onClick={() => supprimerModele(m)}
                            disabled={modeleEnService}
                            title={modeleEnService ? 'Impossible : ce modèle est en service.' : 'Supprimer définitivement ce modèle.'}
                            style={{ ...(modeleEnService ? grise(BTN_DETRUIRE) : BTN_DETRUIRE), height: 26, padding: '0 9px' }}
                          ><IcoPoubelle /> Supprimer</button>
                        </span>
                      </div>
                      <div style={{ marginTop: 6, display: 'flex', gap: 18, flexWrap: 'wrap', fontSize: 11, color: '#6b7280' }}>
                        {/* Mêmes noms que dans le formulaire au-dessus, et que dans la base : un champ,
                            un mot. Le sens en français est dans la bulle d'aide, jamais dans le libellé. */}
                        <span title="Fenêtre totale, en tokens : le texte envoyé ET la réponse, ensemble.">
                          contexte_max : <strong style={{ color: '#374151' }}>{nombre(m.contexte_max)}</strong>
                        </span>
                        <span title="Réponse maximale, en tokens. Vide sur le modèle = celle du fournisseur s’applique.">
                          max_tokens : <strong style={{ color: '#374151' }}>{nombre(m.max_tokens || fournisseur.max_tokens)}</strong>
                        </span>
                        <span title="Sait imposer un format : sait rendre une réponse en JSON contraint.">
                          supporte_schema : <strong style={{ color: '#374151' }}>{m.supporte_schema ? 'oui' : 'non'}</strong>
                        </span>
                        <span title="Accepte le réglage de température. Non = la valeur réglée dans Génération n'est pas envoyée à ce modèle.">
                          supporte_temperature : <strong style={{ color: '#374151' }}>{m.supporte_temperature ? 'oui' : 'non'}</strong>
                        </span>
                      </div>
                    </div>
                  )
                })}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
