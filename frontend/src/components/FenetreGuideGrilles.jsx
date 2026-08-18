import FenetrePro from './FenetrePro.jsx'
import { GUIDE_GRILLES } from '../utils/aideGrilles.js'
import Aschool from './Aschool.jsx'

// « Comment ça marche » des écrans « Mes évals → Grilles ». Même dispositif que les autres guides
// (FenetreGuideEquite, FenetreGuideConsigne…) : une fenêtre déplaçable et étirable posée À CÔTÉ de
// l'écran, pas un onglet qui cache le tableau.
//
// ELLE N'ÉCRIT AUCUN TEXTE : elle lit le catalogue de l'écran (utils/aideGrilles.js), celui-là même
// que les « i » affichent. Une explication, une place.
//
// LA MÊME FENÊTRE SERT AUX DEUX PAGES — la liste et l'éditeur. Ce sont deux vues d'un seul objet ;
// deux guides auraient obligé à écrire deux fois ce qu'est un descripteur, et les deux textes
// auraient divergé au premier ajustement.
export default function FenetreGuideGrilles({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>Une grille d'évaluation</strong> est un tableau : vos
          critères en lignes, les niveaux de maîtrise en colonnes, et dans chaque case ce que l'élève
          doit avoir fait pour obtenir ce niveau sur ce critère.
          <span style={{ display: 'block', marginTop: 6 }}>
            Vous dites en une phrase ce que vous voulez évaluer, <Aschool /> écrit la grille en
            s'appuyant sur le programme officiel de votre niveau, et vous la retouchez case par case.
          </span>
        </p>

        {/* Le cadre qui compte : ce qui sépare une grille utile d'une grille décorative. */}
        <div style={{ background: '#fffbeb', borderRadius: 6, padding: '10px 14px',
                      borderLeft: '3px solid #fcd34d' }}>
          <div style={{ fontSize: 12, color: '#78350f', lineHeight: 1.5 }}>
            <strong style={{ color: '#92400e' }}>Un descripteur se constate, il ne se juge pas</strong><br />
            « Bon travail de recherche » ne se constate pas : deux correcteurs n'y mettront pas la même
            chose, et vous ne pourrez pas le défendre devant un élève. « Cite trois sources et les met
            en relation » se constate — la case est cochée ou elle ne l'est pas. C'est la seule
            différence entre une grille et une impression générale mise en tableau, et c'est ce que
            <Aschool /> applique quand il écrit vos cases.
          </div>
        </div>

        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {GUIDE_GRILLES.map((e, i) => (
            <li key={e.cle} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <span style={{ flexShrink: 0, width: 20, height: 20, borderRadius: '50%', background: 'var(--bleu)',
                             color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex',
                             alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{i + 1}</span>
              <span style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
                <strong style={{ color: '#1e293b' }}>{e.titre}</strong>
                {/* Le texte long du catalogue — ses paragraphes sont séparés par des lignes vides,
                    rendues telles quelles (`pre-line`) plutôt que recopiées en balises ici. */}
                <span style={{ display: 'block', marginTop: 3, whiteSpace: 'pre-line' }}>{e.long}</span>
              </span>
            </li>
          ))}
        </ol>

        <div style={{ background: '#f8fafc', borderRadius: 6, padding: '10px 14px', borderLeft: '3px solid #cbd5e1' }}>
          <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.5 }}>
            <strong style={{ color: '#475569' }}>Ce que cet écran ne fait pas encore</strong><br />
            Il vous donne le MODÈLE — la grille elle-même. Remplir une grille pour un élève donné, un
            jour donné, est autre chose, et ce n'est pas encore là. De même, les grilles imposées d'un
            examen (le contrôle en cours de formation) ne se composent pas ici : elles viennent du
            diplôme, elles ne s'inventent pas.
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <button
          type="button"
          onClick={() => onOuvrirAide()}
          title="Ouvrir le centre d'aide (fiches complètes)"
          style={{ alignSelf: 'flex-start', background: 'none', border: 'none', padding: 0, fontSize: 12,
                   color: '#1F6EEB', textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit' }}
        >
          Ouvrir le centre d'aide
        </button>
      </div>
    </FenetrePro>
  )
}
