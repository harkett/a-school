// « Comment ça marche » des démonstrations — fenêtre destinée à L'ADMIN, et à personne d'autre.
//
// Elle répond aux trois questions de celui qui arrive sur l'écran Démos : qu'est-ce qu'une
// démonstration, qu'est-ce que CET écran commande, et que voit le prof à l'autre bout. Puis elle
// donne la quatrième réponse, celle qu'on cherchait jusqu'ici dans l'historique des sessions :
// comment on en fabrique une nouvelle. En DEUX MOITIÉS, parce que le travail se fait à deux —
// ce que l'admin fait depuis cet écran (ouvrir la fiche, relire, donner le statut), puis ce que
// le dev fait en ligne de commande (la base, la copie, le contenu, la pile).
//
// POURQUOI LA PROCÉDURE EST ICI ET PAS DANS UN FICHIER À PART. Elle a d'abord été écrite en
// Markdown, dans le dépôt. Personne ne l'aurait ouverte : celui qui se demande comment fabriquer
// une démonstration est devant CET écran, pas dans un dossier du dépôt. Elle est donc au même
// endroit que le reste — et elle s'ouvre en aperçu, s'imprime, et se lit à côté du terminal.
//
// POURQUOI UNE FENÊTRE ET NON UN PANNEAU DÉPLIÉ DANS L'ÉCRAN. Une explication qui pousse le
// tableau vers le bas se lit une fois puis se referme ; une fenêtre se déplace, se garde ouverte
// pendant qu'on remplit une fiche, et s'emporte. Elle réutilise `FenetrePro`, la coquille unique
// de l'application — déplaçable par sa barre de titre, étirable par le coin.
//
// LE TEXTE N'EST ÉCRIT QU'UNE FOIS, dans `GUIDE`, `PROCEDURE` et `PIEGES`. Il sert à la fenêtre
// ET à l'aperçu mis en forme, qui est aussi la page imprimée. Un balisage minimal (**gras**,
// `code`) évite d'injecter du HTML dans le JSX pour obtenir un mot en gras.
//
// Tout ce qui y est affirmé se vérifie dans le code : les statuts qui ouvrent la porte
// (`_STATUTS_VISITABLES`, backend/prof/demo.py), la durée du jeton (`_VALIDITE`), et la copie du
// contenu à l'entrée (`_copier_le_gabarit`). Si l'un des trois change, ce texte change avec.
import { useState } from 'react'
import FenetrePro from './FenetrePro.jsx'
import { imprimerApercu } from '../utils/apercuHtml.js'

// Le globe de l'aperçu mis en forme, et l'imprimante — les mêmes que dans Mes contenus.
const IconGlobe = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  </svg>
)

const IconPrint = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 6 2 18 2 18 9"/>
    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
    <rect x="6" y="14" width="12" height="8"/>
  </svg>
)

const SOUS_TITRE = 'Une démonstration est une base à part, avec sa propre instance. '
  + 'Cet écran tient sa fiche ; il ne l’ouvre jamais.'

const GUIDE = [
  { titre: 'Ce qu’est une démonstration', items: [
    'Une base PostgreSQL **séparée**, une par référentiel, avec son propre serveur et son propre écran. La base réelle n’est jamais touchée.',
    'Elle contient un référentiel déjà découpé et vectorisé — copié tel quel depuis le réel, sans rien recalculer — et un **compte modèle**, connexion coupée, qui porte le contenu d’exemple.',
    'Elle ne se fabrique pas depuis cet écran : la base se crée et se remplit à la main, puis on vient déclarer sa fiche ici.',
  ] },
  { titre: 'Côté admin — ce que cet écran commande', items: [
    'Il tient la **fiche**, jamais les données. Il n’ouvre aucune autre base : les compteurs se saisissent, ils ne se calculent pas.',
    'Cinq statuts, du vide au livrable : À faire → En cours → Fabriquée → Testée → Validée. **Seules « Testée » et « Validée » ouvrent la porte aux profs** — ce qui n’a pas été relu n’est proposé à personne.',
    'L’**adresse** branche la fiche sur son instance. Sans elle, l’entrée du menu prof reste grisée, même en statut Validée.',
    '**Visiter** ouvre n’importe quelle démonstration avec l’identité admin, quel que soit son couple et son statut. C’est par là qu’on la relit avant de la passer en « Testée ».',
    '**Retirer** efface la fiche, pas la base : celle-ci survit et se détruit à la main.',
  ] },
  { titre: 'Côté prof — ce qu’il voit', items: [
    'Une entrée **« Démonstration »** dans son menu, active seulement s’il existe une démonstration relue **pour son niveau**.',
    'Il part avec un jeton signé, valable **cinq minutes**, qui porte son identité : il arrive connecté, sans second mot de passe à retenir.',
    'À son arrivée, le contenu du compte modèle est **recopié à son nom**. Chacun a sa copie : ce qu’il modifie ou supprime ne touche ni le modèle ni les autres visiteurs.',
    'Le filigrane **DÉMONSTRATION** marque l’écran, l’impression, le Word et le PDF — une page sortie de là ne peut pas se confondre avec une vraie.',
    'Rien de ce qu’il y fait ne remonte dans la base réelle.',
  ] },
]

// FABRIQUER, PREMIÈRE MOITIÉ : ce que l'ADMIN fait, depuis cet écran, sans terminal. C'est la
// moitié qui manquait — la procédure ne parlait que de commandes, alors que la fiche s'ouvre, se
// remplit et change de statut ici. L'admin encadre le travail du dev : il ouvre la fiche avant,
// il relit et donne le statut après.
const ADMIN_ETAPES = [
  { n: 1, titre: 'Déclarer la fiche',
    texte: 'Bouton **+ Déclarer une démonstration**. Il ne propose que les référentiels qui n’en ont pas encore — un référentiel, une démonstration, pas deux. On donne le nom de la base à venir (`<option>_demo`, minuscules et soulignés) et la fiche naît en **À faire**.' },
  { n: 2, titre: 'Suivre pendant la fabrication',
    texte: 'Passer la fiche en **En cours** quand le dev s’y met. Rien d’autre à faire : l’écran ne fabrique pas, il attend.' },
  { n: 3, titre: 'Recevoir le travail',
    texte: 'À la livraison, vérifier ce qui est renseigné : l’**adresse** de l’instance, les trois compteurs, la **date de génération**. Les compteurs se saisissent à la main — cet écran n’ouvre pas la base pour les recompter. Statut **Fabriquée**.' },
  { n: 4, titre: 'Relire soi-même, par Visiter',
    texte: 'Le bouton **Visiter** ouvre la démonstration avec l’identité admin, quel que soit son couple et son statut. Parcourir une séquence, une séance et deux activités ; vérifier le filigrane à l’écran et sur une impression. Ce qui cloche va dans **Défauts connus**, pas dans un carnet à part.' },
  { n: 5, titre: 'Ouvrir la porte aux profs',
    texte: 'Passer en **Testée** — et seulement à ce moment-là : c’est ce statut qui rend l’entrée « Démonstration » active dans le menu des profs de ce niveau. **Validée** vient ensuite, quand elle a servi sans incident. Renseigner la **date du dernier test**.' },
  { n: 6, titre: 'Corriger, ou retirer',
    texte: '**Modifier** rouvre la fiche à tout moment. **Retirer** l’efface de la liste — la base PostgreSQL, elle, survit : elle se détruit à la main, par le dev.' },
]

// FABRIQUER, SECONDE MOITIÉ : ce que fait le DEV, en ligne de commande. La recette telle qu'elle a
// été suivie pour les quatre démonstrations existantes. Elle ne coûte rien : le référentiel se
// COPIE, le contenu s'ÉCRIT. Chaque étape porte le piège qui l'a fait rater au moins une fois —
// c'est là que la procédure gagne son utilité.
//
// LE TEMPS 2 A CHANGÉ APRÈS LE BTS CRSA. Il disait « vérifier l'identifiant du niveau » ; c'était
// trop faible, et la commande donnée ne copiait même pas les précisions. Le CRSA a montré le cas
// réel : son niveau n'existe pas dans une base neuve, et son id y désigne une licence de droit.
// Le référentiel copié tel quel s'est rattaché à la mauvaise chose, sans une seule erreur.
const PREAMBULE = 'On n’écrit **que** dans la base de démonstration. Seule exception : la ligne '
  + 'de la table `demos`, au temps 6 — c’est le pilotage, il vit dans le réel. Nom de base : '
  + '`<option>_demo`, minuscules et soulignés, jamais de tiret. Et deux ports libres : 8002/5174, '
  + '8003/5175, 8004/5176 et 8005/5177 sont pris.'

const PROCEDURE = [
  { n: 1, titre: 'La base et son schéma',
    texte: 'L’extension **vector** se pose AVANT les migrations : une table de vecteurs ne se crée pas sans elle. Contrôle : même nombre de tables et même révision que la base réelle.',
    code: 'docker compose exec -T db psql -U aschool -d postgres -c "CREATE DATABASE <nom>_demo OWNER aschool;"\n'
        + 'docker compose exec -T db psql -U aschool -d <nom>_demo -c "CREATE EXTENSION IF NOT EXISTS vector;"\n'
        + 'docker compose exec -T -e DATABASE_URL=postgresql+psycopg://aschool:aschool@db:5432/<nom>_demo \\\n'
        + '  backend alembic upgrade head' },

  { n: 2, titre: 'Le niveau d’abord, le référentiel ensuite',
    texte: '**Aucun numéro de niveau ne traverse d’une base à l’autre.** Le niveau peut ne pas exister du tout dans la base neuve, et son numéro peut y désigner autre chose : les migrations sèment les niveaux, mais celui qui a été ajouté à la main dans le réel n’y est pas, et sa place est déjà prise. Le BTS CRSA en est la démonstration — `niveau_id = 89` dans le réel, « Licence Droit » dans une base neuve : copié tel quel, le référentiel arrive rattaché à une licence de droit, sans une erreur. On lit donc le niveau **par son nom des deux côtés**, on le crée s’il manque — cycle résolu par son nom lui aussi — et on rattache par une sous-requête, jamais par un chiffre recopié. C’est la règle que l’application applique déjà : le jeton du prof transporte des noms, pas des identifiants (`backend/prof/demo.py`). Si le cycle n’existait pas non plus, l’insertion casse sur la contrainte `NOT NULL` : bruyamment, et c’est ce qu’on veut. Le reste passe tel quel, vecteurs compris — on n’en recalcule aucun. Les précisions n’ont pas de `referentiel_id` : elles se prennent par jointure sur leur type, d’où leur ligne à part.',
    code: '# a) le niveau — lu PAR NOM des deux côtés, créé s’il manque. Rejouable sans risque.\n'
        + 'docker compose exec -T db psql -U aschool -d aschool_dev -tAc "\n'
        + '  select n.nom, c.nom, n.ordre from niveaux n join cycles c on c.id=n.cycle_id\n'
        + '   where n.nom=\'<NIVEAU>\';"   # relève <CYCLE_NOM> et <ORDRE>\n'
        + 'docker compose exec -T db psql -U aschool -d <nom>_demo -c "\n'
        + '  insert into niveaux (nom, cycle_id, ordre)\n'
        + '  select \'<NIVEAU>\', (select id from cycles where nom=\'<CYCLE_NOM>\'), <ORDRE>\n'
        + '   where not exists (select 1 from niveaux where nom=\'<NIVEAU>\');"\n'
        + '\n'
        + '# b) les quatre tables filtrées sur le référentiel\n'
        + 'for T in "referentiels|id=<REF>" "matieres|referentiel_id=<REF>" \\\n'
        + '         "types_activite|referentiel_id=<REF>" "referentiel_chunks|referentiel_id=<REF>"; do\n'
        + '  TABLE="${T%%|*}"; WHERE="${T##*|}"\n'
        + '  docker compose exec -T db psql -U aschool -d aschool_dev -c "\\copy (SELECT * FROM $TABLE WHERE $WHERE) TO STDOUT" > /tmp/$TABLE.tsv\n'
        + '  docker compose exec -T db psql -U aschool -d <nom>_demo -c "\\copy $TABLE FROM STDIN" < /tmp/$TABLE.tsv\n'
        + 'done\n'
        + '\n'
        + '# c) les précisions — aucun referentiel_id, jointure sur le type\n'
        + 'docker compose exec -T db psql -U aschool -d aschool_dev -c "\\copy (SELECT p.* FROM referentiel_type_precisions p\n'
        + '  JOIN types_activite t ON t.id=p.type_activite_id WHERE t.referentiel_id=<REF>) TO STDOUT" > /tmp/prec.tsv\n'
        + 'docker compose exec -T db psql -U aschool -d <nom>_demo -c "\\copy referentiel_type_precisions FROM STDIN" < /tmp/prec.tsv\n'
        + '\n'
        + '# d) LE RATTACHEMENT — par le nom. Sans cette ligne, le référentiel garde le numéro du réel.\n'
        + 'docker compose exec -T db psql -U aschool -d <nom>_demo -c "\n'
        + '  update referentiels\n'
        + '     set niveau_id=(select id from niveaux where nom=\'<NIVEAU>\')\n'
        + '   where id=<REF>;\n'
        + '  select r.id, n.nom, c.nom from referentiels r join niveaux n on n.id=r.niveau_id\n'
        + '    join cycles c on c.id=n.cycle_id;"   # doit rendre <NIVEAU>, pas autre chose' },

  { n: 3, titre: 'Recaler les compteurs d’identifiants',
    texte: 'L’étape qu’on oublie. `\\copy` écrit les identifiants tels quels **sans toucher aux séquences** : sans ce `setval`, la première insertion faite depuis l’écran tombe en doublon.',
    code: 'for T in referentiels matieres types_activite referentiel_type_precisions referentiel_chunks; do\n'
        + '  docker compose exec -T db psql -U aschool -d <nom>_demo -tAc \\\n'
        + '    "select setval(pg_get_serial_sequence(\'$T\',\'id\'), (select coalesce(max(id),1) from $T));"\n'
        + 'done' },

  { n: 4, titre: 'Le compte modèle, et la clé qui le désigne',
    texte: 'Il porte le contenu d’exemple et **ne se connecte pas** (`is_active=false`). Le mot de passe ne se choisit pas : on reprend l’empreinte d’une démonstration existante. Sans la clé `demo_gabarit_email`, le prof entre dans une démonstration vide. Le niveau se résout par son **nom**, jamais par un numéro : celui du réel ne vaut rien ici. `travail_niveau_id` et `travail_matiere_id` restent vides — le jour où le gabarit les porte, ils se résoudront par nom eux aussi.',
    code: 'HASH=$(docker compose exec -T db psql -U aschool -d ciela_demo -tAc \\\n'
        + '  "select password_hash from users where email=\'demo.btsciela@aschool.fr\';" | tr -d \'\\r\')\n'
        + 'docker compose exec -T db psql -U aschool -d <nom>_demo \\\n'
        + '  -c "insert into users (email, password_hash, is_verified, is_active, failed_attempts,\n'
        + '      guide_creer_vu, prenom, nom, subject_id, niveau_id, created_at) values\n'
        + '      (\'demo.<nom>@aschool.fr\', \'$HASH\', true, false, 0, false, \'Prof\', \'Démo\', <MATIERE>,\n'
        + '      (select id from niveaux where nom=\'<NIVEAU>\'), now());" \\\n'
        + '  -c "insert into settings (key, value) values (\'demo_gabarit_email\',\'demo.<nom>@aschool.fr\')\n'
        + '      on conflict (key) do update set value=excluded.value;"' },

  { n: 5, titre: 'Le contenu, écrit à la main',
    texte: 'Trois fichiers SQL versionnés dans `demos/<nom>_demo/`, injectés dans l’ordre : séquences, séances, activités. **Une séquence par matière, deux activités par séance au moins, et tous les types du référentiel représentés** — un type jamais employé ne se voit pas. Ce qui ne vient pas du référentiel ne se rattache à rien : libellé du type, précision, matière et niveau se reprennent mot pour mot. Le ton suit le public : épreuves et barèmes pour un BTS, ni l’un ni l’autre pour la crèche.',
    code: 'docker compose exec -T db psql -U aschool -d <nom>_demo < demos/<nom>_demo/<nom>_01_sequences.sql' },

  { n: 6, titre: 'La pile Docker, puis la fiche',
    texte: 'Copier les services `_demo_b` de `docker-compose.yml` et changer trois lignes : le nom, la base dans `DATABASE_URL`, les deux ports. `/api/demo/etat` doit rendre le bon couple, et la vérification l’**exige** au lieu de se contenter de ne pas voir d’erreur : la route rend `couple: null` plutôt qu’un mauvais couple, et un vide passerait pour un silence. S’il ne colle pas, c’est le `DATABASE_URL` qui vise la mauvaise base, ou le rattachement du temps 2 qui a manqué. Le test porte sur le nom du niveau seul : le séparateur `·` n’est pas de l’ASCII, une console qui le transcode mal ferait échouer une copie pourtant juste. La fiche se met à jour depuis cet écran : statut, adresse, compteurs, date.',
    code: 'docker compose up -d backend_demo_<x> frontend_demo_<x>\n'
        + 'curl -s http://localhost:<PORT_API>/api/demo/etat | grep -q \'<NIVEAU>\' && echo "couple correct" || echo "COPIE FAUSSE"' },

  { n: 7, titre: 'Contrôler avant de dire que c’est fait',
    texte: 'Tout doit rendre **zéro**. Puis ouvrir la démonstration par **Visiter**, parcourir une séquence, une séance et deux activités, et vérifier le filigrane — écran, impression, Word et PDF.',
    code: 'docker compose exec -T db psql -U aschool -d <nom>_demo -c "\n'
        + "select 'matiere inconnue' ctrl, count(*) from sequences s\n"
        + '  where not exists (select 1 from matieres m where m.nom=s.matiere)\n'
        + "union all select 'seance hors niveau', count(*) from seances where niveau<>'<NIVEAU>'\n"
        + "union all select 'activite sans seance', count(*) from activites a\n"
        + '  where not exists (select 1 from seances s where s.id=a.seance_id)\n'
        + "union all select 'contenu hors compte modele', count(*) from (select user_id from sequences\n"
        + '  union all select user_id from seances union all select user_id from activites) x\n'
        + "  where user_id<>(select id from users where email='demo.<nom>@aschool.fr')\n"
        + "union all select 'label qui ne colle pas au type', count(*) from activites a\n"
        + '  join types_activite t on t.id=a.activite_type_id where t.label<>a.activite_label\n'
        + "union all select 'sous_type inconnu', count(*) from activites a where a.sous_type is not null\n"
        + '  and not exists (select 1 from referentiel_type_precisions p\n'
        + '                  where p.libelle=a.sous_type and p.type_activite_id=a.activite_type_id);"' },
]

const PIEGES = [
  '**Recalculer les vecteurs.** Ils se copient. Une ré-ingestion coûte des appels et ne donne rien de plus.',
  '**Rejouer les prompts** du référentiel dans la base de démonstration : le découpage arrive avec la copie.',
  '**Écrire le contenu ailleurs que dans `demos/`.** Un dossier temporaire de session est purgé par le système, et le travail disparaît avec.',
  '**Passer une démonstration en « Testée » sans l’avoir ouverte** — ou la laisser en « Fabriquée » alors qu’elle a été relue. Le statut est une promesse faite aux profs.',
]

// **gras** → <b>, `code` → <code>. Découpage sur les paires de marqueurs : rangs impairs marqués.
function riche(texte) {
  return texte.split('**').flatMap((bout, i) => {
    if (i % 2) return [<b key={'b' + i} style={{ color: '#0f172a' }}>{bout}</b>]
    return bout.split('`').map((x, j) => (j % 2
      ? <code key={i + '-' + j} style={{ fontFamily: 'Consolas, Monaco, monospace', fontSize: '0.92em',
                                         background: '#f1f5f9', padding: '1px 4px', borderRadius: 3 }}>{x}</code>
      : <span key={i + '-' + j}>{x}</span>))
  })
}

// Le même texte pour l'aperçu mis en forme, qui est aussi la page imprimée. Les trois blocs se
// suivent au lieu de se côtoyer : à l'impression, des colonnes obligeraient à remonter en haut de
// page à chaque fois.
//
// LES CHEVRONS SONT ÉCHAPPÉS. La procédure est pleine de repères `<nom>_demo` et `<REF>` : sans
// échappement, le navigateur les prend pour des balises et les fait disparaître de la page.
function guideEnHtml() {
  const ech = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const enrichir = t => ech(t)
    .split('**').map((x, i) => (i % 2 ? '<strong>' + x + '</strong>' : x)).join('')
    .split('`').map((x, i) => (i % 2 ? '<code>' + x + '</code>' : x)).join('')
  return '<h1>Comment fonctionnent les démonstrations</h1><p>' + SOUS_TITRE + '</p>'
    + GUIDE.map(b => '<h2>' + b.titre + '</h2><ul>'
        + b.items.map(t => '<li>' + enrichir(t) + '</li>').join('') + '</ul>').join('')
    + '<h2>Fabriquer une nouvelle démonstration — par l’admin, depuis cet écran</h2>'
    + ADMIN_ETAPES.map(e => '<h3>' + e.n + '. ' + e.titre + '</h3><p>' + enrichir(e.texte) + '</p>').join('')
    + '<h2>Fabriquer une nouvelle démonstration — par le dev, en ligne de commande</h2>'
    + '<p>' + enrichir(PREAMBULE) + '</p>'
    + PROCEDURE.map(e => '<h3>' + e.n + '. ' + e.titre + '</h3><p>' + enrichir(e.texte) + '</p>'
        + '<pre>' + ech(e.code) + '</pre>').join('')
    + '<h2>Ce qu’il ne faut pas faire</h2><ul>'
    + PIEGES.map(t => '<li>' + enrichir(t) + '</li>').join('') + '</ul>'
}

// Le numéro d'une étape, dans les deux listes — celle de l'admin et celle du dev.
const pastille = {
  flexShrink: 0, width: 20, height: 20, borderRadius: '50%', background: 'var(--bleu)',
  color: '#fff', fontSize: 11, fontWeight: 700, marginTop: 1,
  display: 'flex', alignItems: 'center', justifyContent: 'center',
}

// Norme maison, valable pour les deux fenêtres : un bouton porte son icône et sa bulle d'aide, à
// hauteur fixe. Posé dans la barre de titre, donc sur le bleu : fond transparent, trait blanc.
const boutonBarre = {
  display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
  height: 26, padding: '0 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
  border: '1px solid rgba(255,255,255,0.55)', background: 'rgba(255,255,255,0.12)',
  color: '#fff', cursor: 'pointer', fontFamily: 'inherit',
}

// L'aperçu mis en forme : une fenêtre flottante de plus, posée au-dessus de la première, avec son
// bouton « Imprimer » dans sa barre de titre. Un HTML s'ouvre en fenêtre, jamais dans un onglet.
//
// `dangerouslySetInnerHTML` est sans risque ici : le HTML vient des constantes de ce fichier,
// jamais d'une saisie ni d'un fournisseur d'IA.
function ApercuHtmlGuide({ onFermer }) {
  const html = guideEnHtml()
  const actions = (
    <button type="button" style={boutonBarre} onClick={() => imprimerApercu(html)}
            title="Imprimer cette page — ou l’enregistrer en PDF depuis la boîte d’impression">
      <IconPrint />Imprimer
    </button>
  )
  return (
    <FenetrePro titre="Comment ça marche — aperçu mis en forme" onFermer={onFermer} actions={actions}
                largeur={Math.min(760, window.innerWidth - 60)} hauteur="min(80vh, 720px)" zIndex={470}>
      <div className="apercu-corps"
           style={{ overflowY: 'auto', padding: '22px 28px', color: '#1e293b', lineHeight: 1.7, fontSize: 14.5 }}
           dangerouslySetInnerHTML={{ __html: html }} />
    </FenetrePro>
  )
}

export default function GuideDemos({ onFermer }) {
  // L'aperçu HTML est une SECONDE fenêtre, par-dessus la première — jamais un onglet du
  // navigateur : dans cette application, un HTML s'ouvre en fenêtre flottante, partout.
  const [apercu, setApercu] = useState(false)

  const actions = (
    <button type="button" style={boutonBarre} onClick={() => setApercu(true)}
            title="Voir cette explication mise en forme, dans une fenêtre à part">
      <IconGlobe />Ouvrir en HTML
    </button>
  )
  const code = {
    margin: 0, padding: '8px 10px', background: '#0f172a', color: '#e2e8f0', borderRadius: 6,
    fontFamily: 'Consolas, Monaco, monospace', fontSize: 11, lineHeight: 1.55,
    overflowX: 'auto', whiteSpace: 'pre',
  }
  return (
    <>
    {apercu && <ApercuHtmlGuide onFermer={() => setApercu(false)} />}
    <FenetrePro titre="Comment fonctionnent les démonstrations" onFermer={onFermer} actions={actions}
                largeur={Math.min(880, window.innerWidth - 40)} hauteur="min(78vh, 700px)">
      <div style={{ padding: '14px 16px', overflowY: 'auto', flex: 1, minHeight: 0,
                    display: 'flex', flexDirection: 'column', gap: 14 }}>
        <p style={{ margin: 0, fontSize: 12, color: '#94a3b8', lineHeight: 1.5 }}>{SOUS_TITRE}</p>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20 }}>
          {GUIDE.map(b => (
            <div key={b.titre} style={{ flex: '1 1 240px', minWidth: 0 }}>
              <p style={{ fontSize: 12.5, fontWeight: 700, color: '#0f172a', margin: '0 0 6px' }}>{b.titre}</p>
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, lineHeight: 1.65, color: '#475569' }}>
                {b.items.map((t, i) => <li key={i} style={{ marginBottom: 4 }}>{riche(t)}</li>)}
              </ul>
            </div>
          ))}
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <div>
          <p style={{ fontSize: 12.5, fontWeight: 700, color: '#0f172a', margin: '0 0 8px' }}>
            Fabriquer une nouvelle démonstration — <span style={{ color: 'var(--bleu)' }}>par l’admin</span>, depuis cet écran
          </p>
          <ol style={{ margin: 0, padding: 0, listStyle: 'none',
                       display: 'flex', flexDirection: 'column', gap: 9 }}>
            {ADMIN_ETAPES.map(e => (
              <li key={e.n} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <span style={pastille}>{e.n}</span>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <p style={{ margin: 0, fontSize: 12.5, fontWeight: 700, color: '#1e293b' }}>{e.titre}</p>
                  <p style={{ margin: '2px 0 0', fontSize: 12, lineHeight: 1.6, color: '#475569' }}>{riche(e.texte)}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <div>
          <p style={{ fontSize: 12.5, fontWeight: 700, color: '#0f172a', margin: '0 0 4px' }}>
            Fabriquer une nouvelle démonstration — <span style={{ color: 'var(--bleu)' }}>par le dev</span>, en ligne de commande
          </p>
          <p style={{ fontSize: 12, lineHeight: 1.6, color: '#475569', margin: '0 0 10px' }}>{riche(PREAMBULE)}</p>

          <ol style={{ margin: 0, padding: 0, listStyle: 'none',
                       display: 'flex', flexDirection: 'column', gap: 12 }}>
            {PROCEDURE.map(e => (
              <li key={e.n} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <span style={pastille}>{e.n}</span>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <p style={{ margin: 0, fontSize: 12.5, fontWeight: 700, color: '#1e293b' }}>{e.titre}</p>
                  <p style={{ margin: '2px 0 6px', fontSize: 12, lineHeight: 1.6, color: '#475569' }}>{riche(e.texte)}</p>
                  <pre style={code}>{e.code}</pre>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 }} />

        <div>
          <p style={{ fontSize: 12.5, fontWeight: 700, color: '#0f172a', margin: '0 0 6px' }}>
            Ce qu’il ne faut pas faire
          </p>
          <ul style={{ margin: 0, paddingLeft: 16, fontSize: 12, lineHeight: 1.65, color: '#475569' }}>
            {PIEGES.map((t, i) => <li key={i} style={{ marginBottom: 4 }}>{riche(t)}</li>)}
          </ul>
        </div>
      </div>
    </FenetrePro>
    </>
  )
}
