import FenetrePro from './FenetrePro.jsx'

// LE DÉTAIL D'UN APPEL À L'IA — LE CHEMIN QU'IL A PRIS, DESSINÉ.
//
// POURQUOI UN SCHÉMA ET PAS UNE LISTE. Quinze champs alignés en clé-valeur, personne ne les lit :
// il faut les traduire de tête pour comprendre l'histoire, et l'histoire est simple — on a demandé
// au premier fournisseur, il a dit non, on est passé au suivant, qui a répondu et facturé. Cette
// suite-là se DESSINE : un bloc par fournisseur essayé, une flèche entre eux, l'état et les
// chiffres dans le bloc. On comprend avant d'avoir lu.
//
// LA CASCADE SE RECONSTITUE À L'ÉCRAN, sans rien demander de plus au serveur : les tentatives d'un
// même appel sont des lignes voisines du journal — même outil, à quelques secondes, avec un rang
// qui monte. On les regroupe ici. Une tentative qui manquerait (page tournée au mauvais endroit)
// ne casse rien : le schéma montre ce qu'il a.
//
// LE TEXTE ENVOYÉ ET LA RÉPONSE N'Y SONT PAS, et n'y seront pas : la table compte les appels, elle
// ne conserve pas leur contenu. La fenêtre le dit, sinon on la croit incomplète.

// Les tentatives d'un même appel se suivent de près : une minute suffit largement, et évite de
// ramasser l'appel suivant du même outil lancé cinq minutes plus tard.
const PROCHE_MS = 60000

export default function DetailAppelIA({ ligne, lignes, onFermer, outils }) {
  const { quandLong, duree, nb, usd, arret } = outils

  const t0 = new Date(ligne.quand).getTime()
  const tentatives = (lignes || [])
    .filter(l => l.outil === ligne.outil
              && Math.abs(new Date(l.quand).getTime() - t0) <= PROCHE_MS)
    .sort((a, b) => (a.rang || 1) - (b.rang || 1) || new Date(a.quand) - new Date(b.quand))

  const chemin  = tentatives.length > 0 ? tentatives : [ligne]
  const abouti  = chemin.find(l => l.resultat !== 'refus')
  const refuses = chemin.filter(l => l.resultat === 'refus')

  // Ce que cet appel a coute EN TOUT : un refus ne facture rien, mais deux fournisseurs qui
  // repondent facturent deux fois. On additionne le chemin entier, pas la derniere etape.
  const total = chemin.reduce((s, l) => s + (l.cout_usd || 0), 0)

  // Pas de hauteur imposée : un appel qui a réussi du premier coup tient en un bloc, une
  // cascade de trois en tient trois. La fenêtre suit.
  return (
    <FenetrePro titre="Le chemin de cet appel" onFermer={onFermer} largeur={480}>
      <div style={{ overflowY: 'auto', padding: '14px 18px 18px' }}>

        {/* D'où part l'appel : la fonction du logiciel qui l'a demandé, et quand. */}
        <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{ligne.origine}</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12,
                      marginTop: 2, marginBottom: 12 }}>
          <span style={{ fontSize: 11.5, color: '#94a3b8' }}>{quandLong(ligne.quand)}</span>
          {/* LE TOTAL, en face de l'heure : la question qu'on se pose en ouvrant la fenetre a
              sa reponse avant meme d'avoir lu. C'est bien la somme de TOUTES les tentatives —
              deux fournisseurs sollicites, deux montants ; le detail par etape reste plus bas. */}
          <span style={{ marginLeft: 'auto', fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap',
                         color: total ? '#A63045' : '#166534' }}>
            Total : {usd(total)}
          </span>
        </div>

        {/* ── CE QUE ÇA VEUT DIRE, EN PREMIER. On vient ici pour savoir ce qui s'est passé ; le
            schéma qui suit montre COMMENT. La conclusion placée sous le dessin obligeait à
            déchiffrer trois blocs avant de lire la phrase qu'on était venu chercher. ── */}
        <div style={{
          marginBottom: 14, padding: '10px 12px', borderRadius: 8,
          background: refuses.length > 0 ? '#fffbeb' : '#f0fdf4',
          border: '1px solid ' + (refuses.length > 0 ? '#fde68a' : '#bbf7d0'),
          fontSize: 12, lineHeight: 1.55, color: '#374151',
        }}>
          {!abouti && (
            <>Tous les fournisseurs ont refusé : le professeur a vu un message d’erreur, et rien
              n’a été facturé.</>
          )}
          {abouti && refuses.length === 0 && (
            <>Le premier fournisseur a répondu.{' '}
              {abouti.cout_usd ? <>Cet appel a coûté <strong>{usd(abouti.cout_usd)}</strong>.</>
                               : <>Cet appel n’a rien coûté.</>}</>
          )}
          {abouti && refuses.length > 0 && (
            <>{refuses.length === 1
                ? 'Le premier fournisseur a refusé'
                : `Les ${refuses.length} premiers fournisseurs ont refusé`}, l’appel est parti chez{' '}
              <strong>{abouti.fournisseur}</strong> et a coûté <strong>{usd(abouti.cout_usd)}</strong>.
              {' '}Tant que le gratuit refuse, chaque appel est payé.</>
          )}
        </div>

        {/* ── LE SCHÉMA — un bloc par fournisseur essayé, dans l'ordre où ils l'ont été. ── */}
        {chemin.map((l, i) => (
          <div key={l.id}>
            <Etape ligne={l} rang={l.rang || i + 1} outils={outils} />
            {i < chemin.length - 1 && <Fleche />}
          </div>
        ))}

        <p style={{ margin: '12px 0 0', fontSize: 11, lineHeight: 1.5, color: '#94a3b8' }}>
          Le texte envoyé et la réponse reçue ne sont pas conservés : le journal compte les appels,
          il ne relit pas leur contenu.
        </p>
      </div>
    </FenetrePro>
  )
}


// UN BLOC DU SCHÉMA — un fournisseur essayé, ce qu'il a répondu, ce qu'il a coûté.
//
// La couleur porte l'information : rouge il a dit non, vert il a écrit. Le numéro à gauche dit à
// quel tour on en était — c'est lui qui explique un appel payant alors que le premier de la liste
// est gratuit.
function Etape({ ligne, rang, outils }) {
  const { duree, nb, usd, arret } = outils
  const refus = ligne.resultat === 'refus'
  const a = arret(ligne.motif_arret, ligne.resultat, ligne.code_http)

  return (
    <div style={{
      display: 'flex', gap: 10,
      border: '1px solid ' + (refus ? '#fecaca' : '#bbf7d0'),
      background: refus ? '#fef2f2' : '#f0fdf4',
      borderRadius: 9, padding: '10px 12px',
    }}>
      <div style={{
        width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
        background: refus ? '#fecaca' : '#bbf7d0', color: refus ? '#991b1b' : '#166534',
        fontSize: 11, fontWeight: 800,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {rang}
      </div>

      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>{ligne.fournisseur}</span>
          <span style={{ fontSize: 11.5, color: '#64748b' }}>{ligne.modele}</span>
          <span style={{
            marginLeft: 'auto', fontSize: 10.5, fontWeight: 700, padding: '1px 8px', borderRadius: 99,
            background: refus ? '#fee2e2' : '#dcfce7', color: refus ? '#991b1b' : '#166534',
            whiteSpace: 'nowrap',
          }}>
            {refus ? 'a refusé' : a.coupe ? 'réponse coupée' : 'a répondu'}
          </span>
        </div>

        {/* La raison, en français. Le code du fournisseur est dans la phrase, pas en vedette. */}
        <div style={{ fontSize: 11.5, color: refus ? '#b91c1c' : '#475569', marginTop: 3, lineHeight: 1.45 }}>
          {a.brut}
        </div>

        {/* Les chiffres, seulement pour la tentative qui a produit quelque chose : un refus n'a ni
            jetons ni prix, les afficher à zéro laisserait croire à un appel gratuit réussi. */}
        {!refus && (
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginTop: 6,
                        fontSize: 11.5, color: '#475569' }}>
            <span><strong>{nb(ligne.tokens_entree)}</strong> envoyés</span>
            <span><strong>{nb(ligne.tokens_sortie)}</strong> produits</span>
            <span>{duree(ligne.duree_ms)}</span>
            <span style={{ fontWeight: 700, color: ligne.cout_usd ? '#A63045' : '#166534' }}>
              {ligne.depuis_cache ? 'rejeu du cache' : usd(ligne.cout_usd)}
            </span>
          </div>
        )}

        {ligne.tokens_cache_lecture > 0 && (
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 3 }}>
            dont {nb(ligne.tokens_cache_lecture)} jetons relus dans le cache du fournisseur — facturés 10 %
          </div>
        )}
      </div>
    </div>
  )
}


// La flèche entre deux tentatives : c'est elle qui fait lire le schéma dans le bon sens.
function Fleche() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '5px 0 5px 11px' }}>
      <svg width="16" height="20" viewBox="0 0 16 20" fill="none" stroke="#cbd5e1" strokeWidth="1.6"
           strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 2v13" />
        <polyline points="4 11 8 15 12 11" />
      </svg>
      <span style={{ fontSize: 11, color: '#94a3b8' }}>on passe au suivant</span>
    </div>
  )
}
