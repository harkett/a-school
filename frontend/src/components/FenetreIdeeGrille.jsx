// « Propose-moi une idée » — la fenêtre où le professeur dit SUR QUOI il veut évaluer, avant
// qu'aSchool lui écrive la demande qu'il aurait tapée lui-même.
//
// POURQUOI UNE FENÊTRE, ET PAS LA ZONE PRINCIPALE. Le bouton a besoin d'un thème (« les
// réseaux », « la Révolution française ») : sans lui, les extraits remontés du référentiel sont
// pris au hasard du document entier et l'idée rendue est juste, dans le programme, et sans
// rapport avec ce que l'enseignant a en tête. Ce thème ne peut pas se taper dans la zone
// principale — c'est elle qui recevra l'idée, et ce qu'on y aurait écrit serait effacé par la
// réponse. La fenêtre lui donne sa propre place, et laisse la zone intacte tant que rien n'est
// arrivé.
//
// LE REFUS RESTE DANS LA FENÊTRE, et c'est ce qui a décidé de sa forme. Quand le référentiel n'a
// rien d'assez proche du thème, le serveur répond `available:false` avec un message : la fenêtre
// ne se ferme pas, le message s'affiche dessous, et le professeur reformule sur place. Il n'est
// jamais renvoyé devant l'écran principal sans savoir quoi faire. Ces essais ne coûtent rien —
// ils s'arrêtent après la recherche dans le référentiel, avant le modèle.
//
// ANNULER FERME SANS RIEN ÉCRIRE, y compris après plusieurs essais bloqués : renoncer doit
// rester possible à tout moment, et ne jamais laisser de trace dans la zone.
import { useState } from 'react'
import FenetrePro from './FenetrePro.jsx'
import JaugeAttente from './JaugeAttente.jsx'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_LONG } from '../utils/api.js'
import { IconIdee } from './icones.jsx'

const JAUGE = "aSchool cherche votre thème dans le programme officiel et écrit une idée…"

// Ce que la fenêtre propose quand le champ est vide — deux mots suffisent, l'exemple le montre.
const EXEMPLE = 'les réseaux'

export default function FenetreIdeeGrille({ onFermer, onIdee }) {
  const [theme, setTheme] = useState('')
  const [attente, setAttente] = useState(false)
  // Le message honnête du serveur (seuil non atteint, pas de référentiel). Effacé à chaque
  // nouvel essai : un refus qui resterait affiché sous une réussite dirait le contraire du vrai.
  const [refus, setRefus] = useState(null)

  const pret = !!theme.trim() && !attente

  async function proposer() {
    if (!pret) return
    setAttente(true)
    setRefus(null)
    try {
      const res = await apiFetch('/api/contenus/grilles/proposer-idee', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: theme.trim() }),
      }, TIMEOUT_LONG)
      const d = await lireReponse(res)
      if (d.available && d.texte) {
        // L'écran décide quoi en faire (c'est lui qui tient la zone) ; la fenêtre se retire.
        onIdee(d.texte)
        return
      }
      setRefus(d.message || "aSchool n'a pas pu proposer d'idée sur ce thème.")
    } catch (e) {
      // Panne réelle (réseau, 500, modèle surchargé) : elle se dit ICI, pas dans une boîte
      // par-dessus la fenêtre — le professeur relance sans rien perdre de ce qu'il a tapé.
      setRefus(messagePourEcran(e))
    } finally {
      setAttente(false)
    }
  }

  return (
    <FenetrePro titre="Propose-moi une idée" onFermer={onFermer} largeur={520}
                minWidth={380} zIndex={470}>
      <div style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>

        <p style={{ margin: 0, fontSize: 12.5, color: '#64748b', lineHeight: 1.5 }}>
          Sur quoi voulez-vous évaluer vos élèves ? Deux mots suffisent : aSchool cherche ce thème
          dans le programme officiel de votre niveau et écrit la demande à votre place. Vous la
          relisez et la modifiez avant de générer la grille.
        </p>

        <input
          type="text"
          value={theme}
          onChange={e => setTheme(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') proposer() }}
          disabled={attente}
          placeholder={EXEMPLE}
          autoFocus
          style={{
            width: '100%', border: '1px solid #e2e8f0', borderRadius: 6, padding: '9px 12px',
            fontFamily: 'inherit', fontSize: 13, color: '#374151',
            background: attente ? '#f8fafc' : '#fff',
          }}
        />

        {/* Le refus du serveur : ni une erreur ni une panne — une réponse honnête, dite sur le
            ton de l'information, avec la fenêtre qui reste ouverte pour reformuler. */}
        {refus && (
          <div style={{ padding: '9px 12px', background: '#fff7ed', border: '1px solid #fed7aa',
                        borderRadius: 6, fontSize: 12.5, color: '#9a3412', lineHeight: 1.5 }}>
            {refus}
          </div>
        )}

        {/* Règle « sablier ET jauge » : l'appel IA montre la jauge, jamais un écran figé. */}
        {attente ? (
          <JaugeAttente libelle={JAUGE} />
        ) : (
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onFermer}
              title="Annuler — fermer sans rien écrire dans votre demande"
              /* Padding et taille de texte repris de `.btn-primary` : deux boutons côte à côte
                 se tiennent à la MÊME hauteur, c'est la norme maison. */
              style={{
                padding: '0.45rem 1.1rem', fontSize: '0.875rem', fontWeight: 500,
                borderRadius: 6, border: '1px solid #d1d5db', background: '#fff',
                color: '#374151', cursor: 'pointer', fontFamily: 'inherit',
                display: 'inline-flex', alignItems: 'center', gap: 6,
              }}
            >
              Annuler
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={proposer}
              disabled={!pret}
              title={pret
                ? "Écrire une idée de production à évaluer sur ce thème, tirée du programme officiel"
                : "Dites d'abord sur quoi porte l'évaluation"}
              style={{ cursor: pret ? 'pointer' : 'not-allowed' }}
            >
              <IconIdee />
              Propose-moi une idée
            </button>
          </div>
        )}
      </div>
    </FenetrePro>
  )
}
