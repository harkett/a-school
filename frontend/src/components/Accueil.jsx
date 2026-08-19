import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import InfoGuide from './InfoGuide.jsx'
import Nouveautes from './Nouveautes.jsx'
import { astucesEcran } from '../utils/astuces.js'
import { TYPES_CONTENUS } from '../utils/typesContenus.js'
import { IconSequence, IconSeance, IconActivite, IconAmbiguites, IconConsigne, IconEquite } from './icones.jsx'
import { TYPES_ANALYSES } from '../utils/typesAnalyses.js'

function getPhrase(count) {
  if (count === 0) return 'Votre premier cours personnalisé est à portée de clic.'
  if (count < 3)  return 'Bon début ! Continuez à créer — aSchool apprend à vous connaître.'
  if (count < 10) return `${count} activités créées. aSchool commence à reconnaître votre style.`
  if (count < 30) return `${count} activités créées. aSchool reconnaît maintenant votre façon d'enseigner.`
  return `${count} activités créées — vous faites partie des profs les plus actifs de la plateforme.`
}

// Les astuces de l'écran, lues une fois : le « a » ne bouge pas d'un rendu à l'autre.
const astucesAccueil = astucesEcran('accueil')

// Les trois analyses — l'Accueil est leur SECONDE porte : les phrases disent la même chose que
// les bulles du menu, sous peine d'annoncer ici autre chose que là.
const ANALYSES = [
  { page: 'ambiguites', label: 'Ambiguïtés', Icon: IconAmbiguites, ...TYPES_ANALYSES.ambiguites,
    total: 'mes_ambiguites', nom: 'analyse d’ambiguïtés', pluriel: 'analyses d’ambiguïtés',
    phrase: "Détecter les ambiguïtés cognitives d'un énoncé ou d'un exercice" },
  { page: 'consigne', label: 'Consignes', Icon: IconConsigne, ...TYPES_ANALYSES.consigne,
    total: 'mes_consignes', nom: 'analyse de consigne', pluriel: 'analyses de consignes',
    phrase: "Analyser la qualité didactique d'une consigne" },
  { page: 'equite', label: 'Équité', Icon: IconEquite, ...TYPES_ANALYSES.equite,
    total: 'mes_equites', nom: 'analyse d’équité', pluriel: 'analyses d’équité',
    phrase: "Repérer ce qui pénalise certains élèves pour une raison étrangère à ce qui est évalué" },
]

const TYPES = [
  { type: 'sequence', champ: 'derniere_sequence', total: 'mes_sequences', nom: 'séquence', Icon: IconSequence, label: 'Séquence', page: 'contenus-sequences',
    ...TYPES_CONTENUS.sequence, vide: "Aucune séquence pour l'instant.",
    titreOuvrir: 'Rouvrir cette séquence dans Mes contenus', titreListe: 'Voir toutes mes séquences dans Mes contenus', lienListe: 'Voir toutes mes séquences' },
  { type: 'seance', champ: 'derniere_seance', total: 'mes_seances', nom: 'séance', Icon: IconSeance, label: 'Séance', page: 'contenus-seances',
    ...TYPES_CONTENUS.seance, vide: "Aucune séance pour l'instant.",
    titreOuvrir: 'Rouvrir cette séance dans Mes contenus', titreListe: 'Voir toutes mes séances dans Mes contenus', lienListe: 'Voir toutes mes séances' },
  { type: 'activite', champ: 'derniere_activite', total: 'mes_activites', nom: 'activité', Icon: IconActivite, label: 'Activité', page: 'contenus-activites',
    ...TYPES_CONTENUS.activite, vide: "Aucune activité pour l'instant.",
    titreOuvrir: 'Rouvrir cette activité dans Mes contenus', titreListe: 'Voir toutes mes activités dans Mes contenus', lienListe: 'Voir toutes mes activités' },
]

const EMPTY_MSG = { fontSize: 12, color: '#cbd5e1', fontStyle: 'italic' }

function Total({ n, bloc }) {
  if (!n) return null
  const mot = n > 1 ? (bloc.pluriel || `${bloc.nom}s`) : bloc.nom
  return (
    <span style={{ marginLeft: 'auto', fontSize: 11, color: '#94a3b8', whiteSpace: 'nowrap' }}>
      vous avez {n} {mot} au total
    </span>
  )
}

export default function Accueil({ user, matiereLabel, niveau, onNavigate, onOuvrir }) {

  // Le tableau de bord, lu en base — react-query tient la lecture. Une lecture ratée se DIT
  // (modale + « Réessayer ») : elle ne se déguise jamais en tableau de bord vide.
  const { data = null, isError: chargementRate, error, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => await lireReponse(
      await fetchWithTimeout('/api/dashboard', { credentials: 'include' }, TIMEOUT_STD)),
  })
  useEffect(() => { if (error) showError(messagePourEcran(error)) }, [error])
  const charger = () => refetch()

  const hour     = new Date().getHours()
  const greeting = hour < 12 ? 'Bonjour' : hour < 18 ? 'Bon après-midi' : 'Bonsoir'
  const prenom   = user?.prenom || ''
  const phrase   = data !== null ? getPhrase(data.mes_activites) : ''

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minWidth: 0, height: '100%', minHeight: 0 }}>

      {/* ZONE HAUTE — fixe. Elle ne défile pas et ne rétrécit pas : c'est l'identité de l'écran
          (qui je suis, ma matière, mon niveau), elle reste sous les yeux quoi qu'il arrive. */}
      <div style={{
        background: 'linear-gradient(135deg, #1e40af 0%, #5b21b6 55%, var(--bordeaux) 100%)',
        borderRadius: 12, padding: '22px 28px', color: '#fff',
        position: 'relative', overflow: 'hidden', flexShrink: 0,
      }}>
        {/* LA NOUVEAUTÉ SE POSE ICI, à droite du bandeau : c'est le premier endroit que l'œil
            balaie en arrivant, et le seul qui ne défile pas. Elle se lit sans qu'on la clique —
            mais elle reste une bande, elle ne prend pas la place du travail. */}
        <div style={{
          position: 'absolute', top: 16, right: 22, zIndex: 2,
        }}>
          <Nouveautes onNavigate={onNavigate} />
        </div>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ fontSize: 21, fontWeight: 800, letterSpacing: '-0.02em' }}>
            {greeting}{prenom ? `, ${prenom}` : ''} !
            {astucesAccueil && <InfoGuide {...astucesAccueil} />}
          </div>
          <div style={{ fontSize: 12, opacity: 0.72, marginTop: 3 }}>
            {matiereLabel} · Niveau {niveau}
          </div>
          {phrase && (
            <div style={{ fontSize: 13, marginTop: 11, opacity: 0.9, fontStyle: 'italic', maxWidth: 520 }}>
              {phrase}
            </div>
          )}
        </div>
        <div style={{ position: 'absolute', right: -24, top: -24, width: 130, height: 130, borderRadius: '50%', background: 'rgba(255,255,255,0.06)' }} />
        <div style={{ position: 'absolute', right: 70, bottom: -28, width: 80, height: 80, borderRadius: '50%', background: 'rgba(255,255,255,0.04)' }} />
      </div>

      {/* ZONE BASSE — la seule qui défile. Elle porte son propre ascenseur : rien ne passe
          jamais derrière le bandeau, les deux zones ne se recouvrent pas. */}
      <div className="sidebar-scroll" style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0, flex: '1 1 auto', minHeight: 0, paddingRight: 4 }}>

        {/* ── Mes dernières créations — MONDE NEUF : les cartes rouvrent dans Mes contenus ── */}
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#1e293b' }}>Mes dernières créations</div>

          {chargementRate && (
            <button onClick={charger} className="btn-primary" style={{ alignSelf: 'flex-start' }}
              title="Recharger le tableau de bord">
              Réessayer
            </button>
          )}

          {/* LES TROIS TYPES, DANS L'ORDRE DU MENU (16/08/2026). L'écran n'en montrait que deux —
              la séquence n'était ni calculée par le serveur ni prévue ici — et ses trois
              sous-titres étaient en gris pâle, sans la couleur que le reste de l'application
              donne pourtant à chaque type. Une seule boucle : trois blocs qui ne peuvent plus
              diverger, chacun à sa couleur et à son icône. */}
          {TYPES.map(t => {
            const dernier = data?.[t.champ] ?? null
            const total = data?.[t.total] ?? 0
            return (
              <div key={t.type}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 7 }}>
                  <t.Icon taille={15} couleur={t.accent} />
                  <span style={{ fontSize: 13, fontWeight: 800, color: '#1e293b', letterSpacing: '-0.01em' }}>{t.label}</span>
                  <Total n={total} bloc={t} />
                </div>
                {dernier ? (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '9px 12px', borderRadius: 7, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                    <div style={{ minWidth: 0, flex: '1 1 auto' }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {dernier.titre}
                      </div>
                      <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>
                        {[dernier.matiere, dernier.niveau,
                          dernier.duree_minutes ? `${dernier.duree_minutes} min` : null]
                          .filter(Boolean).join(' · ')}
                      </div>
                    </div>
                    <button
                      onClick={() => onOuvrir(t.type, dernier.id)}
                      title={t.titreOuvrir}
                      className="btn-secondary"
                      style={{ flexShrink: 0, padding: '4px 10px', fontSize: 11, whiteSpace: 'nowrap' }}
                    >
                      Ouvrir →
                    </button>
                  </div>
                ) : (
                  <div style={EMPTY_MSG}>{t.vide}</div>
                )}
                <button onClick={() => onNavigate(t.page)} title={t.titreListe}
                  style={{ marginTop: 7, background: 'none', border: 'none', padding: 0, fontSize: 11, color: '#64748b', cursor: 'pointer', textDecoration: 'underline' }}>
                  {t.lienListe} →
                </button>
              </div>
            )
          })}

          {/* LES TROIS ANALYSES, ÉCRITES COMME LES TROIS TYPES (16/08/2026) : même icône en tête,
              même titre en gras à leur couleur, même ligne teintée avec son « Ouvrir ». Elles
              étaient trois boutons gris sous une étiquette « ANALYSE » — l'étiquette a disparu,
              le nom de chaque analyse la remplace. */}
          {ANALYSES.map(a => (
            <div key={a.page}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 7 }}>
                <span style={{ color: a.accent, display: 'inline-flex' }}><a.Icon taille={15} /></span>
                <span style={{ fontSize: 13, fontWeight: 800, color: '#1e293b', letterSpacing: '-0.01em' }}>{a.label}</span>
                <Total n={data?.[a.total] ?? 0} bloc={a} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '9px 12px', borderRadius: 7, background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: 12, color: '#475569', minWidth: 0, flex: '1 1 auto', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {a.phrase}
                </div>
                <button
                  onClick={() => onNavigate(a.page)}
                  title={a.phrase}
                  className="btn-secondary"
                  style={{ flexShrink: 0, padding: '4px 10px', fontSize: 11, whiteSpace: 'nowrap' }}
                >
                  Ouvrir →
                </button>
              </div>
            </div>
          ))}

        </div>

      </div>

    </div>
  )
}
