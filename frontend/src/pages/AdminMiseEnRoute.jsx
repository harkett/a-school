import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import ActionsAdmin from '../components/ActionsAdmin.jsx'
import ConsommationIA from '../components/ConsommationIA.jsx'

// TABLEAU DE BORD de la plateforme. Deux natures de vérité, jamais mélangées :
//
//   TECHNIQUE — les 8 étapes de branchement, DÉRIVÉES des vraies tables (une clé existe ou non,
//   un email est parti ou non). Rien n'est coché à la main, rien n'est stocké.
//
//   ADMIN et PROF — l'état des fonctionnalités, LU dans `fonctionnalites`. Il ne se dérive pas :
//   aucune table ne sait qu'un bouton est posé mais inactif. La table est tenue par migration à
//   chaque livraison ; l'admin consulte, il n'édite pas.
//
// L'écran d'avant ne montrait que la première et annonçait « Tout est prêt » dès qu'elle était
// verte — vrai sur la plomberie, faux sur le produit. Les deux sont ici, côte à côte.

// Le bouton « spec » ouvre L'EXPLORATEUR WINDOWS sur le dossier des spécifications. Une page
// web ne peut pas lancer un programme ni suivre un chemin `file://` — le navigateur l'interdit.
// Elle peut, en revanche, appeler un PROTOCOLE déclaré dans Windows : `aschool-spec:` est
// enregistré une fois par Scripts/aschool-spec.reg, et Windows répond en ouvrant l'explorateur
// sur le dossier. Le chemin vit donc dans le .reg, sur la machine de l'administrateur, et pas ici.
// `SPECS` dit quelles lignes portent le bouton — une ligne s'ajoute quand sa spec est écrite.
const PROTOCOLE_SPECS = 'aschool-spec:'
const SPECS = ['CCF']

const COULEURS = {
  fait:     { pastille: '#16a34a', fond: '#f0fdf4', bord: '#bbf7d0', texte: '#15803d',
              libelle: 'fait', phrase: 'fait — livré et utilisable' },
  en_cours: { pastille: '#f59e0b', fond: '#fffbeb', bord: '#fde68a', texte: '#b45309',
              libelle: 'en cours', phrase: 'en cours — visible, pas utilisable' },
  a_venir:  { pastille: '#cbd5e1', fond: '#f8fafc', bord: '#e2e8f0', texte: '#94a3b8',
              libelle: 'à venir', phrase: 'à venir — rien encore' },
}

// LA LÉGENDE — au plus près de ce qu'elle explique, et réduite aux états RÉELLEMENT présents.
// Reléguée en pied de page, elle se lisait après la liste qu'elle devait aider à lire ; et une
// entrée « fait » sous une liste d'où le fait est exclu n'explique rien, elle égare.
function Legende({ etats }) {
  return (
    // Gris ardoise et non gris pâle : à #94a3b8, la légende s'effaçait sur les écrans peu
    // contrastés — une explication qu'on ne voit pas n'explique rien.
    <div style={{ display: 'flex', gap: 16, fontSize: 11.5, fontWeight: 600, color: '#475569',
                  flexWrap: 'wrap' }}>
      {etats.map(cle => (
        <span key={cle} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: COULEURS[cle].pastille }} />
          {COULEURS[cle].phrase}
        </span>
      ))}
    </div>
  )
}

// Les titres de l'écran, à UNE seule place : un titre de section domine un titre de cartouche,
// qui domine une entrée de menu. Trois corps, jamais quatre — et jamais deux valeurs pour le
// même rang, sinon la hiérarchie se défait au premier écran ajouté.
const TITRE_SECTION  = { fontSize: 24, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.015em' }
const TITRE_CARTOUCHE = { fontSize: 14, fontWeight: 700, color: '#1e293b' }

// L'EN-TÊTE D'UNE SECTION — ce qui explique la liste à gauche, ce qui la mesure à droite.
//
// PAS DE TITRE ICI. Il y en avait un, et c'était le doublon exact de l'entrée de menu posée à
// deux centimètres, dans un autre corps : le même texte écrit deux fois, à deux tailles, se lit
// comme deux choses différentes. Le titre de la section est l'entrée de menu sélectionnée — un
// seul endroit, celui qu'on vient de cliquer.
function EnteteSection({ milieu, droite }) {
  if (!milieu && !droite) return null
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, flexWrap: 'wrap' }}>
      {milieu}
      {droite && (
        <div style={{ marginLeft: 'auto', fontSize: 12.5, color: '#64748b' }}>{droite}</div>
      )}
    </div>
  )
}

// Une jauge lue d'un coup d'œil : la barre porte le pourcentage, jamais un chiffre à décimale.
function Jauge({ pourcent, hauteur = 8, couleur = '#2563eb', fond = '#e2e8f0' }) {
  return (
    <div style={{ background: fond, borderRadius: hauteur, height: hauteur, overflow: 'hidden', width: '100%' }}>
      <div style={{
        width: `${pourcent}%`, height: '100%', background: couleur,
        borderRadius: hauteur, transition: 'width 0.4s ease',
      }} />
    </div>
  )
}

function Pastille({ etat }) {
  const c = COULEURS[etat] || COULEURS.a_venir
  return (
    <span
      title={c.libelle}
      style={{
        flexShrink: 0, width: 9, height: 9, borderRadius: '50%', background: c.pastille,
        display: 'inline-block', marginTop: 5,
      }}
    />
  )
}

export default function AdminMiseEnRoute() {
  const navigate = useNavigate()
  // La section ouverte. Vue d'ensemble par défaut : on entre par la synthèse, on descend ensuite.
  const [section, setSection] = useState('ensemble')

  // Le bandeau et le menu de gauche restent à l'écran quand la liste défile. Le menu doit se
  // figer SOUS le bandeau : sa hauteur se MESURE (elle change avec la largeur — les trois axes
  // passent à la ligne), elle ne se devine pas dans une constante qui mentirait au premier
  // redimensionnement.
  const bandeauRef = useRef(null)
  const [hautBandeau, setHautBandeau] = useState(0)
  useEffect(() => {
    const el = bandeauRef.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(() => setHautBandeau(el.offsetHeight))
    ro.observe(el)
    setHautBandeau(el.offsetHeight)
    return () => ro.disconnect()
  }, [])

  // Deux lectures indépendantes : la plomberie et les fonctionnalités. react-query les tient,
  // l'écran n'en garde aucune copie.
  const { data: tech, isError: techKo, refetch: relireTech } = useQuery({
    queryKey: ['admin', 'mise-en-route'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/mise-en-route/etat', { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error('état technique illisible')
      return await r.json()
    },
  })
  const { data: fonc, isError: foncKo, refetch: relireFonc } = useQuery({
    queryKey: ['admin', 'fonctionnalites'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/fonctionnalites', { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) throw new Error('inventaire illisible')
      return await r.json()
    },
  })

  if (techKo || foncKo) return (
    <div style={{ fontSize: 13, color: '#64748b' }}>
      Impossible de lire l'état de la plateforme pour le moment.{' '}
      <button onClick={() => { relireTech(); relireFonc() }} style={lienStyle}>Réessayer</button>
    </div>
  )
  if (!tech || !fonc) return <div style={{ fontSize: 13, color: '#94a3b8' }}>Chargement…</div>

  const etapes = tech.etapes
  const techFait = etapes.filter(e => e.fait).length
  const domAdmin = fonc.domaines.find(d => d.domaine === 'admin')
  const domProf = fonc.domaines.find(d => d.domaine === 'prof')

  const SECTIONS = [
    // « Vue d'ensemble » ne disait pas de QUOI : la section ne montre que ce qui reste, le
    // fait n'y a jamais eu sa place. Le nom le dit maintenant, ici comme dans son titre.
    { cle: 'ensemble', label: "Vue d'ensemble du reste à faire", compte: null, pourcent: null },
    { cle: 'technique', label: 'Technique', compte: `${techFait}/${etapes.length}`,
      pourcent: Math.round(100 * techFait / etapes.length) },
    { cle: 'admin', label: 'Côté admin', compte: domAdmin ? `${domAdmin.fait}/${domAdmin.total}` : '',
      pourcent: domAdmin ? domAdmin.pourcent : 0 },
    { cle: 'prof', label: 'Côté prof', compte: domProf ? `${domProf.fait}/${domProf.total}` : '',
      pourcent: domProf ? domProf.pourcent : 0 },
  ]

  return (
    <div style={{ maxWidth: 1080 }}>
      {/* ── BANDEAU — l'avancement global, compté et non déclaré ───────────────────────── */}
      {/* L'enveloppe colle en haut et PEINT le fond de la page (marges négatives : elle reprend
          les 32 px de rembourrage du gabarit admin). Sans elle, la liste défilerait à nu dans
          la bande laissée au-dessus du bandeau. */}
      <div ref={bandeauRef} style={{
        position: 'sticky', top: 0, zIndex: 20, background: '#f0f4f8',
        margin: '-32px -32px 0', padding: '32px 32px 18px',
      }}>
      <div style={{
        borderRadius: 12, padding: '20px 24px',
        background: 'linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%)', color: '#fff',
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ fontSize: 16, fontWeight: 700 }}>aSchool — état de la plateforme</div>
          <button onClick={() => { relireTech(); relireFonc() }} title="Relire l'état en base"
            style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,0.75)', fontSize: 12,
                     cursor: 'pointer', textDecoration: 'underline', padding: 0 }}>
            Rafraîchir
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 14 }}>
          <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: '-0.02em', minWidth: 68 }}>
            {fonc.pourcent} %
          </div>
          <div style={{ flex: 1, minWidth: 160 }}>
            <Jauge pourcent={fonc.pourcent} hauteur={10} couleur="#4ade80" fond="rgba(255,255,255,0.18)" />
            <div style={{ fontSize: 12, opacity: 0.82, marginTop: 7 }}>
              {fonc.par_etat.fait} faites · {fonc.par_etat.en_cours} en cours · {fonc.par_etat.a_venir} à venir
            </div>
          </div>
        </div>

        {/* Les trois axes en un coup d'œil. La technique est comptée à part : elle se dérive. */}
        <div style={{ display: 'flex', gap: 22, marginTop: 16, flexWrap: 'wrap' }}>
          {[
            { titre: 'Technique', fait: techFait, total: etapes.length },
            { titre: 'Admin', fait: domAdmin?.fait ?? 0, total: domAdmin?.total ?? 0 },
            { titre: 'Prof', fait: domProf?.fait ?? 0, total: domProf?.total ?? 0 },
          ].map(a => (
            <div key={a.titre} style={{ minWidth: 128 }}>
              <div style={{ fontSize: 11, opacity: 0.72, marginBottom: 5 }}>
                {a.titre} · {a.fait}/{a.total}
              </div>
              <Jauge pourcent={a.total ? Math.round(100 * a.fait / a.total) : 0}
                     hauteur={5} couleur="rgba(255,255,255,0.85)" fond="rgba(255,255,255,0.18)" />
            </div>
          ))}
        </div>
      </div>
      </div>

      {/* CE QUI ATTEND UN GESTE, avant tout le reste. L'état de la plateforme se consulte ; une
          action, elle, s'impose — elle ne se range donc pas dans une colonne qu'il faut aller
          chercher. L'encart ne s'affiche pas du tout quand il n'y a rien à faire. */}
      <ActionsAdmin />

      {/* CE QUE LA PLATEFORME DÉPENSE, juste après ce qui attend un geste et avant l'état
          détaillé : une facture qui se consulte dans un écran dédié ne se regarde qu'une fois
          qu'on s'inquiète. Le détail reste à IA › Statistiques, où la cartouche renvoie. */}
      <ConsommationIA />

      <div style={{ display: 'flex', gap: 18, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        {/* ── MENU DE GAUCHE — collé sous le bandeau, à la hauteur mesurée ─────────────── */}
        <nav style={{ flex: '0 0 250px', display: 'flex', flexDirection: 'column', gap: 10,
                      position: 'sticky', top: hautBandeau, alignSelf: 'flex-start' }}>
          {SECTIONS.map(s => {
            const actif = section === s.cle
            return (
              <button key={s.cle} onClick={() => setSection(s.cle)}
                title={`Voir : ${s.label}`}
                style={{
                  textAlign: 'left', padding: 0, background: 'none', border: 'none',
                  cursor: actif ? 'default' : 'pointer', fontFamily: 'inherit',
                }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8,
                              alignItems: 'baseline' }}>
                  <span style={actif
                    ? { ...TITRE_SECTION, lineHeight: 1.2 }
                    : { fontSize: 14, fontWeight: 600, color: '#64748b' }}>
                    {s.label}
                  </span>
                  {s.compte && (
                    <span style={{ fontSize: 11.5, color: '#94a3b8', flexShrink: 0,
                                   fontVariantNumeric: 'tabular-nums' }}>
                      {s.compte}
                    </span>
                  )}
                </div>
                {s.pourcent !== null && (
                  <div style={{ marginTop: 6 }}>
                    <Jauge pourcent={s.pourcent} hauteur={4} couleur={actif ? '#2563eb' : '#cbd5e1'} />
                  </div>
                )}
              </button>
            )
          })}
        </nav>

        {/* ── PANNEAU DE DROITE ───────────────────────────────────────────────────────── */}
        <div style={{ flex: '1 1 480px', minWidth: 0 }}>
          {section === 'ensemble' && (
            <VueEnsemble fonc={fonc} etapes={etapes} techFait={techFait}
                         onAller={setSection} />
          )}
          {section === 'technique' && <Technique etapes={etapes} navigate={navigate} />}
          {section === 'admin' && domAdmin && <Domaine dom={domAdmin} />}
          {section === 'prof' && domProf && <Domaine dom={domProf} />}
        </div>
      </div>

      {/* Plus de légende en pied de page : chaque section porte la sienne EN TÊTE, réduite aux
          états qu'elle affiche. Une clé de lecture placée après la liste arrive trop tard, et
          celle du pied listait trois états quelle que soit la section regardée. */}
    </div>
  )
}

// ── VUE D'ENSEMBLE DU RESTE À FAIRE ─────────────────────────────────────────────────────
//
// CE QUI EST FAIT NE S'AFFICHE PLUS. Une liste où le fait côtoie le reste demande à l'œil de
// trier avant de lire, et ce tri se refait à chaque visite. Ce qui est fait est fait : il se
// compte (le bandeau le fait), il ne s'énumère pas.
//
// LE RESTE VIENT DE TROIS CARNETS QUI NE SE PARLAIENT PAS :
//   · les fonctionnalités pas encore livrées (`fonctionnalites`, admin et prof mêlés) ;
//   · le carnet de l'administrateur (Admin › Tâches à faire) ;
//   · ce qui est promis aux professeurs (Admin › Bientôt disponible, non livré).
// Chacun avait son écran, aucun n'avait de vue commune — donc personne ne savait ce qui restait
// AU TOTAL. Les trois se lisent ici, chacun gardant son écran pour agir.
//
// La plomberie technique ne paraît QUE si elle a du retard : « tout est branché » est du fait,
// et le fait n'a rien à faire dans cette vue.
function VueEnsemble({ fonc, etapes, techFait, onAller }) {
  const restant = etapes.length - techFait
  const enChantier = fonc.domaines.flatMap(d =>
    d.ecrans.flatMap(e =>
      e.lignes.filter(l => l.etat !== 'fait')
              .map(l => ({ ...l, domaine: d.domaine, ecran: e.ecran }))))

  // Les deux autres carnets. Une lecture qui échoue rend une liste vide : la vue perd un bloc,
  // elle ne tombe pas — c'est le même principe que les sources du centre d'actions.
  const { data: carnet } = useQuery({
    queryKey: ['admin', 'taches-a-faire'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/taches-a-faire', { credentials: 'include' }, TIMEOUT_STD)
      return r.ok ? await r.json() : { taches: [] }
    },
  })
  const { data: bientot } = useQuery({
    queryKey: ['admin', 'feature-votes'],
    queryFn: async () => {
      const r = await fetchWithTimeout('/api/admin/feature-votes', { credentials: 'include' }, TIMEOUT_STD)
      return r.ok ? await r.json() : []
    },
  })

  const aFaire = (carnet?.taches || []).filter(t => !t.fait)
  // Non livrée = encore à faire. Une carte livrée reste à l'écran des votes, elle n'est plus un
  // chantier — la ranger ici ferait grossir le reste à faire d'un travail déjà terminé.
  const promises = (bientot || []).filter(f => !f.livree)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* LE TITRE, ET LA LÉGENDE EN FACE. Elle explique les pastilles de la première liste ;
          au pied de la page, elle arrivait après ce qu'elle devait aider à lire. */}
      <EnteteSection milieu={<Legende etats={['en_cours', 'a_venir']} />} />

      {/* La plomberie : visible seulement quand elle retient quelque chose. */}
      {restant > 0 && (
        <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 10,
                      padding: '14px 16px' }}>
          <div style={{ ...TITRE_CARTOUCHE, marginBottom: 3 }}>
            Plomberie technique : {restant} étape{restant > 1 ? 's' : ''} à faire
          </div>
          <div style={{ fontSize: 12, color: '#475569', lineHeight: 1.55 }}>
            Certaines briques ne sont pas encore branchées : ouvrez l'onglet Technique pour savoir
            lesquelles.
          </div>
          <button onClick={() => onAller('technique')} style={{ ...lienStyle, fontSize: 12, marginTop: 8 }}
            title="Voir le détail des étapes techniques">
            Voir le détail
          </button>
        </div>
      )}

      {/* 1. LES FONCTIONNALITÉS — celles qui portent un état, donc une pastille. */}
      <Carnet titre="Fonctionnalités en chantier" compte={`${enChantier.length} sur ${fonc.total}`}
              vide="Toutes les fonctionnalités recensées sont livrées.">
        {enChantier.map((l, i) => (
          <Ligne key={`${l.domaine}-${l.ecran}-${l.nom}`} ligne={l} premier={i === 0}
                 prefixe={`${l.domaine === 'admin' ? 'Admin' : 'Prof'} · ${l.ecran}`} />
        ))}
      </Carnet>

      {/* 2. LE CARNET DE L'ADMINISTRATEUR — noté à la main, sans état ni preuve : c'est un
             carnet, il ne contient que ce qu'on y écrit. */}
      <Carnet titre="Carnet de l'administrateur" compte={`${aFaire.length}`}
              lien="/admin/taches-a-faire"
              vide="Rien de noté dans le carnet.">
        {aFaire.map((t, i) => (
          <LigneSimple key={t.id} titre={t.titre} detail={t.detail} premier={i === 0} />
        ))}
      </Carnet>

      {/* 3. CE QUI EST PROMIS AUX PROFESSEURS — ils le voient et ils votent dessus, donc c'est
             un engagement, pas une idée. */}
      <Carnet titre="Promis aux professeurs" compte={`${promises.length}`}
              lien="/admin/bientot-disponible"
              vide="Tout ce qui est annoncé aux professeurs est livré.">
        {promises.map((f, i) => (
          <LigneSimple key={f.key} titre={f.label} detail={f.description} premier={i === 0}
                       marque={f.count > 0 ? `${f.count} vote${f.count > 1 ? 's' : ''}` : null} />
        ))}
      </Carnet>
    </div>
  )
}


// UN CARNET — un en-tête, un compte, et ses lignes. Trois listes de natures différentes, un
// seul moule : sans lui, chacune dériverait à sa prochaine retouche.
//
// Un carnet vide GARDE sa place et le dit. C'est l'inverse de l'encart « À traiter », qui
// disparaît quand il n'y a rien : là, l'absence est une information (« rien ne reste »), ici
// elle serait un trou dans une vue qui prétend tout montrer.
function Carnet({ titre, compte, lien, vide, children }) {
  const lignes = Array.isArray(children) ? children.filter(Boolean) : (children ? [children] : [])
  return (
    <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f1f5f9', display: 'flex',
                    justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}>
        <span style={TITRE_CARTOUCHE}>{titre}</span>
        <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 12 }}>
          <span style={{ fontSize: 12, color: '#94a3b8', fontVariantNumeric: 'tabular-nums' }}>{compte}</span>
          {lien && (
            <Link to={lien} style={{ fontSize: 12, fontWeight: 600, color: '#1F6EEB',
                                     textDecoration: 'none', whiteSpace: 'nowrap' }}
                  title="Ouvrir l'écran où ces lignes se modifient">
              Ouvrir →
            </Link>
          )}
        </span>
      </div>
      {lignes.length === 0
        ? <div style={{ padding: 16, fontSize: 13, color: '#64748b' }}>{vide}</div>
        : <div>{lignes}</div>}
    </div>
  )
}


// UNE LIGNE SANS ÉTAT — pour les deux carnets tenus à la main. Pas de pastille : ni le carnet
// ni les cartes de vote ne portent d'état vérifié, et une pastille inventée ici serait une
// affirmation que rien ne soutient.
function LigneSimple({ titre, detail, premier, marque }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '9px 15px',
                  borderTop: premier ? 'none' : '1px solid #f8fafc' }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, color: '#334155' }}>{titre}</div>
        {detail && (
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2, lineHeight: 1.45 }}>{detail}</div>
        )}
      </div>
      {marque && (
        <span style={{ flexShrink: 0, fontSize: 10.5, fontWeight: 700, color: '#64748b',
                       background: '#f1f5f9', borderRadius: 4, padding: '2px 7px', marginTop: 1,
                       whiteSpace: 'nowrap' }}>
          {marque}
        </span>
      )}
    </div>
  )
}


// ── TECHNIQUE ───────────────────────────────────────────────────────────────────────────
// Les 8 étapes, telles qu'elles étaient : le message et le bouton n'apparaissent que sur une
// étape à faire — une étape faite n'a plus rien à dire.
function Technique({ etapes, navigate }) {
  const restant = etapes.filter(e => !e.fait).length
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ marginBottom: 4 }}>
        <EnteteSection
          droite={restant === 0 ? 'tout est branché'
                                : `${restant} étape${restant > 1 ? 's' : ''} à faire`}
        />
      </div>
      {etapes.map(e => (
        <div key={e.num} style={{
          display: 'flex', alignItems: 'flex-start', gap: 13,
          background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '13px 15px',
        }}>
          <span style={{
            flexShrink: 0, marginTop: 1, width: 22, height: 22, borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: e.fait ? '#16a34a' : '#fee2e2',
            color: e.fait ? '#fff' : '#dc2626', fontSize: 11, fontWeight: 700,
            border: e.fait ? 'none' : '1px solid #fecaca',
          }}>
            {e.fait
              ? <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              : e.num}
          </span>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{e.titre}</div>
            {!e.fait && (
              <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.55, marginTop: 4 }}>{e.message}</div>
            )}
          </div>

          {!e.fait && e.ecran && (
            <button onClick={() => navigate(e.ecran)} className="btn-primary"
              style={{ flexShrink: 0, whiteSpace: 'nowrap' }}
              title={`Aller à l’écran pour : ${e.titre}`}>
              Aller à l'écran
            </button>
          )}
          {e.fait && (
            <span style={{ flexShrink: 0, fontSize: 11, fontWeight: 600, color: '#16a34a', marginTop: 3 }}>Fait</span>
          )}
        </div>
      ))}
    </div>
  )
}

// ── UN DOMAINE (admin ou prof) ──────────────────────────────────────────────────────────
// Groupé par écran, chaque groupe avec sa jauge : c'est l'écran qui parle à l'admin, pas la
// fonctionnalité isolée.
function Domaine({ dom }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <EnteteSection
        milieu={<Legende etats={['fait', 'en_cours', 'a_venir']} />}
        droite={<span style={{ fontVariantNumeric: 'tabular-nums' }}>
          {dom.fait} / {dom.total} · {dom.pourcent} %
        </span>}
      />

      {dom.ecrans.map(e => (
        <div key={e.ecran} style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden' }}>
          <div style={{ padding: '11px 15px', borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 10 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{e.ecran}</span>
              <span style={{ fontSize: 11, color: '#94a3b8', fontVariantNumeric: 'tabular-nums' }}>
                {e.fait}/{e.total}
              </span>
            </div>
            <div style={{ marginTop: 7 }}>
              <Jauge pourcent={e.pourcent} hauteur={4}
                     couleur={e.pourcent === 100 ? '#16a34a' : '#f59e0b'} />
            </div>
          </div>
          <div>
            {e.lignes.map((l, i) => <Ligne key={l.nom} ligne={l} premier={i === 0} />)}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── UNE LIGNE ───────────────────────────────────────────────────────────────────────────
// La `note` est la PREUVE : elle dit d'où vient l'état — « bouton posé, inactif », « page vide ».
// Sans elle, une ligne « en cours » est une affirmation qu'on ne peut ni vérifier ni contester.
function Ligne({ ligne, premier, prefixe }) {
  const c = COULEURS[ligne.etat] || COULEURS.a_venir
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10, padding: '9px 15px',
      borderTop: premier ? 'none' : '1px solid #f8fafc',
    }}>
      <Pastille etat={ligne.etat} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, color: ligne.etat === 'a_venir' ? '#94a3b8' : '#334155' }}>
          {prefixe && <span style={{ color: '#94a3b8' }}>{prefixe} · </span>}
          {ligne.nom}
        </div>
        {ligne.note && (
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2, fontStyle: 'italic' }}>{ligne.note}</div>
        )}
      </div>
      {SPECS.includes(ligne.nom) && (
        <a href={PROTOCOLE_SPECS}
          title="Ouvrir l'explorateur Windows sur le dossier des spécifications"
          style={{
            flexShrink: 0, fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.03em', cursor: 'pointer', marginTop: 1, whiteSpace: 'nowrap',
            color: '#1F6EEB', background: '#eff6ff', border: '1px solid #bfdbfe',
            borderRadius: 4, padding: '2px 7px', textDecoration: 'none',
          }}>
          spec
        </a>
      )}
      <span style={{
        flexShrink: 0, fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.03em',
        color: c.texte, background: c.fond, border: `1px solid ${c.bord}`,
        borderRadius: 4, padding: '2px 7px', marginTop: 1, whiteSpace: 'nowrap',
      }}>
        {c.libelle}
      </span>
    </div>
  )
}

const lienStyle = {
  background: 'none', border: 'none', color: '#1F6EEB',
  cursor: 'pointer', textDecoration: 'underline', fontSize: 13, padding: 0,
}
