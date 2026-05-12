import { useState, useEffect, useRef } from 'react'
import { fetchWithTimeout } from '../utils/api.js'

const CATEGORIES = [
  { key: 'bug',        label: 'Problème' },
  { key: 'suggestion', label: 'Suggestion' },
  { key: 'question',   label: 'Question' },
]

const STATUTS = {
  nouveau:  { label: 'Nouveau',  bg: '#dbeafe', color: '#1d4ed8' },
  en_cours: { label: 'En cours', bg: '#ffedd5', color: '#c2410c' },
  traite:   { label: 'Traité',   bg: '#dcfce7', color: '#15803d' },
  archive:  { label: 'Archivé',  bg: '#f3f4f6', color: '#6b7280' },
}
const STATUTS_MODIFIABLES = ['nouveau', 'en_cours']
const ALLOWED_MIME = ['image/png', 'image/jpeg', 'application/pdf', 'text/plain']
const MAX_SIZE     = 5 * 1024 * 1024
const MAX_FILES    = 5

function formatBytes(b) {
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} Ko`
  return `${(b / 1024 / 1024).toFixed(1)} Mo`
}

// ── Pièces jointes — bouton + drag & drop ────────────────────────────────────
function ZoneFichier({ files, onAdd, onRemove, uploading, error, onError }) {
  const fileRef = useRef()
  const [drag, setDrag] = useState(false)

  function validate(file) {
    if (!ALLOWED_MIME.includes(file.type)) {
      onError(`"${file.name}" : format non accepté. Seuls PNG, JPEG, PDF et TXT sont autorisés.`)
      return false
    }
    if (file.size > MAX_SIZE) {
      onError(`"${file.name}" : fichier trop volumineux (${formatBytes(file.size)}). Limite : 5 Mo.`)
      return false
    }
    if (files.length >= MAX_FILES) {
      onError(`Maximum ${MAX_FILES} fichiers.`)
      return false
    }
    return true
  }

  function handleChange(e) {
    onError('')
    const file = e.target.files[0]
    e.target.value = ''
    if (file && validate(file)) onAdd(file)
  }

  function onDrop(e) {
    e.preventDefault(); setDrag(false); onError('')
    const file = e.dataTransfer.files[0]
    if (file && validate(file)) onAdd(file)
  }

  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.85rem', color: '#6b7280', marginBottom: 4 }}>
        Pièces jointes <span style={{ fontWeight: 400, color: '#9ca3af' }}>(optionnel — PNG, JPEG, PDF ou TXT, max 5 Mo)</span>
      </label>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: 8 }}>
        Pour joindre une capture d'écran, utilisez <kbd style={{ background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 3, padding: '1px 5px', fontFamily: 'monospace', fontSize: '0.78rem' }}>Win+Maj+S</kbd>, enregistrez l'image, puis cliquez sur Parcourir.
      </p>

      {files.length > 0 && (
        <ul style={{ listStyle: 'none', margin: '0 0 10px', padding: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {files.map((f, i) => (
            <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 6, padding: '6px 10px' }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" style={{ flexShrink: 0 }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <span style={{ fontSize: '0.82rem', color: '#374151', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
              <span style={{ fontSize: '0.72rem', color: '#9ca3af', flexShrink: 0 }}>{f.size ? formatBytes(f.size) : ''}</span>
              <button type="button" onClick={() => onRemove(i)} title="Supprimer ce fichier"
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af', padding: '0 2px', fontSize: '1rem', lineHeight: 1, flexShrink: 0 }}>×</button>
            </li>
          ))}
        </ul>
      )}

      {files.length < MAX_FILES && (
        <div
          onDragOver={e => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={onDrop}
          style={{
            border: `2px dashed ${drag ? 'var(--bleu)' : '#d1d5db'}`,
            borderRadius: 8, padding: '16px 20px', background: drag ? '#eff6ff' : '#fafafa',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
            transition: 'all 0.15s',
          }}
        >
          <span style={{ fontSize: '0.82rem', color: drag ? 'var(--bleu)' : '#6b7280' }}>
            {uploading ? 'Envoi en cours…' : 'Glissez un fichier ici'}
          </span>
          <button type="button" onClick={() => { onError(''); fileRef.current.click() }} disabled={uploading}
            title="Parcourir et sélectionner un fichier (PNG, JPEG ou PDF)"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 6, border: '1px solid #d1d5db', background: 'white', color: '#374151', cursor: uploading ? 'default' : 'pointer', fontSize: '0.82rem', flexShrink: 0 }}>
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Parcourir…
          </button>
        </div>
      )}

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, padding: '7px 12px', fontSize: '0.82rem', color: '#dc2626', marginTop: 8 }}>
          {error}
        </div>
      )}

      <input ref={fileRef} type="file" accept=".png,.jpg,.jpeg,.pdf,.txt" style={{ display: 'none' }} onChange={handleChange} />
    </div>
  )
}

// ── Page principale ────────────────────────────────────────────────────────────
export default function MesFeedbacks() {
  const [onglet, setOnglet] = useState('envoyer')
  const [retours, setRetours] = useState(null)
  const [erreurGlobal, setErreurGlobal] = useState('')
  const [succès, setSuccès] = useState('')

  // Onglet envoyer
  const [newCategory, setNewCategory] = useState('')
  const [newMessage, setNewMessage]   = useState('')
  const [newFiles, setNewFiles]       = useState([])
  const [newFileError, setNewFileError] = useState('')
  const [sending, setSending]         = useState(false)
  const [sent, setSent]               = useState(false)
  const [sendError, setSendError]     = useState('')
  const [uploading, setUploading]     = useState(false)

  // Modification
  const [editId, setEditId]       = useState(null)
  const [category, setCategory]   = useState('')
  const [message, setMessage]     = useState('')
  const [editFiles, setEditFiles] = useState([])
  const [editFileError, setEditFileError] = useState('')
  const [editUploading, setEditUploading] = useState(false)
  const [loading, setLoading]     = useState(false)

  useEffect(() => {
    fetchWithTimeout('/api/feedback/mes-feedbacks', { credentials: 'include' })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(setRetours)
      .catch(() => setErreurGlobal('Impossible de charger vos retours.'))
  }, [])

  async function uploadFile(file) {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch('/api/feedback/upload', { method: 'POST', credentials: 'include', body: form })
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}))
      throw new Error(detail?.detail || 'Erreur lors de l\'envoi.')
    }
    const { path } = await res.json()
    return { path, name: file.name, size: file.size }
  }

  async function handleAddNewFile(file) {
    setUploading(true)
    setNewFileError('')
    try {
      const uploaded = await uploadFile(file)
      setNewFiles(prev => [...prev, uploaded])
    } catch (e) {
      setNewFileError(`"${file.name}" — ${e.message}`)
    } finally {
      setUploading(false)
    }
  }

  async function handleAddEditFile(file) {
    setEditUploading(true)
    setEditFileError('')
    try {
      const uploaded = await uploadFile(file)
      setEditFiles(prev => [...prev, uploaded])
    } catch (e) {
      setEditFileError(`"${file.name}" — ${e.message}`)
    } finally {
      setEditUploading(false)
    }
  }

  function removeNewFile(i)  { setNewFiles(prev => prev.filter((_, idx) => idx !== i)) }
  function removeEditFile(i) { setEditFiles(prev => prev.filter((_, idx) => idx !== i)) }

  function handleModifier(fb) {
    setEditId(fb.id)
    setCategory(fb.category || '')
    setMessage(fb.message)
    const paths = fb.attachment_path ? fb.attachment_path.split(',').filter(Boolean) : []
    setEditFiles(paths.map(p => ({ path: p, name: p, size: 0 })))
    setSuccès('')
    setEditFileError('')
  }

  function annuler() { setEditId(null); setCategory(''); setMessage(''); setEditFiles([]); setEditFileError('') }

  async function handleEnregistrer(e) {
    e.preventDefault()
    if (!message.trim()) return
    setLoading(true)
    try {
      const paths = editFiles.map(f => f.path).join(',')
      const res = await fetchWithTimeout(`/api/feedback/${editId}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ message: message.trim(), category, attachment_path: paths || null }),
      })
      if (!res.ok) throw new Error()
      setRetours(prev => prev.map(f =>
        f.id === editId ? { ...f, message: message.trim(), category, updated_at: "aujourd'hui", attachment_path: paths || null } : f
      ))
      setSuccès('Retour modifié.')
      annuler()
    } catch { setErreurGlobal('Erreur lors de la modification.') }
    finally { setLoading(false) }
  }

  async function handleEnvoyer(e) {
    e.preventDefault()
    if (!newCategory || newMessage.trim().length < 5) return
    setSending(true); setSendError('')
    try {
      const paths = newFiles.map(f => f.path).join(',')
      const res = await fetchWithTimeout('/api/feedback', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ type: 'feedback', message: newMessage.trim(), category: newCategory, attachment_path: paths || null }),
      })
      if (!res.ok) throw new Error()
      setSent(true)
      fetchWithTimeout('/api/feedback/mes-feedbacks', { credentials: 'include' })
        .then(r => r.ok ? r.json() : Promise.reject()).then(setRetours).catch(() => {})
    } catch { setSendError('Une erreur est survenue. Réessayez.') }
    finally { setSending(false) }
  }

  function recommencer() { setSent(false); setNewCategory(''); setNewMessage(''); setNewFiles([]); setSendError(''); setNewFileError(''); setOnglet('retours') }

  const ongletStyle = active => ({
    padding: '12px 28px', fontSize: '0.95rem', fontWeight: active ? 600 : 400,
    cursor: 'pointer', border: 'none', background: 'none',
    borderBottom: active ? '3px solid var(--bleu)' : '3px solid transparent',
    color: active ? 'var(--bleu)' : '#9ca3af',
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-800">Mes feedbacks</h2>
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb', marginBottom: 24 }}>
        <button style={ongletStyle(onglet === 'envoyer')} onClick={() => { setOnglet('envoyer'); setSent(false) }}>Envoyer un retour</button>
        <button style={ongletStyle(onglet === 'retours')} onClick={() => setOnglet('retours')}>Mes retours {retours ? `(${retours.length})` : ''}</button>
      </div>

      {/* ── ONGLET ENVOYER ── */}
      {onglet === 'envoyer' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          {sent ? (
            <div className="text-center py-8">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="1.5" style={{ margin: '0 auto 12px' }}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              <p className="text-gray-700 font-semibold mb-1">Merci pour votre retour !</p>
              <p className="text-sm text-gray-400 mb-6">Votre message a bien été transmis à l'équipe aSchool.</p>
              <button onClick={recommencer} style={{ background: 'var(--bleu)', color: 'white', border: 'none', borderRadius: 6, padding: '9px 22px', fontSize: '0.88rem', cursor: 'pointer' }}>
                Voir mes retours
              </button>
            </div>
          ) : (
            <form onSubmit={handleEnvoyer} className="flex flex-col gap-5">
              <div>
                <label className="block text-sm text-gray-600 mb-2">Type <span style={{ color: '#dc2626' }}>*</span></label>
                <div className="flex gap-2 flex-wrap">
                  {CATEGORIES.map(c => (
                    <button key={c.key} type="button" onClick={() => setNewCategory(c.key)} title={`Catégorie : ${c.label}`}
                      style={{ padding: '7px 18px', borderRadius: 20, fontSize: '0.88rem', cursor: 'pointer', fontWeight: newCategory === c.key ? 600 : 400,
                        border: newCategory === c.key ? '2px solid var(--bleu)' : '1px solid #e5e7eb',
                        background: newCategory === c.key ? '#eff6ff' : 'white',
                        color: newCategory === c.key ? 'var(--bleu)' : '#6b7280' }}>
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-600 mb-1">Message <span style={{ color: '#dc2626' }}>*</span></label>
                <textarea value={newMessage} onChange={e => setNewMessage(e.target.value)}
                  placeholder="Décrivez votre retour, problème ou suggestion… (5 caractères minimum)"
                  rows={6} maxLength={2000}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 resize-none focus:outline-none focus:border-blue-400" />
                <p className="text-xs text-gray-400 text-right mt-0.5">{newMessage.length}/2000</p>
              </div>

              <ZoneFichier
                files={newFiles}
                onAdd={handleAddNewFile}
                onRemove={removeNewFile}
                uploading={uploading}
                error={newFileError}
                onError={setNewFileError}
              />

              {sendError && <p className="text-sm text-red-500">{sendError}</p>}

              <div className="flex justify-end">
                <button type="submit" className="btn-primary"
                  disabled={!newCategory || newMessage.trim().length < 5 || sending || uploading}
                  title="Envoyer votre feedback à l'équipe aSchool">
                  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                  {sending ? 'Envoi en cours…' : 'Envoyer'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* ── ONGLET MES RETOURS ── */}
      {onglet === 'retours' && (
        <div className="flex flex-col gap-3">
          {succès && <div style={{ background: '#dcfce7', border: '1px solid #bbf7d0', borderRadius: 8, padding: '10px 14px', fontSize: '0.85rem', color: '#15803d' }}>{succès}</div>}
          {erreurGlobal && <p className="text-sm text-red-500">{erreurGlobal}</p>}
          {!retours && !erreurGlobal && <p className="text-sm text-gray-400">Chargement…</p>}
          {retours && retours.length === 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Vous n'avez pas encore envoyé de retour.
              <br />
              <button onClick={() => setOnglet('envoyer')} style={{ marginTop: 12, background: 'var(--bleu)', color: 'white', border: 'none', borderRadius: 6, padding: '7px 18px', fontSize: '0.82rem', cursor: 'pointer' }}>
                Envoyer mon premier retour
              </button>
            </div>
          )}
          {retours && retours.map(fb => {
            const st = STATUTS[fb.statut] || STATUTS.nouveau
            const isEdit = editId === fb.id
            const attachPaths = fb.attachment_path ? fb.attachment_path.split(',').filter(Boolean) : []
            return (
              <div key={fb.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    {fb.category && <span style={{ fontSize: '0.72rem', background: '#eff6ff', color: '#1d4ed8', borderRadius: 4, padding: '2px 8px' }}>{fb.category}</span>}
                    <span style={{ fontSize: '0.72rem', fontWeight: 600, borderRadius: 4, padding: '2px 8px', background: st.bg, color: st.color }}>{st.label}</span>
                  </div>
                  <span style={{ fontSize: '0.72rem', color: '#9ca3af' }}>
                    {fb.updated_at ? `Modifié le ${fb.updated_at}` : fb.created_at}
                  </span>
                </div>

                {isEdit ? (
                  <form onSubmit={handleEnregistrer} className="flex flex-col gap-4">
                    <div className="flex gap-2 flex-wrap">
                      {CATEGORIES.map(c => (
                        <button key={c.key} type="button" onClick={() => setCategory(c.key)} title={`Catégorie : ${c.label}`}
                          style={{ padding: '5px 14px', borderRadius: 20, fontSize: '0.82rem', cursor: 'pointer',
                            border: category === c.key ? '2px solid var(--bleu)' : '1px solid #e5e7eb',
                            background: category === c.key ? '#eff6ff' : 'white',
                            color: category === c.key ? 'var(--bleu)' : '#6b7280' }}>
                          {c.label}
                        </button>
                      ))}
                    </div>
                    <textarea value={message} onChange={e => setMessage(e.target.value)}
                      rows={4} maxLength={2000}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 resize-none focus:outline-none focus:border-blue-400" />
                    <ZoneFichier
                      files={editFiles}
                      onAdd={handleAddEditFile}
                      onRemove={removeEditFile}
                      uploading={editUploading}
                      error={editFileError}
                      onError={setEditFileError}
                    />
                    <div className="flex justify-end gap-2">
                      <button type="button" onClick={annuler} style={{ padding: '6px 16px', fontSize: '0.85rem', borderRadius: 6, border: '1px solid #e5e7eb', background: 'white', cursor: 'pointer', color: '#6b7280' }}>Annuler</button>
                      <button type="submit" className="btn-primary" disabled={loading || !message.trim() || editUploading} title="Enregistrer les modifications">
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                        {loading ? 'Envoi…' : 'Enregistrer'}
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <p style={{ fontSize: '0.88rem', color: '#374151', lineHeight: 1.6, margin: 0 }}>{fb.message}</p>

                    {/* Pièces jointes */}
                    {attachPaths.length > 0 && (
                      <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {attachPaths.map((p, i) => (
                          <a key={i} href={`/api/feedback/attachment/${p}`} download
                            title={`Télécharger le fichier joint ${i + 1}`}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 10px', borderRadius: 5, border: '1px solid #d1d5db', background: '#f8fafc', color: '#374151', textDecoration: 'none', fontSize: '0.78rem' }}>
                            <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                              <polyline points="7 10 12 15 17 10"/>
                              <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            Fichier {attachPaths.length > 1 ? i + 1 : 'joint'}
                          </a>
                        ))}
                      </div>
                    )}

                    {STATUTS_MODIFIABLES.includes(fb.statut) && (
                      <div className="flex justify-end mt-3">
                        <button onClick={() => handleModifier(fb)} title="Modifier ce feedback"
                          style={{ padding: '5px 16px', fontSize: '0.82rem', borderRadius: 6, border: '1px solid #d1d5db', background: 'white', color: '#374151', cursor: 'pointer' }}>
                          Modifier
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
