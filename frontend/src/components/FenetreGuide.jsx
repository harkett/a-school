import { GUIDE_CREER } from '../utils/aideCreer.js'
import FenetrePro from './FenetrePro.jsx'

// Plan du « Comment ça marche » : les mêmes numéros et titres que les cartouches 1→4 de l'écran
// avec leurs sous-options (N.M). Les libellés des sous-options sont écrits ici (aideCreer.js n'a
// pas ce niveau de détail). `cles` = phrase lue dans le catalogue (intro + Générer, pour rester
// alignés avec la visite guidée) ; `local` = courte intro d'une cartouche ; `sous` = les sous-options
// numérotées. L'écran s'arrête à ④ Résultat (les ex-cartouches 5 « Vérifier » / 6 « Améliorer » ont
// été retirées le 27-28/07 : le contrôle qualité est désormais intégré à la génération, invisible).
const CARTOUCHES = [
  { n: 1, titre: "Paramètres de l'activité", sous: [
    { num: '1.1', titre: "Type d'activité",                   desc: "ce que vous voulez créer ; la liste dépend de votre matière et de votre niveau." },
    { num: '1.2', titre: 'Précision',                         desc: "affine le type choisi, quand il le propose (inférence, lexique, mélange…)." },
    { num: '1.3', titre: 'Nombre de questions',               desc: "quand le type d'activité en demande." },
    { num: '1.4', titre: 'Proposition de correction',         desc: "cochez pour recevoir le corrigé, regroupé à la fin du document." },
  ] },
  { n: 2, titre: 'Texte source', sous: [
    { num: '2.1', titre: 'La zone de texte',                  desc: "la base de tout : votre demande ou votre document ; elle guide la génération." },
    { num: '2.2', titre: 'Six façons de la remplir',          desc: "Fichier TXT · Image/Scan · PDF · Document d'exemple · Dicter · Propose-moi une idée." },
    { num: '2.3', titre: 'Objet',                             desc: "optionnel : le nom sous lequel l'activité apparaît dans « Mes activités »." },
  ] },
  { n: 3, titre: 'Générer', cles: ['generer'], sous: [
    { num: '3.1', titre: 'Ton académique',   desc: "formel, phrases longues, style « documents officiels » ; le clic lance la génération dans ce ton." },
    { num: '3.2', titre: 'Ton opérationnel', desc: "clair, phrases courtes, consignes directes, style « prof en classe » ; le clic lance la génération dans ce ton." },
  ] },
  { n: 4, titre: 'Résultat généré', sous: [
    { num: '4.1', titre: "L'activité générée",              desc: "le texte produit, dans le ton choisi, affiché à droite." },
    { num: '4.2', titre: 'Changer votre texte / votre ton', desc: "deux boutons bleus en haut : rouvrir votre texte pour l'ajuster, ou régénérer dans l'autre ton." },
    { num: '4.3', titre: 'Export',                          desc: ".txt · Word · PDF · aperçu HTML · Imprimer · E-mail." },
  ] },
]
const phraseDe = cle => (GUIDE_CREER.find(e => e.cle === cle) || {}).phrase

// « Comment ça marche » (l'idée de l'utilisateur, 25/07) : une fenêtre déplaçable et
// étirable (coquille FenetrePro), pas un onglet qui remplace l'écran — le prof la pose où
// il veut et garde le mode d'emploi sous les yeux pendant qu'il remplit le vrai formulaire.
// Les étapes lisent le catalogue unique (utils/aideCreer.js — les mêmes phrases que les
// bulles et le centre d'aide). L'exemple ne se fabrique PLUS ici (décision du 25/07 : un
// appel IA n'a pas sa place dans un mode d'emploi, c'était trop lourd) — on renvoie au
// bouton « Document d'exemple » de la zone de texte, seul endroit qui fabrique un exemple.
export default function FenetreGuide({ onFermer, onRevoirGuide, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* Intro : le bandeau classe/matière, au-dessus des cartouches sur l'écran. */}
        {phraseDe('couple') && (
          <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>{phraseDe('couple')}</p>
        )}
        {/* Les étapes, regroupées par cartouche (mêmes numéros/titres que l'écran). Textes lus
            dans le catalogue unique aideCreer.js — les mêmes phrases que les bulles de la visite. */}
        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {CARTOUCHES.map(c => {
            const phrases = (c.cles || []).map(phraseDe).filter(Boolean)
            if (c.local) phrases.push(c.local)
            return (
              <li key={c.n} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <span style={{ flexShrink: 0, width: 20, height: 20, borderRadius: '50%', background: 'var(--bleu)',
                               color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex',
                               alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{c.n}</span>
                <span style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
                  <strong style={{ color: '#1e293b' }}>{c.titre}</strong>
                  {phrases.map((p, i) => (
                    <span key={i} style={{ display: 'block', marginTop: 3 }}>{p}</span>
                  ))}
                  {c.sous && c.sous.map(s => (
                    <span key={s.num} style={{ display: 'block', marginTop: 4, marginLeft: 4 }}>
                      <strong style={{ color: '#1e293b' }}>{s.num} {s.titre}</strong> — {s.desc}
                    </span>
                  ))}
                </span>
              </li>
            )
          })}
        </ol>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        {/* L'exemple ne se fabrique plus ici : on pointe vers le bouton qui le fait. */}
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          Pour voir un exemple adapté à votre classe, cliquez sur <strong>« Document d'exemple »</strong>, au-dessus de la zone de texte.
        </p>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={onRevoirGuide}
            title="Relancer la visite guidée : chaque élément de l'écran s'explique, à sa place"
            style={{ background: 'none', border: 'none', padding: 0, fontSize: 12, color: '#1F6EEB',
                     textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
          >
            Revoir le guide de l'écran
          </button>
          <button
            type="button"
            onClick={() => onOuvrirAide()}
            title="Ouvrir le centre d'aide (fiches complètes)"
            style={{ background: 'none', border: 'none', padding: 0, fontSize: 12, color: '#1F6EEB',
                     textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
          >
            Ouvrir le centre d'aide
          </button>
        </div>
      </div>
    </FenetrePro>
  )
}
