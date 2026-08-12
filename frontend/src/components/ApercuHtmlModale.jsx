import { IconPrint } from './icones.jsx'
import { imprimerApercu } from '../utils/apercuHtml.js'

// L'aperçu MIS EN FORME, en modale : voir le rendu d'un résultat sans quitter aSchool, et
// l'imprimer tel qu'il s'affiche (pas le texte brut). Fermable au clic dehors et par la croix.
//
// Le corps reçu est du HTML SÛR — produit par utils/apercuHtml.js, qui échappe le texte et ne
// laisse passer que nos balises (h1-3, strong/em, ul/ol/li, p, hr) : `dangerouslySetInnerHTML`
// n'y voit jamais autre chose que ce que nous avons fabriqué.
export default function ApercuHtmlModale({ corps, onFermer, titreImpression = 'Imprimer cette page mise en forme' }) {
  if (corps === null || corps === undefined) return null
  return (
    <div
      onClick={onFermer}
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
            <button type="button" onClick={() => imprimerApercu(corps)} className="btn-secondary" title={titreImpression}>
              <IconPrint /> Imprimer
            </button>
            <button type="button" onClick={onFermer} title="Fermer l'aperçu" style={{ width: 28, height: 28, borderRadius: '50%', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', padding: 0, flexShrink: 0 }}>
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div className="apercu-corps" style={{ overflowY: 'auto', padding: '22px 28px', color: '#1e293b', lineHeight: 1.7, fontSize: 15 }} dangerouslySetInnerHTML={{ __html: corps }} />
      </div>
    </div>
  )
}
