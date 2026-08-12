// La ZONE DES PIÈCES JOINTES — commune à l'envoi d'un retour et à la modification d'un retour
// déjà envoyé. Elle vivait dans MesFeedbacks.jsx, d'où le formulaire d'envoi est parti : la
// laisser là-bas aurait fait dépendre le formulaire de l'écran d'historique.
import { useState, useEffect, useRef } from 'react'
import { showError } from '../errorDialog'
import { listeFormats } from '../utils/piecesJointes.js'

export function formatBytes(b) {
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(0)} Ko`
  return `${(b / 1024 / 1024).toFixed(1)} Mo`
}

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

export default function ZoneFichier({ files, onAdd, onRemove, uploading, limites }) {
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
