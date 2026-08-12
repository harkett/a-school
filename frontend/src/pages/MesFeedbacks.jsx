import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../utils/api.js'
import { showError } from '../errorDialog'
import { libelleEcran } from '../utils/ecrans.js'
import { couleurStatut } from '../utils/statutsFeedback.js'
import { useLimitesPiecesJointes } from '../utils/useLimitesPiecesJointes.js'
import { formatBytes, listeFormats } from '../utils/piecesJointes.js'
import FilEchange from '../components/FilEchange'

const CATEGORIES = [
  { key: 'bug',        label: 'Problème' },
  { key: 'suggestion', label: 'Suggestion' },
  { key: 'question',   label: 'Question' },
]

// ── Pièces jointes — bouton + drag & drop ────────────────────────────────────
// Les refus de pièce jointe passent par la boîte de dialogue comme tout le reste (règle
// maison) — cette zone n'a plus son propre bandeau rouge posé dans l'écran.
// Taille, nombre et formats acceptés viennent du SERVEUR (`limites`) : cet écran ne les
// connaît plus. Tant qu'ils ne sont pas arrivés, il n'accepte aucun fichier plutôt que
// d'en accepter selon une limite devinée.
// Le style des touches du clavier citées dans l'aide — écrit une fois, quatre emplois.
const kbd = {
  background: '#f3f4f6', border: '1px solid #d1d5db', borderRadius: 3,
  padding: '1px 5px', fontFamily: 'monospace', fontSize: '0.78rem',
}

function ZoneFichier({ files, onAdd, onRemove, uploading, limites }) {
  const fileRef = useRef()
  const [drag, setDrag] = useState(false)

  function validate(file) {
    if (!limites) return false
    if (!limites.mime_acceptes.includes(file.type)) {
      showError(`"${file.name}" : format non accepté.\n\nSeuls les fichiers ${listeFormats(limites, 'et')} sont acceptés.`)
      return false
    }
    if (file.size > limites.taille_max_mo * 1024 * 1024) {
      showError(`"${file.name}" : fichier trop volumineux (${formatBytes(file.size)}).\n\nLa limite est de ${limites.taille_max_mo} Mo par fichier.`)
      return false
    }
    if (files.length >= limites.nombre_max) {
      showError(`Vous ne pouvez pas joindre plus de ${limites.nombre_max} fichiers à un retour.\n\nRetirez-en un pour en ajouter un autre.`)
      return false
    }
    return true
  }

  function handleChange(e) {
    const file = e.target.files[0]
    e.target.value = ''
    if (file && validate(file)) onAdd(file)
  }

  function onDrop(e) {
    e.preventDefault(); setDrag(false)
    const file = e.dataTransfer.files[0]
    if (file && validate(file)) onAdd(file)
  }

  // LE COLLAGE — une capture d'écran ne passe plus par un fichier enregistré. Windows met
  // l'image dans le presse-papiers ; sans ceci, il fallait la rouvrir, l'enregistrer quelque
  // part, puis la retrouver avec Parcourir, pour finir par la supprimer. Trois gestes de trop
  // au moment précis où le prof veut montrer ce qu'il voit.
  //
  // L'ÉCOUTE EST POSÉE SUR LA FENÊTRE, pas sur la zone : personne ne pense à cliquer dans une
  // zone de dépôt avant de coller. Le collage marche donc partout dans le formulaire — depuis
  // le champ Message, où le clic droit propose « Coller », comme depuis la zone elle-même.
  //
  // `getAsFile()` rend un fichier nommé « image.png » pour tout le monde : deux captures
  // collées porteraient le même nom dans la liste. On le renomme avec l'heure.
  useEffect(() => {
    function onPaste(e) {
      const item = [...(e.clipboardData?.items || [])].find(i => i.type.startsWith('image/'))
      if (!item) return               // du texte collé dans le message : ce n'est pas notre affaire
      const brut = item.getAsFile()
      if (!brut) return
      e.preventDefault()
      const h = new Date()
      const deuxChiffres = n => String(n).padStart(2, '0')
      const nom = `capture-${deuxChiffres(h.getHours())}h${deuxChiffres(h.getMinutes())}-${deuxChiffres(h.getSeconds())}s.png`
      const fichier = new File([brut], nom, { type: brut.type })
      if (validate(fichier)) onAdd(fichier)
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  })

  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.85rem', color: '#6b7280', marginBottom: 4 }}>
        Pièces jointes {limites && (
          <span style={{ fontWeight: 400, color: '#9ca3af' }}>
            (optionnel — {listeFormats(limites)}, max {limites.taille_max_mo} Mo)
          </span>
        )}
      </label>
      <p style={{ fontSize: '0.78rem', color: '#9ca3af', marginBottom: 8 }}>
        Capturez une zone (<kbd style={kbd}>Impr. écran</kbd> ou <kbd style={kbd}>Win+Maj+S</kbd>),
        puis collez-la ici avec <kbd style={kbd}>Ctrl+V</kbd> ou un clic droit → Coller.
        Vous pouvez aussi glisser un fichier, ou cliquer sur Parcourir.
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

      {limites && files.length < limites.nombre_max && (
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
          <button type="button" onClick={() => fileRef.current.click()} disabled={uploading}
            title={`Parcourir et sélectionner un fichier (${listeFormats(limites)})`}
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

      {/* Le filtre du sélecteur de fichiers vient AUSSI du serveur : c'était une sixième
          copie de la liste des formats, à tenir à jour à la main comme les autres. */}
      <input ref={fileRef} type="file" accept={(limites?.mime_acceptes || []).join(',')}
        style={{ display: 'none' }} onChange={handleChange} />
    </div>
  )
}

// ── Page principale ────────────────────────────────────────────────────────────
// LES DEUX ONGLETS SONT DEVENUS DEUX ENTRÉES DE MENU. Écrire un retour et relire les siens
// étaient deux onglets à l'intérieur d'un même écran : il fallait donc ouvrir « Mes feedbacks »
// pour ensuite choisir. Ils sont maintenant côte à côte dans le menu — « Nouveau » et
// « Mes retours » — et cet écran affiche celui qu'on lui demande.
//
// UN SEUL COMPOSANT POUR LES DEUX, et pas deux fichiers : l'envoi et la liste partagent l'état
// des pièces jointes, la requête des retours et le rechargement après écriture. Les séparer
// aurait dédoublé tout cela pour ne gagner qu'une prop.
// LA FENÊTRE FLOTTANTE SERT LE MÊME FORMULAIRE. Le header et la modale d'erreur ouvraient une
// version pauvre du formulaire (components/Feedback.jsx) : ni pièce jointe, ni compteur, ni
// limites lues du serveur. Deux formulaires pour un seul geste, dont un qui ne recevait aucun
// des correctifs de l'autre. La fenêtre affiche désormais celui-ci, avec `dansFenetre`.
export default function MesFeedbacks({ vue = 'retours', onNavigate = null,
                                       contexte = null, incidentRef = null,
                                       dansFenetre = false, onClose = null }) {
  const onglet = vue
  // Passer d'une vue à l'autre, c'est maintenant NAVIGUER. Le repli sans navigation laisse
  // l'écran utilisable là où la prop n'est pas fournie, plutôt que de casser sur un clic.
  const allerAux = cible => {
    if (!onNavigate) return
    onNavigate(cible === 'envoyer' ? 'nouveau-retour' : 'mes-feedbacks')
  }
  // Taille, nombre et formats des pièces jointes : LUS EN BASE via le serveur (crochet partagé
  // avec l'Aide, qui annonce les mêmes chiffres). Cet écran ne les connaît plus.
  const { limites } = useLimitesPiecesJointes()

  const [succès, setSuccès] = useState('')

  // Onglet envoyer
  const [newCategory, setNewCategory] = useState('')
  const [newMessage, setNewMessage]   = useState('')
  const [newFiles, setNewFiles]       = useState([])

  const [sending, setSending]         = useState(false)
  const [sent, setSent]               = useState(false)

  const [uploading, setUploading]     = useState(false)

  // Modification
  const [editId, setEditId]       = useState(null)
  const [category, setCategory]   = useState('')
  const [message, setMessage]     = useState('')
  const [editFiles, setEditFiles] = useState([])

  const [editUploading, setEditUploading] = useState(false)
  const [loading, setLoading]     = useState(false)

  // Échange : la réponse en cours de frappe, par retour
  const [brouillons, setBrouillons] = useState({})
  const [envoiId, setEnvoiId]       = useState(null)

  // Read-after-write : après chaque écriture on relit le serveur, jamais de miroir local.
  // Lecture ratée : ni « Chargement… » sans fin, ni liste vide trompeuse — message en boîte de
  // dialogue et bouton « Réessayer » (motif de l'Accueil).
  const { data: retours = null, isError: chargementRate, error, refetch } = useQuery({
    queryKey: ['feedback', 'mes-feedbacks'],
    queryFn: async () => await lireReponse(
      await fetchWithTimeout('/api/feedback/mes-feedbacks', { credentials: 'include' })),
  })
  useEffect(() => { if (error) showError(messagePourEcran(error)) }, [error])
  async function recharger() { await refetch() }
  const chargerRetours = () => refetch()

  // L'envoi du fichier passe par lireReponse : le message du serveur remonte s'il est écrit
  // pour le prof, sinon c'est le message serveur générique — jamais un « Failed to fetch ».
  async function uploadFile(file) {
    const form = new FormData()
    form.append('file', file)
    const res = await fetchWithTimeout(
      '/api/feedback/upload', { method: 'POST', credentials: 'include', body: form }, TIMEOUT_LONG)
    const { path } = await lireReponse(res)
    return { path, name: file.name, size: file.size }
  }

  async function handleAddNewFile(file) {
    setUploading(true)
    try {
      const uploaded = await uploadFile(file)
      setNewFiles(prev => [...prev, uploaded])
    } catch (e) {
      showError(`« ${file.name} » n'a pas pu être joint.\n\n${messagePourEcran(e)}`)
    } finally {
      setUploading(false)
    }
  }

  async function handleAddEditFile(file) {
    setEditUploading(true)
    try {
      const uploaded = await uploadFile(file)
      setEditFiles(prev => [...prev, uploaded])
    } catch (e) {
      showError(`« ${file.name} » n'a pas pu être joint.\n\n${messagePourEcran(e)}`)
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
  }

  function annuler() { setEditId(null); setCategory(''); setMessage(''); setEditFiles([]) }

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
      await lireReponse(res)
      await recharger()
      setSuccès('Retour modifié.')
      annuler()
    } catch (e) {
      showError(messagePourEcran(e))
    } finally { setLoading(false) }
  }

  async function repondre(id) {
    const corps = (brouillons[id] || '').trim()
    if (!corps) return
    setEnvoiId(id)
    setSuccès('')
    try {
      const res = await fetchWithTimeout(`/api/feedback/${id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ corps }),
      })
      await lireReponse(res)   // le message du serveur passe tel quel, filtré du technique
      setBrouillons(b => ({ ...b, [id]: '' }))
      await recharger()
      setSuccès('Message envoyé. L\'équipe aSchool vous répondra ici même.')
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setEnvoiId(null)
    }
  }

  async function handleEnvoyer(e) {
    e.preventDefault()
    if (!newCategory || newMessage.trim().length < 5) return
    setSending(true)
    try {
      const paths = newFiles.map(f => f.path).join(',')
      const res = await fetchWithTimeout('/api/feedback', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ type: 'feedback', message: newMessage.trim(), category: newCategory, attachment_path: paths || null,
                               contexte: contexte || `Écran ${libelleEcran('mes-feedbacks')}`,
                               incident_ref: incidentRef || null }),
      })
      await lireReponse(res)
      setSent(true)
      chargerRetours()   // read-after-write : la relecture dit elle-même si elle échoue
    } catch (e) {
      showError(messagePourEcran(e))   // le retour RESTE dans le formulaire, prêt à repartir
    } finally { setSending(false) }
  }

  function recommencer() { setSent(false); setNewCategory(''); setNewMessage(''); setNewFiles([]); allerAux('retours') }

  return (
    <div style={dansFenetre ? { padding: '16px 20px', overflowY: 'auto', flex: 1, minHeight: 0 } : undefined}>
      {/* Dans la fenêtre, le titre est celui de la fenêtre : un second en dessous ferait doublon. */}
      {!dansFenetre && (
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-gray-800">
            {onglet === 'envoyer'
              ? 'Envoyer un retour'
              : `Mes retours${retours ? ` (${retours.length})` : ''}`}
          </h2>
        </div>
      )}

      {/* ── ONGLET ENVOYER ── */}
      {onglet === 'envoyer' && (
        <div className={dansFenetre ? '' : 'bg-white rounded-xl border border-gray-200 p-6'}>
          {/* D'OÙ PART LE RETOUR — affiché seulement quand l'appelant l'a fourni : ouvert depuis
              le menu, l'écran EST celui des retours et le dire n'apprendrait rien. */}
          {contexte && (
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6,
                          padding: '7px 12px', fontSize: 12, color: '#64748b', lineHeight: 1.5, marginBottom: 14 }}
                 title="Cette information part avec votre message — vous n'avez pas à décrire où vous êtes.">
              <strong style={{ color: '#475569' }}>Depuis :</strong> {contexte}
            </div>
          )}
          {incidentRef && (
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6,
                          padding: '7px 12px', fontSize: 12, color: '#b91c1c', lineHeight: 1.5, marginBottom: 14 }}
                 title="Cette référence part avec votre message — elle nous permet de retrouver l'incident technique exact.">
              <strong>Incident :</strong> {incidentRef}
            </div>
          )}
          {sent ? (
            <div className="text-center py-8">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="1.5" style={{ margin: '0 auto 12px' }}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              <p className="text-gray-700 font-semibold mb-1">Merci pour votre retour !</p>
              <p className="text-sm text-gray-400 mb-6">Votre message a bien été transmis à l'équipe aSchool.</p>
              <button onClick={dansFenetre ? onClose : recommencer}
                      title={dansFenetre ? 'Fermer la fenêtre' : 'Voir vos retours envoyés et leur statut'}
                      style={{ background: 'var(--bleu)', color: 'white', border: 'none', borderRadius: 6, padding: '9px 22px', fontSize: '0.88rem', cursor: 'pointer' }}>
                {dansFenetre ? 'Fermer' : 'Voir mes retours'}
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
                limites={limites}
              />

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
          {!retours && !chargementRate && <p className="text-sm text-gray-400">Chargement…</p>}
          {!retours && chargementRate && (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center">
              <button onClick={chargerRetours} className="btn-primary" title="Recharger vos retours">
                Réessayer
              </button>
            </div>
          )}
          {retours && retours.length === 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
              Vous n'avez pas encore envoyé de retour.
              <br />
              <button onClick={() => allerAux('envoyer')} title="Envoyer un nouveau retour (feedback)" style={{ marginTop: 12, background: 'var(--bleu)', color: 'white', border: 'none', borderRadius: 6, padding: '7px 18px', fontSize: '0.82rem', cursor: 'pointer' }}>
                Envoyer mon premier retour
              </button>
            </div>
          )}
          {retours && retours.map(fb => {
            const st = couleurStatut(fb.statut)
            const isEdit = editId === fb.id
            const attachPaths = fb.attachment_path ? fb.attachment_path.split(',').filter(Boolean) : []
            return (
              <div key={fb.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    {fb.category && <span style={{ fontSize: '0.72rem', background: '#eff6ff', color: '#1d4ed8', borderRadius: 4, padding: '2px 8px' }}>{fb.category}</span>}
                    <span style={{ fontSize: '0.72rem', fontWeight: 600, borderRadius: 4, padding: '2px 8px', background: st.bg, color: st.color }}>{fb.statut_label}</span>
                    {fb.contexte && <span title="D'où ce retour a été envoyé" style={{ fontSize: '0.72rem', background: '#f1f5f9', color: '#64748b', borderRadius: 4, padding: '2px 8px' }}>{fb.contexte}</span>}
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
                      limites={limites}
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

                    {fb.modifiable && (
                      <div className="flex justify-end mt-3">
                        <button onClick={() => handleModifier(fb)} title="Modifier ce feedback"
                          style={{ padding: '5px 16px', fontSize: '0.82rem', borderRadius: 6, border: '1px solid #d1d5db', background: 'white', color: '#374151', cursor: 'pointer' }}>
                          Modifier
                        </button>
                      </div>
                    )}

                    {/* Échange avec l'équipe aSchool : ses réponses, les vôtres, et de quoi répondre. */}
                    <FilEchange
                      messages={fb.messages}
                      valeur={brouillons[fb.id] || ''}
                      onChange={v => setBrouillons(b => ({ ...b, [fb.id]: v }))}
                      onEnvoyer={() => repondre(fb.id)}
                      envoiEnCours={envoiId === fb.id}
                      placeholder="Ajouter une précision, ou répondre à l'équipe aSchool…"
                      libelleBouton="Envoyer"
                    />
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
