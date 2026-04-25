const IconUpload = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
)
const IconMic = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
)

export default function TexteSource({ texte, onChange }) {
  function handleFile(e) {
    const file = e.target.files[0]
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (ext === 'txt') {
      const reader = new FileReader()
      reader.onload = ev => onChange(ev.target.result)
      reader.readAsText(file, 'utf-8')
    } else {
      onChange(`(Scan « ${file.name} » — traitement OCR via API)`)
    }
    e.target.value = ''
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      <div className="section-title mb-3">Texte source</div>
      <textarea
        className="w-full border border-gray-300 rounded p-3 text-sm resize-y"
        rows={8}
        value={texte}
        onChange={e => onChange(e.target.value)}
        placeholder={"Collez un extrait de texte ici\n— ou téléchargez un fichier .txt\n— ou importez un scan JPG/PNG\n— ou dictez avec le micro"}
      />
      <div className="mt-3 flex gap-2">
        <label
          className="btn-action"
          title="Importer un fichier .txt ou un scan JPG/PNG — le texte sera extrait automatiquement"
        >
          <IconUpload />
          Fichier .txt / scan JPG
          <input type="file" accept=".txt,.jpg,.jpeg,.png" className="hidden" onChange={handleFile} />
        </label>
        <button
          className="btn-action"
          title="Cliquez pour dicter — parlez, puis cliquez à nouveau pour arrêter"
          onClick={() => alert('Dictée vocale — disponible prochainement')}
        >
          <IconMic />
          Dicter
        </button>
      </div>
    </section>
  )
}
