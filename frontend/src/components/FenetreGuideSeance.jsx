import FenetrePro from './FenetrePro.jsx'

// « Comment ça marche » de l'écran « Séance » (Mes contenus). Même dispositif que celui de
// l'écran Créer (FenetreGuide) et de l'Historique (FenetreGuideHistorique) : une fenêtre
// déplaçable et étirable (coquille FenetrePro), que le prof pose où il veut pendant qu'il
// remplit le vrai formulaire. Contenu = liste numérotée décrivant l'écran RÉEL (règle des
// deux publics : on ne décrit que ce que l'écran fait vraiment) — à tenir À JOUR à chaque
// évolution de l'écran Séance (demande utilisateur du 30/07 : rempli au fur et à mesure).
const ETAPES = [
  { n: 1, titre: 'Infos de base — tout l\'obligatoire', sous: [
    { num: '1.1', titre: 'Thème / objectif',        desc: "le point de départ de la séance, c'est lui qui guide toute la génération. Cinq façons de remplir : Fichier TXT · Image/Scan · PDF · Dicter · Propose-moi un thème (aSchool l'écrit depuis le programme officiel de votre niveau). Une pastille bleue sur la ligne du titre rappelle d'où vient le texte." },
    { num: '1.2', titre: 'Contexte rapide',         desc: "optionnel : votre classe en une phrase (effectif, ambiance, ce qui a bloqué…) ; c'est lui qui donne tout son sens au mode Remédiation. La ligne du titre affiche en permanence « avec » ou « sans contexte rapide »." },
    { num: '1.3', titre: 'Mode et durée',           desc: "Séance standard · Remédiation · Approfondissement · Autonomie guidée (rien n'est pré-coché), et la durée en minutes (5 à 300) sur la même ligne. Les choix faits s'affichent en pastilles face au titre, cartouche repliée comme dépliée." },
  ] },
  { n: 2, titre: 'Contenu pédagogique (facultatif)', sous: [
    { num: '2.1', titre: 'Compétences / attendus',  desc: "ce que les élèves doivent savoir faire à la fin (le thème, lui, dit de quoi parle la séance). Une zone de texte, une compétence par ligne — même grammaire que le thème : cinq façons de remplir (TXT · Image/Scan · PDF · Dicter · Propose-moi des compétences)." },
    { num: '2.2', titre: 'Propose-moi des compétences', desc: "aSchool lit le programme officiel de votre niveau et écrit dans la zone 3 à 5 compétences EN LIEN AVEC VOTRE THÈME — vous les retouchez librement, comme n'importe quel texte. Rien n'est inventé hors programme." },
    { num: '2.3', titre: 'Matériel et contraintes', desc: "le matériel nécessaire et vos consignes spéciales (matériel imposé, élève à part, rituel de classe…) — pris en compte dans le déroulé. Chacun a son « Propose-moi… » : aSchool remplit le champ d'après votre thème et votre cadre, vous corrigez librement." },
  ] },
  { n: 3, titre: 'Déroulé souhaité (facultatif)',
    desc: "La séance générée a toujours un début, un milieu et une fin — c'est aSchool qui l'écrit. Cette cartouche sert à imposer VOTRE volonté sur ces moments, si vous en avez une. Rien n'est obligatoire : une zone vide n'est jamais une erreur, c'est « aSchool décide pour ce moment-là ».",
    sous: [
    { num: '3.1', titre: 'Esquisse A / B / C',      desc: "A, B, C = les trois moments successifs de la MÊME séance (mise en route, activité principale, retour / trace écrite) — pas trois options à départager. Remplissez zéro, une, deux ou trois zones : par exemple seulement C, « terminer par un exercice sur ardoise » — aSchool invente le reste, mais la fin sera la vôtre. « Propose-moi cette phase » écrit dans une zone à votre place, en cohérence avec les autres." },
    { num: '3.2', titre: 'Style de production (optionnel)', desc: "la FAÇON dont le document final est rédigé — même séance, même contenu, présentation différente. Classique : une fiche de préparation traditionnelle, sobre. Ludique : chaque phase passe par un jeu (défi, énigme, jeu de rôle…). Structuré : phases minutées, listes à puces, transitions explicites. Très concis : télégraphique, la séance tient sur une page. « Aucun style » (le défaut) : aSchool rédige à sa façon habituelle, et un clic dessus retire un style choisi par erreur." },
  ] },
  { n: 4, titre: 'Générer la séance',
    desc: "La cartouche ④, en bas de la colonne : son bouton s'active dès que les Infos de base sont complètes (thème + mode + durée — les cartouches 2 et 3 restent facultatives). Le déroulé s'écrit en direct dans la colonne de droite, phase par phase. Ensuite « Régénérer » relance avec vos réglages du moment." },
  { n: 5, titre: 'Activités de cette séance (cartouche ⑤, optionnel)',
    desc: "Sous « Générer », dès que la séance est enregistrée : accrochez-lui des activités. « Créer une activité ici » ouvre l'écran Activité — la nouvelle activité naît rattachée à la séance et, sitôt générée et enregistrée, l'écran REVIENT tout seul à la séance (l'activité reste à un clic : « Ouvrir ») ; « Ajouter une activité existante » va chercher une activité de vos contenus (une activité n'a qu'une séance : déjà rangée ailleurs, elle déménage après confirmation). Détacher ne supprime jamais l'activité — elle reste dans vos contenus. La frise en haut l'affiche en permanence : croix rouge « Aucune activité », ou rond vert avec le nombre." },
  { n: 6, titre: 'Enregistrement automatique',
    desc: "Aucun bouton à cliquer : la séance générée s'enregistre toute seule — le badge « Enregistrée » l'atteste en haut de l'écran. Retrouvez-la dans Mes contenus → Séances ; si l'enregistrement échoue, un bouton « Réessayer l'enregistrement » apparaît." },
  { n: 7, titre: 'La colonne de droite',
    desc: "Le déroulé généré, mis en forme à la fin du flux, avec « Imprimer ». La poignée au milieu se tire à la souris pour élargir l'une ou l'autre colonne (double-clic = rééquilibre). Le bouton « Cacher le déroulé », à droite de la frise, escamote cette colonne pour travailler le formulaire en pleine largeur — recliquez pour la réafficher. La frise du haut suit le chemin : Infos de base → Affinage → Générer, puis le compteur d'activités." },
]

export default function FenetreGuideSeance({ onFermer, onOuvrirAide }) {
  return (
    <FenetrePro titre="Comment ça marche" onFermer={onFermer}>
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 12 }}>
        <p style={{ margin: 0, fontSize: 12.5, color: '#374151', lineHeight: 1.5 }}>
          <strong style={{ color: '#1e293b' }}>« Séance »</strong> construit le déroulé complet d'une séance de
          classe en 3 cartouches : ① les infos de base (obligatoires), ② le contenu pédagogique et ③ le déroulé
          souhaité (facultatifs) — puis le bouton Générer, en bas. aSchool rédige le déroulé et l'enregistre
          automatiquement.
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
