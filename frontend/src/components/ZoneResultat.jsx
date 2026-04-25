import { Document, Packer, Paragraph, TextRun } from 'docx'

const IconTxt = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
)
const IconWord = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
)
const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)
const IconMail = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
    <polyline points="22,6 12,13 2,6"/>
  </svg>
)
const IconRegen = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <polyline points="1 4 1 10 7 10"/>
    <path d="M3.51 15a9 9 0 1 0 .49-3.71"/>
  </svg>
)

function telechargerTxt(texte) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([texte], { type: 'text/plain;charset=utf-8' }))
  a.download = `activite_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
}

async function telechargerWord(texte) {
  const paragraphs = texte.split('\n').map(line =>
    new Paragraph({ children: [new TextRun(line || ' ')] })
  )
  const doc = new Document({
    sections: [{ properties: {}, children: paragraphs }],
  })
  const blob = await Packer.toBlob(doc)
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `activite_${new Date().toISOString().slice(0, 10)}.docx`
  a.click()
}

function imprimer(texte) {
  const win = window.open('', '_blank')
  const escaped = texte.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  win.document.write(`
    <html><head><title>Activité A-SCHOOL</title>
    <style>body{font-family:Arial,sans-serif;padding:2rem;white-space:pre-wrap;line-height:1.8;font-size:13px}</style>
    </head><body>${escaped}</body></html>
  `)
  win.document.close()
  win.print()
}

function envoyerMail(texte, email) {
  const sujet = encodeURIComponent(`Activité A-SCHOOL — ${new Date().toLocaleDateString('fr-FR')}`)
  const corps = encodeURIComponent(texte)
  window.location.href = `mailto:${email}?subject=${sujet}&body=${corps}`
}

export default function ZoneResultat({ resultat, onRegenerer, loading, email }) {
  if (!resultat && !loading) return null

  function handleRegenerer() {
    if (window.confirm('La génération précédente sera perdue. Continuer ?')) {
      onRegenerer()
    }
  }

  return (
    <section className="bg-white rounded border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="section-title">Résultat généré</div>
        <div className="flex gap-2 flex-wrap justify-end">
          <button
            className="btn-secondary"
            onClick={() => telechargerTxt(resultat)}
            title="Télécharger le résultat en fichier texte .txt"
          >
            <IconTxt /> .txt
          </button>
          <button
            className="btn-secondary"
            onClick={() => telechargerWord(resultat)}
            title="Télécharger le résultat au format Word .docx"
          >
            <IconWord /> Word
          </button>
          <button
            className="btn-secondary"
            onClick={() => imprimer(resultat)}
            title="Imprimer le résultat"
          >
            <IconPrint /> Imprimer
          </button>
          <button
            className="btn-secondary"
            onClick={() => envoyerMail(resultat, email)}
            title="Envoyer le résultat par e-mail"
          >
            <IconMail /> E-mail
          </button>
          <button
            className="btn-primary"
            onClick={handleRegenerer}
            disabled={loading}
            title="Lancer une nouvelle génération — le résultat actuel sera perdu"
          >
            <IconRegen /> {loading ? 'Génération en cours...' : 'Régénérer'}
          </button>
        </div>
      </div>
      <div
        className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed rounded p-4"
        style={{
          background: '#f8faff',
          border: '1px solid #e2e8f0',
          borderLeftWidth: '4px',
          borderLeftColor: 'var(--bordeaux)',
        }}
      >
        {resultat}
      </div>
    </section>
  )
}
