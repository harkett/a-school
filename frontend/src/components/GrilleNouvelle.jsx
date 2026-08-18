// Écran « Nouvelle grille » — il ne fait qu'UNE chose : écrire une grille depuis une demande.
//
// C'EST UN ÉCRAN, PAS UN PANNEAU DÉPLIÉ DANS LA LISTE. Le formulaire vivait en tête de la page
// liste : il repoussait les grilles vers le bas à chaque visite, et surtout ça ne se fait nulle
// part dans la maison. « Nouvelle activité » ouvre l'écran Activité, la liste disparaît ; ici
// c'est pareil — on quitte la liste, on ne voit que la demande.
//
// UNE FOIS LA GRILLE ÉCRITE, ON REVIENT À LA LISTE, où elle apparaît. L'écran de création n'a
// plus rien à montrer : la grille se lit dans le détail de la liste, et s'édite en l'ouvrant.
//
// IL N'Y A PAS DE « GRILLE VIDE ». Un tableau nu à remplir case par case n'est pas un service :
// le professeur a déjà un tableur. Ce qu'il vient chercher, c'est que la grille soit ÉCRITE, sur
// son programme.
import { useState } from 'react'
import ApportTexte from './contenus/ApportTexte.jsx'
import FenetreIdeeGrille from './FenetreIdeeGrille.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import InfoGuide from './InfoGuide.jsx'
import { aideGrilles } from '../utils/aideGrilles.js'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../utils/api.js'
import { demanderConfirmation } from '../confirmDialog'
import { showError } from '../errorDialog.js'
import { TYPES_CONTENUS } from '../utils/typesContenus.js'
import { IconGrille } from './icones.jsx'

const TYPE_GRI = TYPES_CONTENUS.grille

// Ce que la zone propose quand elle est vide — un exemple vaut mieux qu'une consigne.
const EXEMPLE = "Un exposé oral de cinq minutes sur une œuvre étudiée en classe"

// D'où vient le texte, quand il n'a pas été tapé au clavier — la barre d'apport rend une CLÉ,
// l'écran l'affiche en clair (même principe que les écrans Ambiguïtés, Consigne et Équité).
const SOURCES_TEXTE = {
  txt:    "Demande importée d'un fichier",
  image:  "Demande extraite d'une image",
  pdf:    "Demande extraite d'un PDF",
  dictee: 'Demande issue de votre dictée',
  exemple: 'Idée proposée par aSchool, à relire et modifier',
}


export default function GrilleNouvelle({ onNavigate }) {
  const [demande, setDemande] = useState('')
  const [origineTexte, setOrigineTexte] = useState(null)
  const [generation, setGeneration] = useState(false)
  const [fenetreIdee, setFenetreIdee] = useState(false)

  // « Propose-moi une idée » — le cinquième bouton de la barre d'apport. Il n'appelle RIEN
  // lui-même : il ouvre la fenêtre où le professeur dit son thème, puisque l'appel a besoin de
  // ce thème pour rapporter autre chose qu'un passage au hasard du référentiel. `avant()` qui
  // rend `false` est ce qui arrête le bouton là (ApportTexte n'ira pas jusqu'à `action`) : sans
  // ça, sa jauge tournerait pendant que le professeur tape, pour un appel qui n'est pas parti.
  const proposerIdee = {
    label: 'Propose-moi une idée',
    // La bulle du bouton se lit dans le catalogue d'aide, comme les « i » : une explication,
    // une place.
    title: aideGrilles('idee').court,
    jauge: '',      // l'attente se voit DANS la fenêtre, jamais sous la barre d'apport
    note: 'exemple',
    avant: () => { setFenetreIdee(true); return false },
    action: async () => null,
  }

  // L'idée arrive de la fenêtre. La zone peut déjà contenir un début de demande : on ne
  // l'écrase pas sans le dire — c'est la question que la barre d'apport pose pour un fichier
  // ou une dictée, et elle vaut ici pour la même raison.
  const recevoirIdee = async texte => {
    if (demande.trim() && !await demanderConfirmation({
      titre: 'Remplacer le texte actuel ?',
      message: "Le contenu de la zone sera remplacé par l'idée proposée, et le texte actuel sera perdu.",
      confirmLabel: 'Remplacer',
    })) return
    setDemande(texte)
    setOrigineTexte('exemple')
    setFenetreIdee(false)
  }

  const generer = async () => {
    const texte = demande.trim()
    if (!texte || generation) return
    setGeneration(true)
    try {
      const res = await apiFetch('/api/contenus/grilles/generer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texte }),
      }, TIMEOUT_LONG)
      await lireReponse(res)
      // Retour à la liste : la grille y est. L'écran de création n'a plus rien à dire.
      onNavigate('eval-grilles')
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setGeneration(false)
    }
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* Barre de titre fixe — même moule que les autres écrans du monde neuf. */}
      <div style={{
        display: 'flex', alignItems: 'center', borderBottom: '2px solid #e2e8f0',
        background: '#fff', padding: '0 24px', gap: 8, flexShrink: 0,
      }}>
        <span
          title="Écrire une nouvelle grille d'évaluation à partir de votre demande"
          style={{ padding: '12px 16px', fontSize: 13, fontWeight: 600, color: 'var(--bordeaux)',
                   whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: 7 }}
        >
          <IconGrille taille={16} couleur={TYPE_GRI.accent} />
          Nouvelle grille
        </span>
      </div>

      {/* LE CORPS OCCUPE TOUT L'ESPACE — règle maison : un écran qui s'ouvre ne laisse ni bande
          vide à droite ni blanc en bas. Il portait `maxWidth: 900` (d'où la bande) et un
          `overflowY` qui empêchait la zone de saisie de s'étirer (d'où le blanc). */}
      <div style={{ flex: 1, padding: 24, display: 'flex',
                    flexDirection: 'column', gap: 12, minHeight: 0 }}>

        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1f2937',
                     display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          Ce que vous voulez évaluer
          <InfoGuide {...aideGrilles('demande')} />
        </h2>
        <p style={{ margin: 0, fontSize: 12.5, color: '#64748b', lineHeight: 1.5 }}>
          Dites ce que vos élèves vont rendre et ce que vous voulez y regarder. aSchool écrit les
          critères, l'échelle et le descripteur de chaque case, en s'appuyant sur le programme
          officiel de votre niveau.
          <InfoGuide {...aideGrilles('referentiel')} />
        </p>

        {/* La barre d'apport de la maison : clavier, fichier .txt, image, PDF, dictée. */}
        <ApportTexte
          texte={demande}
          onChange={setDemande}
          onSourceNote={setOrigineTexte}
          proposer={proposerIdee}
          disabled={generation}
        />

        {origineTexte && SOURCES_TEXTE[origineTexte] && (
          <span style={{ fontSize: 11.5, color: '#64748b', display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#6366f1', flexShrink: 0 }} />
            {SOURCES_TEXTE[origineTexte]}
          </span>
        )}

        <textarea
          value={demande}
          onChange={e => setDemande(e.target.value)}
          disabled={generation}
          placeholder={EXEMPLE}
          style={{
            flex: 1, minHeight: 120, width: '100%',
            border: '1px solid #e2e8f0', borderRadius: 6, padding: '10px 12px',
            fontFamily: 'inherit', fontSize: 13, color: '#374151', resize: 'none',
            background: generation ? '#f8fafc' : '#fff',
          }}
        />

        {/* Règle « sablier ET jauge » : l'appel IA montre la jauge, jamais un écran figé. */}
        {generation ? (
          <JaugeAttente libelle="aSchool écrit votre grille, critère par critère…" />
        ) : (
          <button
            type="button"
            className="btn-primary"
            onClick={generer}
            disabled={!demande.trim()}
            title={demande.trim()
              ? 'Écrire la grille à partir de votre demande, ancrée sur le programme officiel'
              : "Dites d'abord ce que vous voulez évaluer"}
            style={{ alignSelf: 'flex-start', cursor: demande.trim() ? 'pointer' : 'not-allowed' }}
          >
            <IconGrille taille={13} />
            Générer la grille
          </button>
        )}
      </div>

      {/* Annuler la ferme sans rien écrire : la zone n'est touchée qu'au retour d'une idée. */}
      {fenetreIdee && (
        <FenetreIdeeGrille onFermer={() => setFenetreIdee(false)} onIdee={recevoirIdee} />
      )}
    </div>
  )
}
