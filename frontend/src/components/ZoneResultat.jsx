import { useState } from 'react'
import { Document, Packer, Paragraph, TextRun } from 'docx'
import EtapeBadge from './EtapeBadge.jsx'
import InfoGuide from './InfoGuide.jsx'
import { aideActivite } from '../utils/aideActivite.js'

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
const IconPdf = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="9" y1="15" x2="15" y2="15"/>
    <line x1="9" y1="18" x2="13" y2="18"/>
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
  paragraphs.push(new Paragraph({ children: [] }))
  paragraphs.push(new Paragraph({
    children: [new TextRun({ text: 'Généré avec aSchool — aschool.fr', color: '999999', size: 16 })],
  }))
  const doc = new Document({
    sections: [{ properties: {}, children: paragraphs }],
  })
  const blob = await Packer.toBlob(doc)
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `activite_${new Date().toISOString().slice(0, 10)}.docx`
  a.click()
}

async function telechargerPdf(texte) {
  // jsPDF chargé À LA DEMANDE (import dynamique) : son poids (~700 Ko) ne pèse que sur le
  // clic PDF, pas au démarrage de l'appli. PDF texte fidèle au résultat (contenu brut, comme
  // le Word) : découpe aux marges + saut de page auto + pied « aSchool » sur chaque page,
  // comme le .txt / Word / impression. La police standard helvetica gère les accents français.
  const { jsPDF } = await import('jspdf')
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const margeX = 56, margeHaut = 56, margeBas = 48, interligne = 16
  const largeurPage = doc.internal.pageSize.getWidth()
  const hauteurPage = doc.internal.pageSize.getHeight()
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(11)
  const lignes = doc.splitTextToSize(texte, largeurPage - margeX * 2)
  let y = margeHaut
  lignes.forEach(ligne => {
    if (y + interligne > hauteurPage - margeBas) {
      doc.addPage()
      y = margeHaut
    }
    doc.text(ligne, margeX, y)
    y += interligne
  })
  const nbPages = doc.internal.getNumberOfPages()
  for (let p = 1; p <= nbPages; p++) {
    doc.setPage(p)
    doc.setFontSize(8)
    doc.setTextColor(153)
    doc.text('Généré avec aSchool — aschool.fr', largeurPage / 2, hauteurPage - 24, { align: 'center' })
  }
  doc.save(`activite_${new Date().toISOString().slice(0, 10)}.pdf`)
}

function imprimer(texte) {
  const win = window.open('', '_blank')
  const escaped = texte.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  win.document.write(`
    <html><head><title>Activité aSchool</title>
    <style>
      body{font-family:Arial,sans-serif;padding:2rem 2rem 4rem;white-space:pre-wrap;line-height:1.8;font-size:13px}
      @media print{.pied-aschool{position:fixed;bottom:0;left:0;right:0;text-align:center;font-size:10px;color:#aaa;padding:6px;border-top:1px solid #eee}}
      .pied-aschool{display:none}
    </style>
    </head><body>${escaped}<div class="pied-aschool">Généré avec aSchool — aschool.fr</div></body></html>
  `)
  win.document.close()
  win.print()
}

function envoyerMail(texte, email) {
  const sujet = encodeURIComponent(`Activité aSchool — ${new Date().toLocaleDateString('fr-FR')}`)
  const signature = '\n\n---\nGénéré avec aSchool — aschool.fr — Créez votre compte gratuit'
  const corps = encodeURIComponent(texte + signature)
  window.location.href = `mailto:${email}?subject=${sujet}&body=${corps}`
}

const IconSearch = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)

const Spinner = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: 'spin 0.7s linear infinite' }}>
    <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round"/>
  </svg>
)

export default function ZoneResultat({ resultat, loading, valide, email, onRegenerer, onChangerDemande, cahierPresent = false }) {
  const [replie, setReplie] = useState(false)   // repli manuel de la cartouche (affichage éphémère, jamais en base)
  if (!resultat && !loading) return null

  return (
    <section data-guide="resultat" className="bg-white rounded border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3 gap-3" style={{ flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', flex: 1, minWidth: 0 }}>
          <div className="section-title" style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <EtapeBadge n={4} fait={!!resultat} />
            <span style={{ display: 'inline-flex', alignItems: 'center' }}>
              Résultat généré
              <InfoGuide {...aideActivite('resultat', { cahier: cahierPresent })} />
            </span>
            {/* Chevron plier/déplier — même pattern que la carte Texte source (TexteSource.jsx). */}
            {resultat && (
              <button
                type="button"
                onClick={() => setReplie(r => !r)}
                title={replie ? "Déplier le résultat" : "Replier le résultat"}
                style={{ marginLeft: 6, width: 16, height: 16, borderRadius: '50%', border: '1px solid #cbd5e1', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ transition: 'transform 0.2s', transform: replie ? 'rotate(-90deg)' : 'none' }}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
            )}
          </div>
          {/* Message + 2 boutons de retour arrière, sur la MÊME ligne que « Résultat généré ».
              Affichés seulement quand le résultat est TERMINÉ (!loading) et pas encore validé. */}
          {resultat && !loading && !valide && onChangerDemande && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 700, color: '#334155' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                Ce résultat ne vous convient pas ? Deux solutions :
              </span>
              <button
                type="button"
                className="btn-secondary"
                onClick={onChangerDemande}
                title="Changer votre demande : déverrouille votre texte pour le modifier (réécrire, réimporter un document, redicter…), puis vous régénérez avec la nouvelle demande."
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                Changer votre demande
              </button>
            </div>
          )}
        </div>
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
            onClick={() => telechargerPdf(resultat)}
            title="Télécharger le résultat au format PDF"
          >
            <IconPdf /> PDF
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
          {/* Bouton Régénérer déplacé ici : au bout à droite, en face du titre « Résultat généré ».
              Même action et même condition qu'avant (résultat terminé, pas encore validé). */}
          {resultat && !loading && !valide && (
            <button
              type="button"
              className="btn-secondary"
              onClick={onRegenerer}
              title="Régénérer : aSchool relance une génération avec la MÊME demande et en produit une autre version, proche mais différente. Votre texte n'est pas modifié."
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.71"/></svg>
              Régénérer
            </button>
          )}
        </div>
      </div>

      {!replie && (
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
      )}
    </section>
  )
}
