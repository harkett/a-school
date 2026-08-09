import { useEffect, useState } from 'react'
import OngletsPrompts from '../components/OngletsPrompts'
import { fetchWithTimeout, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import SplitPane from '../components/SplitPane.jsx'
import FenetrePro from '../components/FenetrePro.jsx'

// Écran « Prompts → Référentiels » (06/08/2026) — LA SAISIE À LA MAIN des prompts d'un niveau.
// Il n'existait aucun endroit pour les écrire soi-même : ils ne pouvaient venir que de l'IA, donc
// d'un appel facturé. Ici, doter un référentiel coûte zéro.
//
// QUATRE COUPLES, huit textes, et le même geste dans les quatre — un méta-prompt qui fait ÉCRIRE
// un prompt, et le prompt qui TRAVAILLE :
//   - matières : prompt_meta_matieres (repère {document}) → prompt_matieres (repère {texte}) ;
//   - découpe  : prompt_meta_decoupe  (repère {document}) → prompt_decoupe  (repère {texte}) ;
//   - types    : prompt_meta_types    (repère {document}) → prompt_types    (repère {texte}) ;
//   - précisions : prompt_meta_precisions (repère {document}) → prompt_precisions ({texte} + {label}).
// Ils ne sont PAS dans le registre des prompts d'outils (llm_prompts) : ce sont des colonnes de la
// table `referentiels`, une ligne par niveau — d'où une liste, et non un texte unique. Le nom du
// niveau n'apparaît donc dans aucune clé : il EST la ligne.
//
// Deux colonnes comme les autres écrans de Prompts : la liste des niveaux à gauche, le niveau
// choisi à droite avec ses liens. Le bouton « Cacher le détail » est permanent (règle maison).
const CHAMPS = [
  {
    cle: 'meta',
    groupe: 'Matières',
    route: '/api/admin/referentiels/prompt-meta-matieres',
    colonne: 'referentiels.prompt_meta_matieres',
    titre: 'prompt_meta_matieres',
    role: 'La consigne qui sert à ÉCRIRE le prompt de lecture. Elle reçoit le document et rend un prompt.',
    repere: '{document}',
    repli: 'Vide : rien ne sert. La génération lèvera tant que cette case est vide.',
  },
  {
    cle: 'lecture',
    groupe: 'Matières',
    route: '/api/admin/referentiels/prompt-matieres/valider',
    colonne: 'referentiels.prompt_matieres',
    titre: 'prompt_matieres',
    role: 'Le prompt qui LIT le document et rend la liste des matières. C’est lui qui travaille.',
    repere: '{texte}',
    repli: 'Vide impossible : le serveur refuse un prompt vide. Tant qu’il n’existe pas, l’IA l’écrit au premier « Proposer les matières » — un appel payant de plus.',
  },
  {
    cle: 'meta_decoupe',
    groupe: 'Découpe',
    route: '/api/admin/referentiels/prompt-meta-decoupe',
    colonne: 'referentiels.prompt_meta_decoupe',
    titre: 'prompt_meta_decoupe',
    role: 'La consigne qui sert à ÉCRIRE le prompt de découpe. Elle reçoit le document et rend un prompt.',
    repere: '{document}',
    repli: 'Vide : rien ne sert. La génération lèvera tant que cette case est vide.',
  },
  {
    cle: 'decoupe',
    groupe: 'Découpe',
    route: '/api/admin/referentiels/prompt-decoupe/valider',
    colonne: 'referentiels.prompt_decoupe',
    titre: 'prompt_decoupe',
    role: 'Le prompt qui DÉCOUPE le document en unités. C’est lui qui travaille.',
    repere: '{texte}',
    repli: 'Vide impossible : le serveur refuse un prompt vide. Tant qu’il n’existe pas, l’IA l’écrit au premier « Découper » — un appel payant de plus.',
  },
  {
    cle: 'meta_types',
    groupe: 'Types d’activité',
    route: '/api/admin/referentiels/prompt-meta-types',
    colonne: 'referentiels.prompt_meta_types',
    titre: 'prompt_meta_types',
    role: 'La consigne qui sert à ÉCRIRE le prompt de lecture des types. Elle reçoit le document et rend un prompt.',
    repere: '{document}',
    repli: 'Vide : rien ne sert. La génération lèvera tant que cette case est vide.',
  },
  {
    cle: 'types',
    groupe: 'Types d’activité',
    route: '/api/admin/referentiels/prompt-types/valider',
    colonne: 'referentiels.prompt_types',
    titre: 'prompt_types',
    role: 'Le prompt qui LIT le document et rend la liste des types d’activité. C’est lui qui travaille.',
    repere: '{texte}',
    repli: 'Vide impossible : le serveur refuse un prompt vide. Tant qu’il n’existe pas, l’IA l’écrit au premier « Détecter les types » — un appel payant de plus.',
  },
  {
    cle: 'meta_precisions',
    groupe: 'Précisions (plusieurs précisions par type)',
    route: '/api/admin/referentiels/prompt-meta-precisions',
    colonne: 'referentiels.prompt_meta_precisions',
    titre: 'prompt_meta_precisions',
    role: 'La consigne qui sert à ÉCRIRE le prompt des précisions. Elle reçoit le document et rend un prompt.',
    repere: '{document}',
    repli: 'Vide : rien ne sert. La génération lèvera tant que cette case est vide.',
  },
  {
    cle: 'precisions',
    groupe: 'Précisions (plusieurs précisions par type)',
    route: '/api/admin/referentiels/prompt-precisions/valider',
    colonne: 'referentiels.prompt_precisions',
    titre: 'prompt_precisions',
    role: 'Le prompt qui LIT le document et rend les précisions d’UN type d’activité. C’est lui qui travaille.',
    // Seul champ à DEUX repères : le document et le nom du type dont on veut les précisions.
    repere: '{texte}',
    repere2: '{label}',
    repli: 'Vide impossible : le serveur refuse un prompt vide. Tant qu’il n’existe pas, l’IA l’écrit à la première génération de précisions — un appel payant de plus.',
  },
]

// LE NEUVIÈME PROMPT, ET IL N'EST PAS DANS `CHAMPS` (08/08/2026). `types_activite.prompt` est le
// prompt de GÉNÉRATION : celui qui décide de ce que le professeur reçoit quand il clique. C'était
// le SEUL prompt du produit absent de cet écran, parce qu'il ne rentre pas dans le moule des huit
// autres — ceux-là sont huit colonnes fixes de `referentiels`, celui-ci est une ligne par TYPE, en
// nombre variable (deux pour la crèche, douze pour un BTS). Il vivait donc uniquement derrière le
// ✎ Prompt de l'écran Référentiels, et l'écran qui s'appelle « Prompts » ne le montrait pas.
//
// Il se greffe ici en groupe supplémentaire, un bouton par type, alimenté par la liste des types
// du niveau choisi. Aucune nouvelle porte d'écriture : c'est la MÊME route que le ✎ Prompt.
const CHAMP_TYPE = {
  groupe: 'Génération (un prompt par type)',
  route: '/api/admin/referentiels/types-activite/prompt',
  role: 'Le prompt qui GÉNÈRE ce que le professeur reçoit quand il choisit ce type. C’est lui qui travaille, à chaque clic.',
  repere: '{texte}',
  repli: 'Vide : ce type n’est pas générable — le professeur le voit dans son menu et n’obtient rien. '
    + 'Repères disponibles en plus : {referentiel}, {niveau}, {nb}, {sous_type}, {langue}.',
}

// Titre d'un groupe de liens, cliquable pour le replier. Le chevron est la SEULE marque : pas de
// bouton en plus, pas de libellé « Réduire » — le titre lui-même est la commande.
function TitreGroupe({ titre, reduit, onBasculer, marge }) {
  return (
    <button
      type="button"
      onClick={onBasculer}
      title={reduit ? `Développer « ${titre} »` : `Réduire « ${titre} »`}
      style={{
        display: 'flex', alignItems: 'center', gap: 6, width: '100%', textAlign: 'left',
        background: 'none', border: 'none', padding: '2px 0', cursor: 'pointer',
        marginTop: marge ? 6 : 0,
        fontSize: 11, fontWeight: 700, color: '#94a3b8',
        textTransform: 'uppercase', letterSpacing: 0.4,
      }}>
      <span aria-hidden="true" style={{ fontSize: 9, lineHeight: 1, color: '#cbd5e1' }}>
        {reduit ? '▶' : '▼'}
      </span>
      {titre}
    </button>
  )
}

export default function AdminPromptsReferentiels() {
  const [refs, setRefs] = useState([])          // [{ id, cycle, niveau, meta, lecture, meta_decoupe, decoupe, ...valide }]
  const [refId, setRefId] = useState(0)         // 0 = rien de choisi (on ne présélectionne pas)
  const [typesRef, setTypesRef] = useState([])  // types du niveau choisi : [{ id, label, prompt, validee }]
  const [champ, setChamp] = useState('')        // '' = tous les liens ; sinon la clé d'un CHAMPS, ou `type:<id>`
  const [texte, setTexte] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [panne, setPanne] = useState(false)
  const [detailCache, setDetailCache] = useState(false)
  // Groupes repliés, par titre. Cinq groupes et jusqu'à douze types font une colonne trop longue
  // pour être lue d'un coup d'œil ; un chevron par titre laisse ouvrir ce sur quoi on travaille.
  // Vide = tout ouvert : on ne cache rien à quelqu'un qui arrive sur l'écran.
  const [groupesReduits, setGroupesReduits] = useState({})
  const basculerGroupe = (g) => setGroupesReduits(p => ({ ...p, [g]: !p[g] }))

  // Lecture en base : la liste ET les textes en un seul appel (pas de N+1). Aucun setState avant
  // le fetch — `chargement` vaut déjà true au premier rendu.
  function charger() {
    fetchWithTimeout('/api/admin/referentiels/prompts-matieres', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`Erreur ${r.status}`))))
      .then(d => { setRefs(d.referentiels || []); setPanne(false) })
      .catch(() => setPanne(true))
      .finally(() => setChargement(false))
  }
  // « Réessayer » : là seulement l'écran doit REPASSER en lecture — il n'y est plus.
  function relire() {
    setChargement(true)
    charger()
  }
  useEffect(() => { charger() }, [])

  const refCourant = refs.find(r => r.id === refId) || null

  // Les types du niveau choisi, avec leur prompt de génération. Lecture à part : le GET global de
  // la liste rend les colonnes de `referentiels`, pas les lignes d'une autre table.
  useEffect(() => {
    const r = refs.find(x => x.id === refId)
    if (!r) return
    let annule = false
    fetchWithTimeout(
      `/api/admin/referentiels/types-activite?cycle_id=${r.cycle_id}&niveau=${encodeURIComponent(r.niveau)}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(x => (x.ok ? x.json() : null))
      .then(d => { if (!annule) setTypesRef((d && d.types) || []) })
      .catch(() => { if (!annule) setTypesRef([]) })
    return () => { annule = true }
  }, [refId, refs])

  // `typesRef` garde ce que le dernier chargement a rendu ; ce qu'on MONTRE se derive du
  // referentiel courant. Sans cette derivation, il faudrait vider l'etat dans l'effet — un
  // setState synchrone qui relance un rendu pour rien.
  const typesVus = refCourant ? typesRef : []

  // Le lien ouvert. Un type se reconnaît à sa clé `type:<id>` : son descripteur est construit à la
  // volée (titre et colonne portent l'id de LA ligne écrite), le reste vient de CHAMP_TYPE.
  const typeCourant = champ.startsWith('type:')
    ? typesVus.find(t => String(t.id) === champ.slice(5)) || null
    : null
  const champCourant = typeCourant
    ? { ...CHAMP_TYPE, cle: champ, typeId: typeCourant.id,
        titre: typeCourant.label,
        colonne: `types_activite.prompt — ligne id ${typeCourant.id}` }
    : (CHAMPS.find(c => c.cle === champ) || null)

  // Ouvrir un lien = repartir de ce qui est EN BASE. Un brouillon d'un autre niveau ne traîne pas.
  function ouvrirChamp(cle) {
    setChamp(cle)
    if (cle.startsWith('type:')) {
      const t = typesVus.find(x => String(x.id) === cle.slice(5))
      setTexte(t ? (t.prompt || '') : '')
    } else {
      setTexte(refCourant ? (refCourant[cle] || '') : '')
    }
    setMessage(null)
  }

  function choisirRef(id) {
    setRefId(id)
    setChamp('')
    setTexte('')
    setMessage(null)
    setDetailCache(false)   // choisir un niveau veut dire « montre-moi le détail »
  }

  // Enregistrement — AUCUNE IA. Le serveur refuse un texte à qui il manque son repère.
  async function enregistrer() {
    if (!refCourant || !champCourant) return
    setSaving(true)
    setMessage(null)
    try {
      // Le prompt d'un TYPE part sur sa propre route (PUT, avec `type_id`) : il écrit une ligne de
      // `types_activite`, pas une colonne de `referentiels`. C'est la route du ✎ Prompt de l'écran
      // Référentiels — donc les mêmes contrôles serveur, pas un second chemin d'écriture.
      if (champCourant.typeId) {
        const r = await fetchWithTimeout(champCourant.route, {
          method: 'PUT', credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cycle_id: refCourant.cycle_id, niveau: refCourant.niveau,
                                 type_id: champCourant.typeId, prompt: texte }),
        }, TIMEOUT_STD)
        const d = await r.json().catch(() => ({}))
        if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
        const propre = texte.trim()
        setTypesRef(prev => prev.map(t => (t.id === champCourant.typeId ? { ...t, prompt: propre } : t)))
        setMessage({ ok: true, texte: `Enregistré — ${propre.length} caractères.` })
        return
      }
      const r = await fetchWithTimeout(champCourant.route, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: refCourant.cycle_id, niveau: refCourant.niveau, prompt: texte }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      // On remet à jour la ligne en mémoire avec ce qui vient d'être écrit : pas de relecture
      // complète, et surtout pas de texte affiché qui différerait de la base.
      const propre = texte.trim()
      setRefs(prev => prev.map(x => (x.id === refCourant.id
        ? { ...x, [champCourant.cle]: propre,
            lecture_valide: champCourant.cle === 'lecture' ? !!propre : x.lecture_valide,
            decoupe_relue: champCourant.cle === 'decoupe' ? !!propre : x.decoupe_relue,
            types_relu: champCourant.cle === 'types' ? !!propre : x.types_relu,
            precisions_relu: champCourant.cle === 'precisions' ? !!propre : x.precisions_relu }
        : x)))
      setMessage({ ok: true, texte: propre ? `Enregistré — ${propre.length} caractères.` : 'Champ vidé.' })
    } catch (e) {
      showError(`Enregistrement impossible.\n\n${e.message}`, { danger: true })
    } finally {
      setSaving(false)
    }
  }

  const pastille = (rempli) => ({
    fontSize: 11, fontWeight: 700, color: rempli ? '#166534' : '#94a3b8',
  })

  const colonneListe = (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {chargement ? (
        <p className="text-sm text-gray-500" style={{ padding: '1.25rem 1.5rem' }}>Lecture en cours…</p>
      ) : panne ? (
        <div style={{ padding: '1.25rem 1.5rem' }}>
          <p className="text-sm text-gray-600">La liste n’a pas pu être lue.</p>
          <button type="button" onClick={relire} className="btn-secondary" style={{ marginTop: 8, fontSize: 12 }}>
            Réessayer
          </button>
        </div>
      ) : refs.length === 0 ? (
        <p className="text-sm text-gray-500" style={{ padding: '1.25rem 1.5rem', lineHeight: 1.6 }}>
          Aucun référentiel en base. Déposez d’abord un document sur l’écran <b>Référentiel</b> :
          les prompts se rangent sur la ligne du niveau, elle doit exister d’abord.
        </p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            {refs.map(r => {
              const actif = r.id === refId
              return (
                <tr key={r.id}
                  onClick={() => choisirRef(r.id)}
                  style={{
                    cursor: 'pointer', borderBottom: '1px solid #f1f5f9',
                    background: actif ? '#eff6ff' : 'white',
                  }}>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontSize: 13, fontWeight: actif ? 700 : 600, color: '#1e293b' }}>
                      {r.niveau}
                    </div>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{r.cycle}</div>
                  </td>
                  {/* Une ligne par couple : on voit d'un coup d'œil ce qui manque à ce niveau,
                      et de quel côté — les matières ou la découpe. */}
                  <td style={{ padding: '10px 14px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div style={{ fontSize: 11, color: '#94a3b8' }}>
                      matières{' '}
                      <span style={pastille(!!(r.meta || '').trim())}>
                        {(r.meta || '').trim() ? '● méta' : '○ méta'}
                      </span>{' '}
                      <span style={pastille(!!(r.lecture || '').trim())}>
                        {(r.lecture || '').trim() ? '● lecture' : '○ lecture'}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                      découpe{' '}
                      <span style={pastille(!!(r.meta_decoupe || '').trim())}>
                        {(r.meta_decoupe || '').trim() ? '● méta' : '○ méta'}
                      </span>{' '}
                      <span style={pastille(!!(r.decoupe || '').trim())}>
                        {(r.decoupe || '').trim() ? '● prompt' : '○ prompt'}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                      types{' '}
                      <span style={pastille(!!(r.meta_types || '').trim())}>
                        {(r.meta_types || '').trim() ? '● méta' : '○ méta'}
                      </span>{' '}
                      <span style={pastille(!!(r.types || '').trim())}>
                        {(r.types || '').trim() ? '● prompt' : '○ prompt'}
                      </span>
                    </div>
                    {/* Le neuvième prompt, compté et non deviné : combien de types de ce niveau
                        portent leur prompt de génération. Placé ICI, entre les types et leurs
                        précisions : on lit les types, on écrit ce que chacun génère, puis on
                        détaille ses précisions — c'est l'ordre du travail réel. */}
                    <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                      génération{' '}
                      <span style={pastille(r.nb_types > 0 && r.nb_types_prompt === r.nb_types)}>
                        {r.nb_types
                          ? `${r.nb_types_prompt === r.nb_types ? '●' : '○'} ${r.nb_types_prompt}/${r.nb_types} prompts`
                          : '○ aucun type'}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>
                      précisions{' '}
                      <span style={pastille(!!(r.meta_precisions || '').trim())}>
                        {(r.meta_precisions || '').trim() ? '● méta' : '○ méta'}
                      </span>{' '}
                      <span style={pastille(!!(r.precisions || '').trim())}>
                        {(r.precisions || '').trim() ? '● prompt' : '○ prompt'}
                      </span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )

  // Le NEUVIÈME prompt : un bouton par TYPE du niveau. Rendu comme un groupe à part, mais glissé
  // ENTRE « Types d'activité » et « Précisions » — l'ordre du travail réel : on lit les types, on
  // écrit ce que chacun génère, puis on détaille ses précisions.
  const blocGeneration = !refCourant ? null : (
    <div key="groupe-generation" style={{ display: 'contents' }}>
      <TitreGroupe titre={CHAMP_TYPE.groupe} reduit={!!groupesReduits[CHAMP_TYPE.groupe]}
        onBasculer={() => basculerGroupe(CHAMP_TYPE.groupe)} marge />
      {groupesReduits[CHAMP_TYPE.groupe] ? null : typesVus.length === 0 ? (
        <p className="text-xs text-gray-400" style={{ padding: '4px 2px', lineHeight: 1.6 }}>
          Ce niveau n’a aucun type d’activité. Ils se créent sur l’écran <b>Référentiel</b>,
          cartouche « Types d’activité » — ici on écrit leur prompt, on ne les crée pas.
        </p>
      ) : typesVus.map(t => {
        const rempli = !!(t.prompt || '').trim()
        const cle = `type:${t.id}`
        const ouvert = champ === cle
        return (
          <button
            key={cle}
            type="button"
            onClick={() => ouvrirChamp(cle)}
            title={`${CHAMP_TYPE.role} Repère obligatoire : ${CHAMP_TYPE.repere}.`}
            style={{
              textAlign: 'left', display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 12px', borderRadius: 8, cursor: 'pointer',
              border: `1px solid ${ouvert ? '#bfdbfe' : '#e2e8f0'}`,
              background: ouvert ? '#eff6ff' : '#f8fafc',
            }}>
            <span style={{ fontSize: 12.5, fontWeight: 700, color: ouvert ? '#1d4ed8' : '#334155' }}>
              {t.label}
            </span>
            {!t.validee && (
              <span style={{ fontSize: 11, color: '#b45309' }}>proposé, pas retenu</span>
            )}
            <span style={{ marginLeft: 'auto', fontSize: 11, fontWeight: 700,
              color: rempli ? '#166534' : '#A63045' }}>
              {rempli ? `● ${(t.prompt || '').trim().length} caractères` : '○ vide'}
            </span>
          </button>
        )
      })}
    </div>
  )

  // Détail : d'abord les DEUX LIENS du niveau choisi, puis l'éditeur du lien cliqué.
  const colonneDetail = !refCourant ? (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <p className="text-sm text-gray-500">
        Choisissez un niveau à gauche pour voir ses prompts : matières, découpe, types d’activité et précisions.
      </p>
      <p className="text-xs text-gray-400 mt-2">
        Ils sont rangés sur la ligne du niveau (table <code>referentiels</code>), un jeu par niveau.
        Les écrire ici ne coûte rien : aucun appel à l’IA.
      </p>
    </div>
  ) : (
    <div className="bg-white rounded-lg border border-gray-200 p-6 flex flex-col gap-4"
         style={{ height: '100%', minHeight: 320 }}>
      <div style={{ flexShrink: 0 }}>
        <h3 className="text-sm font-semibold text-gray-700">
          {refCourant.niveau} <span className="text-gray-400 font-normal">— {refCourant.cycle}</span>
        </h3>
        <p className="text-xs text-gray-400 mt-1"
           style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
          referentiels, ligne id {refCourant.id}
        </p>
      </div>

      {/* Les liens, groupés par couple. Toujours affichés : on doit pouvoir passer de l'un à
          l'autre sans revenir en arrière. Celui qui est ouvert est marqué. */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0 }}>
        {CHAMPS.map((c, i) => {
          const rempli = !!(refCourant[c.cle] || '').trim()
          const ouvert = champ === c.cle
          const debutGroupe = i === 0 || CHAMPS[i - 1].groupe !== c.groupe
          // Dernier lien du groupe des précisions : le groupe « Génération » se glisse juste après lui.
          const finDesTypes = c.groupe === 'Précisions (plusieurs précisions par type)'
            && (i === CHAMPS.length - 1 || CHAMPS[i + 1].groupe !== c.groupe)
          return (
            <div key={`g-${c.cle}`} style={{ display: 'contents' }}>
            {debutGroupe && (
              <TitreGroupe titre={c.groupe} reduit={!!groupesReduits[c.groupe]}
                onBasculer={() => basculerGroupe(c.groupe)} marge={!!i} />
            )}
            {!groupesReduits[c.groupe] && (
            <button
              type="button"
              onClick={() => ouvrirChamp(c.cle)}
              title={`${c.role} Repère obligatoire : ${c.repere}.`}
              style={{
                textAlign: 'left', display: 'flex', alignItems: 'center', gap: 10,
                padding: '9px 12px', borderRadius: 8, cursor: 'pointer',
                border: `1px solid ${ouvert ? '#bfdbfe' : '#e2e8f0'}`,
                background: ouvert ? '#eff6ff' : '#f8fafc',
              }}>
              <span style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                fontSize: 12.5, fontWeight: 700, color: ouvert ? '#1d4ed8' : '#334155' }}>
                {c.titre}
              </span>
              <span style={{ fontSize: 11, color: '#94a3b8' }}>
                repère{c.repere2 ? 's' : ''} {c.repere}{c.repere2 ? ` + ${c.repere2}` : ''}
              </span>
              <span style={{ marginLeft: 'auto', fontSize: 11, fontWeight: 700,
                color: rempli ? '#166534' : '#A63045' }}>
                {rempli ? `● ${(refCourant[c.cle] || '').trim().length} caractères` : '○ vide'}
              </span>
            </button>
            )}
            {finDesTypes && blocGeneration}
            </div>
          )
        })}
      </div>

    </div>
  )


  // L'éditeur, en fenêtre flottante ET MODALE. Déplaçable pour ne pas perdre de vue la ligne sur
  // laquelle on travaille ; modale parce qu'un texte en cours de saisie ne doit pas pouvoir être
  // écrasé par un clic derrière : cliquer un autre lien remplacerait le brouillon sans un mot.
  // Le voile ne ferme rien au clic — perdre un prompt collé parce qu'on a visé à côté serait pire
  // que tout. On sort par Annuler ou par le × de la barre de titre.
  const fenetreEditeur = (!refCourant || !champCourant) ? null : (
    <>
    <div
      onMouseDown={e => e.stopPropagation()}
      title="Terminez ou annulez la modification en cours"
      style={{ position: 'fixed', inset: 0, zIndex: 599, background: 'rgba(15,23,42,0.45)',
        cursor: 'not-allowed' }} />
    <FenetrePro
      titre={`${refCourant.niveau} — ${champCourant.titre}`}
      onFermer={() => { setChamp(''); setTexte(''); setMessage(null) }}
      largeur={720}
      hauteur="min(78vh, 720px)"
      minWidth={420}
      minHeight={320}
      zIndex={600}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 14,
        height: '100%', minHeight: 0, boxSizing: 'border-box' }}>
          <div style={{ flexShrink: 0 }}>
            <p className="text-xs text-gray-500" style={{ lineHeight: 1.6 }}>
              {champCourant.role}
            </p>
            <p className="text-xs text-gray-400 mt-1" style={{ lineHeight: 1.6 }}>
              {champCourant.repli} Colonne : <code>{champCourant.colonne}</code>.
            </p>
          </div>
          <textarea
            value={texte}
            onChange={e => { setTexte(e.target.value); setMessage(null) }}
            spellCheck={false}
            placeholder={`Collez ici le texte. ${champCourant.repere2
              ? `Les repères ${champCourant.repere} et ${champCourant.repere2} sont obligatoires.`
              : `Le repère ${champCourant.repere} est obligatoire.`}`}
            style={{
              flex: 1, minHeight: 200, width: '100%', boxSizing: 'border-box', resize: 'none',
              padding: 12, fontSize: 12, lineHeight: 1.5, color: '#334155',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
              background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
            }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, flexWrap: 'wrap' }}>
            {/* Le champ des précisions exige DEUX repères : on les contrôle tous les deux, sinon
                l'écran annonce « présent » sur un texte que le serveur refusera. */}
            {[champCourant.repere, champCourant.repere2].filter(Boolean).map(rep => (
              <span key={rep} style={{ fontSize: 11.5, fontWeight: 600,
                color: texte.includes(rep) ? '#166534' : '#A63045' }}>
                {texte.includes(rep) ? `${rep} présent` : `${rep} manquant — le texte sera refusé`}
              </span>
            ))}
            {message && (
              <span style={{ fontSize: 11.5, color: '#166534' }}>{message.texte}</span>
            )}
            <button
              type="button"
              onClick={() => { setChamp(''); setTexte(''); setMessage(null) }}
              disabled={saving}
              title="Fermer sans enregistrer : ce qui est en base ne bouge pas"
              style={{
                marginLeft: 'auto', height: 36, padding: '0 16px', borderRadius: 8, border: 'none',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                background: saving ? '#e2e8f0' : '#A63045', color: saving ? '#94a3b8' : 'white',
                fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer',
              }}>
              <span aria-hidden="true">✕</span> Annuler
            </button>
            <button
              type="button"
              onClick={enregistrer}
              disabled={saving}
              title="Écrire ce texte sur la ligne de ce niveau (gratuit, aucune IA)"
              style={{
                height: 36, padding: '0 16px', borderRadius: 8, border: 'none',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                background: saving ? '#e2e8f0' : '#1F6EEB', color: saving ? '#94a3b8' : 'white',
                fontSize: 13, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer',
              }}>
              <span aria-hidden="true">✓</span> {saving ? 'Enregistrement…' : 'Enregistrer le prompt'}
            </button>
          </div>
      </div>
    </FenetrePro>
    </>
  )

  return (
    <div className="flex flex-col gap-3" style={{ height: '100%' }}>
      {fenetreEditeur}
      <OngletsPrompts />
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Prompts — Référentiels</h2>
          <p className="text-xs text-gray-400" style={{ maxWidth: 760, lineHeight: 1.5 }}>
            Les prompts de chaque niveau — matières, découpe, types d’activité et précisions —, écrits à la main. Ils vivent sur la
            ligne du niveau (table <code>referentiels</code>), jamais sur le cycle : deux diplômes d’une
            même famille ne se lisent pas avec les mêmes repères. Rien ici n’appelle l’IA.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDetailCache(c => !c)}
          title={detailCache
            ? 'Réafficher la colonne de détail à droite'
            : 'Cacher la colonne de détail — la liste prend toute la largeur'}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, flexShrink: 0,
            background: 'white', color: '#6b7280', border: '1px solid #e5e7eb',
            borderRadius: 7, padding: '7px 14px', fontSize: 12, fontWeight: 500, cursor: 'pointer',
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {detailCache
              ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
              : <><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>}
          </svg>
          {detailCache ? 'Afficher le détail' : 'Cacher le détail'}
        </button>
      </div>

      <div className="admin-prompts-corps">
        {detailCache
          ? <div className="split-pane"><div className="split-col split-col-flex">{colonneListe}</div></div>
          : <SplitPane
              storageKey="admin-prompts-referentiels-split-v1"
              defautGauche={38}
              gauche={colonneListe}
              droite={colonneDetail}
            />}
      </div>
    </div>
  )
}
