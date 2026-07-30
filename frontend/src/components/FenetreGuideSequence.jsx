import FenetrePro from './FenetrePro.jsx'

// « Comment ça marche » de l'écran « Séquence » (Mes contenus). Même dispositif que les
// autres écrans : fenêtre déplaçable et étirable (coquille FenetrePro). Contenu = liste
// numérotée décrivant l'écran RÉEL (règle des deux publics : on ne décrit que ce que
// l'écran fait vraiment) — à tenir À JOUR à chaque évolution de l'écran Séquence.
const ETAPES = [
  { n: 1, titre: 'Objectif général — l\'obligatoire', sous: [
    { num: '1.1', titre: 'Objectif de la séquence', desc: "le but à atteindre au fil des séances — une séquence est une suite ordonnée de séances vers cet objectif, quelle que soit sa durée (quelques séances comme un projet sur deux ans). Cinq façons de remplir : Fichier TXT · Image/Scan · PDF · Dicter · Propose-moi un objectif (aSchool l'écrit depuis le programme officiel de votre niveau). Une pastille bleue sur la ligne du titre rappelle d'où vient le texte." },
    { num: '1.2', titre: 'Contexte rapide', desc: "optionnel : votre classe en une phrase (effectif, ambiance, ce qui marche…). La ligne du titre affiche en permanence « avec » ou « sans contexte rapide »." },
  ] },
  { n: 2, titre: 'Précisions (facultatif)', sous: [
    { num: '2.1', titre: 'Ampleur souhaitée', desc: "la taille que vous voulez donner à la séquence, en toutes lettres : « une dizaine de séances », « un trimestre », « un projet sur deux ans »… Sans ampleur, aSchool déduit le nombre de séances de l'objectif seul." },
    { num: '2.2', titre: 'Compétences / attendus', desc: "ce que les élèves doivent savoir faire à la fin de la séquence. Une compétence par ligne, avec les mêmes cinq façons de remplir — « Propose-moi des compétences » les tire du programme officiel, en lien avec votre objectif." },
  ] },
  { n: 3, titre: 'Générer le plan',
    desc: "Le bouton s'active dès que l'objectif est rempli. Le plan s'écrit EN DIRECT dans la colonne de droite : les lignes apparaissent une à une, chaque ligne = une séance. À la fin, tout s'enregistre automatiquement en une seule fois — la séquence ET ses séances (le badge « Enregistrée » l'atteste en haut de l'écran ; en cas d'échec, un bouton « Réessayer l'enregistrement » apparaît)." },
  { n: 4, titre: 'Travailler les séances — la boucle',
    desc: "Chaque ligne du plan a son bouton « Ouvrir » : l'écran Séance s'ouvre pré-rempli (le thème est déjà posé), vous générez son déroulé, vous y accrochez ses activités — puis « ← Retour à la séquence » vous ramène ici, la ligne passe de « à générer » (violet) à « générée » (vert), et vous enchaînez la suivante. Générer le plan ne génère jamais un déroulé tout seul : un clic = un étage, c'est vous qui décidez." },
  { n: 5, titre: 'La colonne de droite',
    desc: "Le plan de la séquence : une ligne par séance, numérotée dans l'ordre, avec son état (« à générer » / « générée ») et son bouton « Ouvrir ». La poignée au milieu se tire à la souris pour élargir l'une ou l'autre colonne ; le bouton « Cacher le plan », à droite de la frise, escamote cette colonne pour travailler le formulaire en pleine largeur. La frise du haut suit le chemin : Objectif → Précisions → Générer le plan, puis le compteur de séances." },
]

export default function FenetreGuideSequence({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Séquence »</strong> construit le plan d'une séquence
          pédagogique : vous donnez l'objectif, aSchool propose la liste ordonnée des séances — et
          chaque ligne du plan devient une vraie séance « à générer », enregistrée automatiquement.
        </p>

        <ol style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {ETAPES.map(e => (
            <li key={e.n} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <span style={{ flexShrink: 0, width: 20, height: 20, borderRadius: '50%', background: 'var(--bleu)',
                             color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex',
                             alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{e.n}</span>
              <span style={{ fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
                <strong style={{ color: '#1e293b' }}>{e.titre}</strong>
                {e.desc && <span style={{ display: 'block', marginTop: 3 }}>{e.desc}</span>}
                {e.sous && e.sous.map(s => (
                  <span key={s.num} style={{ display: 'block', marginTop: 4, marginLeft: 4 }}>
                    <strong style={{ color: '#1e293b' }}>{s.num} {s.titre}</strong> — {s.desc}
                  </span>
                ))}
              </span>
            </li>
          ))}
        </ol>

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
