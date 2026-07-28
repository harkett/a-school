import FenetrePro from './FenetrePro.jsx'

// « Comment ça marche » de l'écran « Mes activités » (Historique). Même dispositif que celui de
// l'écran Créer (FenetreGuide) : une fenêtre déplaçable et étirable (coquille FenetrePro), que le
// prof pose où il veut pendant qu'il utilise l'écran. Contenu = liste numérotée décrivant l'écran
// réel (deux colonnes, onglets, sélection, actions de ligne, panneau de détail).
const ETAPES = [
  { n: 1, titre: 'Deux colonnes',
    desc: "À gauche la liste de vos activités, à droite le détail de celle que vous choisissez, affiché en permanence. La poignée au milieu se tire à la souris pour élargir l'une ou l'autre (double-clic = rééquilibre)." },
  { n: 2, titre: 'Deux onglets', sous: [
    { num: '2.1', titre: 'Niveau en cours',        desc: "les activités de votre matière et de votre niveau du moment." },
    { num: '2.2', titre: 'Toutes mes activités',   desc: "toutes vos activités, regroupées par matière-niveau, le couple courant épinglé en haut." },
  ] },
  { n: 3, titre: 'Choisir une activité',
    desc: "Un clic sur une ligne l'ouvre à droite (texte source + résultat généré). La plus récente est ouverte d'office, la ligne active est surlignée." },
  { n: 4, titre: 'Lire une ligne', sous: [
    { num: '4.1', titre: 'Pastille de couleur', desc: "repère le couple matière/niveau." },
    { num: '4.2', titre: 'Date',                desc: "quand l'activité a été créée (relative, avec la date exacte dessous)." },
    { num: '4.3', titre: 'Badge « Partagé »',   desc: "présent si l'activité est publiée dans Mon réseau." },
  ] },
  { n: 5, titre: "Les actions d'une ligne", sous: [
    { num: '5.1', titre: 'Partager',  desc: "publier l'activité dans « Mon réseau » pour vos collègues (à votre nom ou anonyme) ; recliquer pour la retirer." },
    { num: '5.2', titre: 'Supprimer', desc: "la corbeille supprime définitivement l'activité, après confirmation." },
  ] },
  { n: 6, titre: 'Le panneau de détail (à droite)', sous: [
    { num: '6.1', titre: 'HTML',      desc: "voir l'activité mise en forme et l'imprimer, sans quitter aSchool." },
    { num: '6.2', titre: 'Reprendre', desc: "recharger l'activité dans le formulaire pour la régénérer ou la faire évoluer." },
  ] },
  { n: 7, titre: 'Reprendre & profil',
    desc: "On ne reprend qu'une activité de votre couple courant. Pour une activité d'une autre matière ou d'un autre niveau, changez d'abord le couple dans le bandeau, en haut de l'écran." },
]

export default function FenetreGuideHistorique({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Mes activités »</strong> réunit tout ce que vous avez généré et
          enregistré : retrouvez, consultez, reprenez ou partagez vos activités.
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
