import { useState, useEffect } from 'react'
import { Document, Packer, Paragraph, TextRun } from 'docx'
import InfoGuide from './InfoGuide.jsx'
import { aideActivite } from '../utils/aideActivite.js'
import { corpsHtml, imprimerApercu } from '../utils/apercuHtml.js'
import { IconPrint } from './icones.jsx'

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

// Aperçu HTML : formateur (corpsHtml) + impression mise en forme (imprimerApercu) sont extraits
// dans utils/apercuHtml.js et PARTAGÉS avec l'Historique (MesActivites) — un seul formateur, zéro copie.

function envoyerMail(texte, email) {
  const sujet = encodeURIComponent(`Activité aSchool — ${new Date().toLocaleDateString('fr-FR')}`)
  const signature = '\n\n---\nGénéré avec aSchool — aschool.fr — Créez votre compte gratuit'
  const corps = encodeURIComponent(texte + signature)
  window.location.href = `mailto:${email}?subject=${sujet}&body=${corps}`
}



export default function ZoneResultat({ resultat, loading, email, cahierPresent = false }) {
  const [replie, setReplie] = useState(false)   // repli manuel de la cartouche (affichage éphémère, jamais en base)
  const [apercuHtml, setApercuHtml] = useState(null)   // aperçu HTML mis en forme (modale) : chaîne = ouvert, null = fermé ; éphémère, jamais en base
  // Échap ferme l'aperçu. Hook placé AVANT le return conditionnel ci-dessous (règle des hooks React).
  useEffect(() => {
    if (apercuHtml === null) return
    const onEsc = e => { if (e.key === 'Escape') setApercuHtml(null) }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [apercuHtml])
  if (!resultat && !loading) return null

  return (
    <section data-guide="resultat" className="bg-white rounded border border-gray-200 p-4">
      {/* Barre d'en-tête (titre + exports + Régénérer) FIXE en haut : sticky dans la colonne qui
          défile (.split-col). Fond blanc + filet + marges négatives pour couvrir le padding de la
          cartouche → le texte du résultat défile DESSOUS, la barre ne suit pas l'ascenseur. */}
      <div className="flex items-center justify-between gap-3" style={{ flexWrap: 'wrap', position: 'sticky', top: 0, zIndex: 5, background: '#fff', margin: '-16px -16px 12px', padding: '16px 16px 10px', borderBottom: '1px solid #e2e8f0', borderTopLeftRadius: 6, borderTopRightRadius: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', flex: 1, minWidth: 0 }}>
          <div className="section-title" style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Le résultat n'est PAS une étape (pas de numéro) : c'est la SORTIE de l'étape ③.
                Pastille à icône « document » — verte dès qu'une activité est là, grise sinon. */}
            <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: resultat ? '#16a34a' : '#e2e8f0', color: resultat ? '#fff' : '#94a3b8' }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </span>
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
          {/* « Changer votre demande » a été déplacé (27/07) dans le bandeau titre, en haut de l'écran
              (voir App.jsx). Il n'est plus rendu ici. */}
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
            onClick={() => setApercuHtml(corpsHtml(resultat))}
            title="Voir l'activité mise en forme (aperçu, sans quitter aSchool)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> HTML
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
          {/* Barre d'export uniquement : SORTIR le résultat (télécharger / voir / imprimer / envoyer),
              tel quel. La reprise (« Changer votre texte » / « Changer votre ton ») vit dans le bandeau
              du haut. Le « Régénérer » d'origine a été retiré (ménage 28/07). */}
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
      {/* Aperçu « HTML » — MODALE fermable (clic dehors, croix, Échap), pour voir le formatage SANS
          quitter aSchool. Corps = HTML sûr (texte échappé + nos seules balises h1-3, strong/em,
          ul/ol/li, p, hr) → dangerouslySetInnerHTML sans risque. */}
      {apercuHtml !== null && (
        <div
          onClick={() => setApercuHtml(null)}
          style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(15,23,42,0.55)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 10, maxWidth: 820, width: '100%', maxHeight: '88vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
              <span style={{ fontWeight: 700, color: '#0f172a', display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                Aperçu mis en forme
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                {/* Imprimer la version MISE EN FORME (celle affichée dans la modale), pas le texte brut. */}
                <button type="button" onClick={() => imprimerApercu(apercuHtml)} className="btn-secondary" title="Imprimer cette activité mise en forme">
                  <IconPrint /> Imprimer
                </button>
                <button type="button" onClick={() => setApercuHtml(null)} title="Fermer l'aperçu" style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
            </div>
            <div className="apercu-corps" style={{ overflowY: 'auto', padding: '22px 28px', color: '#1e293b', lineHeight: 1.7, fontSize: 15 }} dangerouslySetInnerHTML={{ __html: apercuHtml }} />
            <style>{`
              .apercu-corps h1,.apercu-corps h2,.apercu-corps h3{color:#0f172a;line-height:1.3;margin:1.4em 0 .4em}
              .apercu-corps h1{font-size:1.5rem}.apercu-corps h2{font-size:1.25rem}.apercu-corps h3{font-size:1.08rem}
              .apercu-corps p{margin:.6em 0}
              .apercu-corps ul,.apercu-corps ol{margin:.6em 0 .6em 1.4em;padding:0}.apercu-corps li{margin:.3em 0}
              .apercu-corps hr{border:none;border-top:1px solid #e2e8f0;margin:1.4em 0}
              .apercu-corps strong{color:#0f172a}
            `}</style>
          </div>
        </div>
      )}
    </section>
  )
}
