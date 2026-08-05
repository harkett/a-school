import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchWithTimeout } from '../utils/api.js'
import { demanderConfirmation } from '../confirmDialog'
import { VARIABLES_EMAIL, apercuVariables } from '../utils/variablesEmail.js'

const CLE_MODELES = ['admin', 'email-templates']

export default function AdminParametresEmail() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState(null)
  // Le formulaire est un BROUILLON de la ligne lue : null = « rien de tapé, montre la base ».
  // Il n'y a donc rien à recopier quand la sélection change — le brouillon repart à null et
  // l'écran réaffiche ce que le serveur dit, sans effet de synchronisation.
  const [brouillon, setBrouillon] = useState(null)
  const [saving, setSaving]   = useState(false)
  const [busy, setBusy]       = useState(false)      // envoi / test en cours
  const [message, setMessage] = useState(null)       // { type: 'ok'|'err', text }

  const [showAdd, setShowAdd]   = useState(false)     // modale « Ajouter un mail »
  const [newName, setNewName]   = useState('')
  const [showSend, setShowSend] = useState(false)     // modale « Envoyer maintenant »
  const [sendTo, setSendTo]     = useState('')

  const [tab, setTab]           = useState('modeles') // 'modeles' | 'suivi'

  // Les modèles d'e-mail, lus en base — react-query tient la lecture ; l'écran n'a plus d'état
  // « en cours » à poser lui-même.
  const { data: templates = [], isPending: loading } = useQuery({
    queryKey: CLE_MODELES,
    queryFn: async () => {
      const res = await fetch('/api/admin/email-templates', { credentials: 'include' })
      return await res.json()
    },
  })

  // L'historique des envois ne se lit QUE si l'onglet « Suivi » est ouvert — inutile de le
  // demander au serveur pour un onglet que l'admin ne regarde pas.
  const { data: envois = [], isFetching: envoisLoading } = useQuery({
    queryKey: ['admin', 'email-envois'],
    enabled: tab === 'suivi',
    queryFn: async () => {
      const res = await fetch('/api/admin/email-envois', { credentials: 'include' })
      const data = await res.json()
      return Array.isArray(data) ? data : []
    },
  })

  // Le modèle affiché : celui qu'on a choisi, sinon le premier de la liste. C'est un CALCUL,
  // pas une sélection posée après coup — la liste arrive, le premier modèle s'affiche.
  const selected = templates.find(t => t.id === selectedId) || templates[0] || null

  const form = brouillon ?? {
    description: selected?.description || '',
    objet: selected?.objet || '',
    corps: selected?.corps || '',
  }
  const setForm = (maj) => setBrouillon(f => (typeof maj === 'function' ? maj(f ?? form) : maj))

  // Remplace l'ancien setTemplates : la liste lue reste LA liste, on la corrige au même
  // endroit que react-query la garde — pas de seconde copie dans l'écran.
  function majTemplates(maj) { queryClient.setQueryData(CLE_MODELES, maj) }

  function selectTemplate(t) {
    setSelectedId(t.id)
    setBrouillon(null)     // on repart de ce qui est en base pour ce modèle
    setMessage(null)
  }

  async function save() {
    if (!selected) return
    setSaving(true)
    setMessage(null)
    try {
      const res = await fetchWithTimeout(`/api/admin/email-templates/${selected.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ description: form.description, objet: form.objet, corps: form.corps }),
      })
      const data = await res.json().catch(() => ({}))
      if (res.ok) {
        majTemplates(ts => (ts || []).map(t => t.id === data.id ? data : t))
        setBrouillon(null)   // c'est enregistré : la base redevient la vérité affichée
        setMessage({ type: 'ok', text: 'Modèle enregistré.' })
      } else {
        setMessage({ type: 'err', text: data.detail || 'Erreur lors de l\'enregistrement.' })
      }
    } catch {
      setMessage({ type: 'err', text: 'Erreur réseau — vérifiez que le backend tourne.' })
    } finally {
      setSaving(false)
    }
  }

  async function addTemplate() {
    const nom = newName.trim()
    if (!nom) return
    setBusy(true)
    try {
      const res = await fetchWithTimeout('/api/admin/email-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ nom }),
      })
      const data = await res.json().catch(() => ({}))
      if (res.ok) {
        majTemplates(ts => [...(ts || []), data])
        selectTemplate(data)
        setShowAdd(false)
        setNewName('')
      } else {
        setMessage({ type: 'err', text: data.detail || 'Erreur lors de la création.' })
      }
    } finally {
      setBusy(false)
    }
  }

  async function removeTemplate() {
    if (!selected || !selected.supprimable) return
    if (!await demanderConfirmation({
      titre: `Supprimer le modèle « ${selected.nom} » ?`,
      message: 'Ce modèle d’e-mail sera perdu. Cette action est définitive.',
      confirmLabel: 'Supprimer',
      danger: true,
    })) return
    setBusy(true)
    try {
      const res = await fetchWithTimeout(`/api/admin/email-templates/${selected.id}`, {
        method: 'DELETE', credentials: 'include',
      })
      if (res.ok) {
        const rest = templates.filter(t => t.id !== selected.id)
        majTemplates(rest)
        if (rest.length) selectTemplate(rest[0]); else { setSelectedId(null); setBrouillon(null) }
      } else {
        const data = await res.json().catch(() => ({}))
        setMessage({ type: 'err', text: data.detail || 'Erreur lors de la suppression.' })
      }
    } finally {
      setBusy(false)
    }
  }

  async function sendNow() {
    const to = sendTo.trim()
    if (!selected || !to) return
    setBusy(true)
    setMessage(null)
    try {
      const res = await fetchWithTimeout(`/api/admin/email-templates/${selected.id}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ to }),
      })
      const data = await res.json().catch(() => ({}))
      if (res.ok) {
        setMessage({ type: 'ok', text: `Email envoyé à ${to}.` })
        setShowSend(false)
        setSendTo('')
      } else {
        setMessage({ type: 'err', text: data.detail || 'Erreur lors de l\'envoi.' })
      }
    } catch {
      setMessage({ type: 'err', text: 'Erreur réseau — vérifiez que le backend tourne.' })
    } finally {
      setBusy(false)
    }
  }

  async function sendTest() {
    if (!selected) return
    setBusy(true)
    setMessage(null)
    try {
      const res = await fetchWithTimeout(`/api/admin/email-templates/${selected.id}/test`, {
        method: 'POST', credentials: 'include',
      })
      const data = await res.json().catch(() => ({}))
      setMessage(res.ok
        ? { type: 'ok', text: 'Test réussi — email envoyé à l\'adresse d\'administration.' }
        : { type: 'err', text: data.detail || 'Erreur envoi email de test.' }
      )
    } catch {
      setMessage({ type: 'err', text: 'Erreur réseau — vérifiez que le backend tourne.' })
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  const isAuto = selected?.mode_envoi === 'auto'

  return (
    <div>
      {/* Onglets : Modèles | Suivi */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #e2e8f0', marginBottom: 20 }}>
        {[['modeles', 'Modèles'], ['suivi', 'Suivi']].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            title={key === 'modeles' ? 'Éditer les modèles d\'email' : 'Historique des envois'}
            style={{
              padding: '8px 16px', fontSize: 13, fontWeight: tab === key ? 600 : 500,
              color: tab === key ? '#A63045' : '#64748b', background: 'none', border: 'none',
              borderBottom: tab === key ? '2px solid #A63045' : '2px solid transparent',
              marginBottom: -1, cursor: 'pointer',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'modeles' && (<>
      <p className="text-xs text-gray-400 mb-4">
        Les emails de la plateforme. Un modèle <strong>automatique</strong> part tout seul sur un
        événement ; un modèle <strong>manuel</strong> s'envoie à la demande vers une adresse que vous saisissez.
      </p>
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>

        {/* ── Colonne gauche : liste verticale des modèles ── */}
        <div style={{ width: 220, flexShrink: 0 }}>
          <div className="bg-white rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
            {templates.map(t => {
              const active = t.id === selectedId
              return (
                <button
                  key={t.id}
                  onClick={() => selectTemplate(t)}
                  title={`Éditer « ${t.nom} »`}
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
                  {t.nom}
                  <span style={{
                    display: 'block', fontSize: 10, marginTop: 2,
                    color: active ? '#A63045' : '#9ca3af',
                  }}>
                    {t.mode_envoi === 'auto' ? 'automatique' : 'manuel'}
                  </span>
                </button>
              )
            })}
          </div>
          <button
            onClick={() => { setNewName(''); setShowAdd(true) }}
            title="Créer un nouveau modèle d'email (envoi manuel)"
            style={{
              marginTop: 10, width: '100%', display: 'flex', alignItems: 'center',
              justifyContent: 'center', gap: 6, padding: '8px 12px', fontSize: 13,
              fontWeight: 500, color: '#374151', background: 'white',
              border: '1px solid #d1d5db', borderRadius: 7, cursor: 'pointer',
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Ajouter un mail
          </button>
        </div>

        {/* ── Colonne droite : éditeur du modèle sélectionné ── */}
        <div style={{ flex: 1, minWidth: 0 }}>
          {!selected ? (
            <p className="text-sm text-gray-400">Aucun modèle sélectionné.</p>
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-5">

              {/* En-tête : nom du modèle + action d'envoi en haut à droite */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#1e293b' }}>{selected.nom}</h3>
                {isAuto ? (
                  <span
                    title="Ce mail part automatiquement lors d'un événement (inscription d'un prof)"
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 11px',
                      fontSize: 12, fontWeight: 600, color: '#166534',
                      background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 99,
                    }}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Envoyé automatiquement par aSchool
                  </span>
                ) : (
                  <button
                    onClick={() => { setSendTo(''); setMessage(null); setShowSend(true) }}
                    title="Envoyer ce mail maintenant à une adresse de votre choix"
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 7,
                      background: '#1F6EEB', color: 'white', border: 'none',
                      borderRadius: 7, padding: '8px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer',
                    }}
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                    </svg>
                    Envoyer maintenant
                  </button>
                )}
              </div>

              {/* Description : à quoi sert ce mail (hors contenu envoyé) */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Description — à quoi sert ce mail</label>
                <input
                  type="text"
                  value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  placeholder="Ex. Demande d'autorisation de réutilisation adressée à l'UNICEF."
                />
                <p className="text-xs text-gray-400 mt-1">Explique le rôle de ce mail. Ce texte n'est pas envoyé.</p>
              </div>

              {/* Objet */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Objet de l'email</label>
                <input
                  type="text"
                  value={form.objet}
                  onChange={e => setForm(f => ({ ...f, objet: e.target.value }))}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  placeholder="Objet…"
                />
              </div>

              {/* Corps */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Corps du message</label>
                <textarea
                  value={form.corps}
                  onChange={e => setForm(f => ({ ...f, corps: e.target.value }))}
                  rows={12}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono"
                  placeholder="Bonjour {prenom},…"
                  style={{ resize: 'vertical', lineHeight: 1.6 }}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Variables disponibles :{' '}
                  {VARIABLES_EMAIL.map(v => (
                    <code key={v} style={{ background: '#f1f5f9', borderRadius: 4, padding: '1px 5px', marginRight: 4, fontSize: 11 }}>{v}</code>
                  ))}
                  — remplacées automatiquement à l'envoi.
                </p>
              </div>

              {/* Aperçu rendu (automatique, en bas) */}
              <div style={{ background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', padding: '12px 16px' }}>
                <p className="text-xs font-medium text-gray-500 mb-2">Aperçu rendu</p>
                <p className="text-xs text-gray-400 mb-1"><strong>Objet :</strong> {form.objet || '—'}</p>
                <pre className="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed" style={{ fontFamily: 'inherit' }}>
                  {apercuVariables(form.corps)}
                </pre>
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-3 pt-1">
                <div className="flex gap-3 flex-wrap">
                  <button
                    onClick={save}
                    disabled={saving}
                    title="Enregistrer ce modèle"
                    style={{
                      background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 7,
                      padding: '8px 20px', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: saving ? 0.6 : 1,
                    }}
                  >
                    {saving ? 'Enregistrement…' : 'Enregistrer'}
                  </button>
                  {isAuto && (
                    <button
                      onClick={sendTest}
                      disabled={busy}
                      title="Envoyer un email de test à l'adresse d'administration pour vérifier la config SMTP"
                      style={{
                        background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 7,
                        padding: '8px 20px', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: busy ? 0.6 : 1,
                      }}
                    >
                      {busy ? 'Envoi en cours…' : 'Envoyer un test'}
                    </button>
                  )}
                  {selected.supprimable && (
                    <button
                      onClick={removeTemplate}
                      disabled={busy}
                      title="Supprimer définitivement ce modèle"
                      style={{
                        marginLeft: 'auto', background: 'white', color: '#dc2626', border: '1px solid #fecaca',
                        borderRadius: 7, padding: '8px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: busy ? 0.6 : 1,
                      }}
                    >
                      Supprimer
                    </button>
                  )}
                </div>
                {message && (
                  <div style={{
                    background: message.type === 'ok' ? '#f0fdf4' : '#fef2f2',
                    border: `1px solid ${message.type === 'ok' ? '#bbf7d0' : '#fecaca'}`,
                    color:  message.type === 'ok' ? '#166534' : '#dc2626',
                    borderRadius: 8, padding: '10px 14px', fontSize: 13,
                  }}>
                    {message.text}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      </>)}

      {tab === 'suivi' && (<>
        <p className="text-xs text-gray-400 mb-4">
          Historique de tous les mails partis depuis aSchool — date d'envoi, modèle, destinataire et statut.
          Le mail de bienvenue automatique et les envois manuels y figurent.
        </p>
        <div className="bg-white rounded-lg border border-gray-200" style={{ overflow: 'hidden' }}>
          {envoisLoading ? (
            <p className="text-sm text-gray-400 p-6">Chargement…</p>
          ) : envois.length === 0 ? (
            <p className="text-sm text-gray-400 p-6">Aucun envoi pour le moment.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase tracking-wide border-b border-gray-200">
                  <th className="px-3 py-3">Date d'envoi</th>
                  <th className="px-3 py-3">Modèle</th>
                  <th className="px-3 py-3">Destinataire</th>
                  <th className="px-3 py-3">Objet</th>
                  <th className="px-3 py-3">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {envois.map(e => (
                  <tr key={e.id}>
                    <td className="px-3 py-3 text-gray-500 text-xs whitespace-nowrap">{e.envoye_le}</td>
                    <td className="px-3 py-3 text-gray-700 text-xs">{e.modele_nom}</td>
                    <td className="px-3 py-3 text-gray-700 text-xs" style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.destinataire}</td>
                    <td className="px-3 py-3 text-gray-500 text-xs" style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.objet}</td>
                    <td className="px-3 py-3">
                      <span title={e.statut === 'echec' ? (e.erreur || 'Échec') : 'Envoyé'} style={{
                        padding: '2px 8px', borderRadius: 99, fontSize: 11, fontWeight: 600,
                        background: e.statut === 'echec' ? '#fee2e2' : '#f0fdf4',
                        color: e.statut === 'echec' ? '#dc2626' : '#15803d',
                      }}>
                        {e.statut === 'echec' ? 'Échec' : 'Envoyé'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </>)}

      {/* ── Modale « Ajouter un mail » ── */}
      {showAdd && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: 12, padding: '24px', maxWidth: 420, width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
            <h3 style={{ margin: '0 0 6px', fontSize: 15, fontWeight: 600, color: '#1e293b' }}>Ajouter un mail</h3>
            <p style={{ margin: '0 0 14px', fontSize: 12, color: '#94a3b8' }}>Le nouveau modèle est de type <strong>manuel</strong> (envoi à la demande).</p>
            <input
              type="text"
              value={newName}
              autoFocus
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') addTemplate() }}
              placeholder="Nom du modèle (ex. Email UNICEF)"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              style={{ marginBottom: 16 }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setShowAdd(false)}
                title="Annuler"
                style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 7, padding: '8px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={addTemplate}
                disabled={busy || !newName.trim()}
                title="Créer le modèle"
                style={{ background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 7, padding: '8px 18px', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: (busy || !newName.trim()) ? 0.5 : 1 }}
              >
                Créer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modale « Envoyer maintenant » ── */}
      {showSend && selected && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fff', borderRadius: 12, padding: '24px', maxWidth: 440, width: '90%', boxShadow: '0 8px 32px rgba(0,0,0,0.2)' }}>
            <h3 style={{ margin: '0 0 6px', fontSize: 15, fontWeight: 600, color: '#1e293b' }}>Envoyer « {selected.nom} »</h3>
            <p style={{ margin: '0 0 14px', fontSize: 12, color: '#94a3b8' }}>Saisissez l'adresse du destinataire. L'email part depuis aSchool.</p>
            <input
              type="email"
              value={sendTo}
              autoFocus
              onChange={e => setSendTo(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') sendNow() }}
              placeholder="destinataire@exemple.org"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              style={{ marginBottom: 16 }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setShowSend(false)}
                title="Annuler"
                style={{ background: 'white', color: '#374151', border: '1px solid #d1d5db', borderRadius: 7, padding: '8px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer' }}
              >
                Annuler
              </button>
              <button
                onClick={sendNow}
                disabled={busy || !sendTo.trim()}
                title="Envoyer l'email maintenant"
                style={{ background: '#1F6EEB', color: 'white', border: 'none', borderRadius: 7, padding: '8px 18px', fontSize: 13, fontWeight: 500, cursor: 'pointer', opacity: (busy || !sendTo.trim()) ? 0.5 : 1 }}
              >
                {busy ? 'Envoi…' : 'Envoyer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
