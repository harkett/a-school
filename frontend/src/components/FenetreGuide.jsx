import { GUIDE_CREER } from '../utils/aideCreer.js'
import FenetrePro from './FenetrePro.jsx'

// Plan du « Comment ça marche » : les mêmes numéros et titres que les cartouches 1→6 de l'écran
// avec leurs sous-options (N.M). Les libellés des sous-options sont écrits ici (aideCreer.js n'a
// pas ce niveau de détail). `cles` = phrase lue dans le catalogue (intro + Générer, pour rester
// alignés avec la visite guidée) ; `local` = courte intro d'une cartouche ; `sous` = les sous-options
// numérotées. aideCreer.js n'est PAS modifié : la visite guidée et le centre d'aide restent intacts.
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
  { n: 3, titre: 'Générer', cles: ['generer'] },
  { n: 4, titre: 'Résultat généré', sous: [
    { num: '4.1', titre: "L'activité générée",                desc: "le texte produit, déjà enregistré tout seul dans « Mes activités »." },
    { num: '4.2', titre: 'Régénérer / Changer votre demande', desc: "une autre version, ou rouvrir votre texte pour l'ajuster." },
    { num: '4.3', titre: 'Export',                            desc: ".txt · Word · PDF · Imprimer · E-mail." },
  ] },
  { n: 5, titre: 'Vérifier le résultat',
    local: "aSchool contrôle l'activité générée sur 5 axes, en une passe, et rend une checklist. C'est un diagnostic seul : il repère, il ne réécrit rien.", sous: [
    { num: '5.1', titre: 'Cohérence interne',      desc: "l'activité correspond-elle fidèlement à votre demande (type, niveau, intention du texte source) ?" },
    { num: '5.2', titre: 'Correction ↔ questions', desc: "chaque question a-t-elle sa correction exacte, sans manque ni décalage ? (ignoré si aucun corrigé n'a été demandé)." },
    { num: '5.3', titre: 'Conformité au type',     desc: "le résultat respecte-t-il le type d'activité demandé, dans sa forme et sa nature ?" },
    { num: '5.4', titre: 'Précision',              desc: "repère les formulations floues, ambiguës ou insuffisamment cadrées." },
    { num: '5.5', titre: 'Mise en forme',          desc: "structure propre : titres, numérotation, lisibilité." },
  ] },
  { n: 6, titre: 'Améliorer  (à venir)',
    local: "la dernière étape : à partir du diagnostic, retravailler l'activité — simplifier, enrichir ou transformer — pour en produire une nouvelle version. En cours de construction." },
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
