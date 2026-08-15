import { useEffect, useState } from 'react'
import { useActionsEcran } from '../components/actionsEcran.jsx'
import { fetchWithTimeout, TIMEOUT_STD, MSG_TIMEOUT } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import InfoGuide from '../components/InfoGuide.jsx'

// IA › Fournisseurs & modèles — LE CATALOGUE, en liste + détail.
//
// Motif maison : la colonne de gauche liste les noms, le clic ouvre le détail à droite, et les
// modèles du fournisseur suivent dans ce même détail. Un tableau large obligeait à défiler
// horizontalement pour lire une ligne — on ne lit pas un catalogue en balayant de droite à gauche.
//
// Frontière avec l'écran Génération : ICI on gère ce qui est raccordé, LÀ-BAS on choisit dedans
// celui qui travaille.
//
// LA CLÉ N'EST PAS ICI. On saisit le NOM de sa variable d'environnement ; sa valeur reste dans le
// .env du serveur, et l'écran ne sait dire qu'une chose : présente ou absente. Un secret qui passe
// par un formulaire finit dans un journal.

const nombre = v => (v || v === 0 ? Number(v).toLocaleString('fr-FR') : '—')

// Boutons — norme maison : une icône, une bulle d'aide, la même hauteur, et le curseur « interdit »
// quand l'action est impossible. Le bleu valide, le rouge annule ou détruit, le vert ajoute.
const BTN = {
  display: 'inline-flex', alignItems: 'center', gap: 6, height: 30, padding: '0 12px',
  borderRadius: 7, fontSize: 12, fontWeight: 600, border: '1px solid transparent',
  cursor: 'pointer', whiteSpace: 'nowrap',
}
const BTN_VALIDER  = { ...BTN, background: '#2563eb', color: '#fff' }
const BTN_ANNULER  = { ...BTN, background: '#fef2f2', color: '#b91c1c', borderColor: '#fecaca' }
const BTN_AJOUTER  = { ...BTN, background: '#059669', color: '#fff' }
const BTN_NEUTRE   = { ...BTN, background: '#fff', color: '#374151', borderColor: '#d1d5db' }
const BTN_DETRUIRE = { ...BTN, background: '#fff', color: '#b91c1c', borderColor: '#fecaca' }
const grise = style => ({ ...style, opacity: 0.45, cursor: 'not-allowed' })

const IcoPlus    = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
const IcoRelever = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/></svg>
const IcoCrayon  = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>
const IcoPoubelle= () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>
const IcoCheck   = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
const IcoCroix   = () => <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>

function Pastille({ ok, oui, non }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600,
      padding: '2px 8px', borderRadius: 99,
      background: ok ? '#ecfdf5' : '#fef2f2', color: ok ? '#047857' : '#b91c1c',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: 99, background: ok ? '#10b981' : '#ef4444' }} />
      {ok ? oui : non}
    </span>
  )
}

function Champ({ nom, aide, children }) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: '1px solid #f3f4f6' }}>
      <span title={aide} style={{ width: 200, flexShrink: 0, fontSize: 12, color: '#6b7280' }}>{nom}</span>
      <span style={{ fontSize: 12, color: '#374151', wordBreak: 'break-all' }}>{children}</span>
    </div>
  )
}

// Champ de saisie du formulaire — même gabarit que Champ, pour que lecture et édition se
// superposent : l'œil retrouve chaque valeur à la place où il l'a lue.
function Saisie({ nom, aide, valeur, onChange, type = 'text', placeholder, options, fige }) {
  const style = { fontSize: 12, padding: '5px 8px', border: '1px solid #d1d5db', borderRadius: 6, width: '100%', maxWidth: 340 }
  return (
    <div style={{ display: 'flex', gap: 10, padding: '6px 0', borderBottom: '1px solid #f3f4f6', alignItems: 'center' }}>
      <label title={aide} style={{ width: 200, flexShrink: 0, fontSize: 12, color: '#6b7280' }}>{nom}</label>
      <div style={{ flex: 1 }}>
        {type === 'case' ? (
          <input type="checkbox" checked={!!valeur} onChange={e => onChange(e.target.checked)} style={{ cursor: 'pointer' }} />
        ) : options ? (
          <select value={valeur || ''} onChange={e => onChange(e.target.value)} style={{ ...style, cursor: 'pointer' }}>
            {options.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
        ) : (
          <input
            type={type} value={valeur ?? ''} placeholder={placeholder} disabled={fige}
            onChange={e => onChange(type === 'number' ? (e.target.value === '' ? null : Number(e.target.value)) : e.target.value)}
            style={{ ...style, background: fige ? '#f9fafb' : '#fff', color: fige ? '#9ca3af' : '#111827' }}
          />
        )}
      </div>
    </div>
  )
}

// Les deux zones de la liste, et les deux seules valeurs que le serveur accepte.
const TARIFICATIONS = ['gratuit', 'payant']
// Les tris offerts sur la zone des payants. AFFICHAGE SEULEMENT : aucun ne touche l'ordre
// d'appel, qui reste celui du catalogue. La liste est faite pour s'allonger — un critère de
// plus, c'est une ligne de plus ici et une comparaison de plus dans `TRIS`.
const TRIS = [
  { cle: 'qualite', libelle: 'qualité',
    aide: "L'ordre décidé par l'administrateur dans le catalogue — c'est celui de l'appel. La qualité n'est mesurée nulle part : ce classement est un jugement, pas un calcul." },
  { cle: 'tarif', libelle: 'tarif',
    aide: 'Du moins cher au plus cher : entrée + sortie du modèle réellement appelé, converti en euros. Ceux dont le tarif n’est pas relevé passent à la fin.' },
]
const FOURNISSEUR_VIDE = { code: '', label: '', type_api: 'openai_compat', base_url: '', cle_env: '', max_tokens: null, actif: true, ordre: 0, tarification: 'payant', lien_tarifs: '' }
const DEVISES = ['USD', 'EUR', 'CHF']
const MODELE_VIDE = { modele: '', label: '', contexte_max: null, max_tokens: null, supporte_schema: true, supporte_stream: true, supporte_temperature: true, recommande: false, actif: true, ordre: 0, cout_entree_million: null, cout_sortie_million: null, devise: 'USD', nom_fournisseur: '' }

export default function AdminIAFournisseurs() {
  const [catalogue, setCatalogue] = useState(null)
  const [choisi, setChoisi]       = useState(null)
  const [erreur, setErreur]       = useState('')
  // Un seul formulaire ouvert à la fois : { quoi: 'fournisseur'|'modele', mode: 'creation'|'edition', valeurs }
  const [form, setForm]           = useState(null)
  const [occupe, setOccupe]       = useState(false)
  // Le compte rendu du dernier relevé de tarifs, affiché tant qu'on ne change pas d'écran.
  const [releve, setReleve]       = useState(null)
  // Le tri de la zone des payants. Il ne vit que le temps de la visite : c'est une façon de
  // REGARDER la liste, pas un réglage de l'application — l'enregistrer ferait croire qu'il
  // change quelque chose au fonctionnement.
  const [tri, setTri]             = useState('qualite')

  function charger(codeAOuvrir) {
    return fetchWithTimeout('/api/admin/ia/catalogue', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('Lecture du catalogue impossible.'))))
      .then(d => {
        setCatalogue(d)
        setChoisi(c => codeAOuvrir || c || d.courant?.fournisseur || d.fournisseurs[0]?.code || null)
      })
      .catch(e => setErreur(e.message === 'timeout' ? MSG_TIMEOUT : e.message))
  }

  useEffect(() => { charger() }, [])

  // Tout passe par ici : une seule façon d'appeler, une seule façon de dire l'échec. Le message
  // du serveur est affiché TEL QUEL — c'est lui qui sait pourquoi il a refusé.
  async function envoyer(url, methode, corps, codeAOuvrir) {
    setOccupe(true)
    try {
      const res = await fetchWithTimeout(url, {
        method: methode, credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: corps ? JSON.stringify(corps) : undefined,
      }, TIMEOUT_STD)
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        showError(d.detail || 'L’enregistrement a échoué.')
        return false
      }
      setForm(null)
      await charger(codeAOuvrir)
      return true
    } catch (e) {
      showError(e.message === 'timeout' ? MSG_TIMEOUT : 'L’enregistrement a échoué.')
      return false
    } finally {
      setOccupe(false)
    }
  }


  // L'ORDRE D'APPEL, tel que le backend le construit : les actifs dont la clé est présente,
  // rangés par `ordre`. Recalculé ici pour l'affichage seul — la vérité reste `liste_fournisseurs`
  // côté serveur ; l'écran ne fait que la montrer.
  const appelables = (catalogue?.fournisseurs || []).filter(f => f.actif && f.cle_configuree)
  const rangDe = f => {
    const i = appelables.findIndex(x => x.code === f.code)
    return i === 0 ? '1er appelé' : `${i + 1}e appelé`
  }
  const fournisseur = catalogue?.fournisseurs.find(f => f.code === choisi) || null
  const modeles     = catalogue?.modeles.filter(m => m.fournisseur === choisi) || []
  // Celui que la boucle appellera chez un fournisseur : son recommandé actif, sinon le premier
  // actif. Même règle qu'en base (`liste_fournisseurs`), pour que l'écran ne montre pas autre
  // chose que ce qui part réellement. Rendu pour N'IMPORTE QUEL fournisseur, parce que le tri par
  // tarif a besoin du prix de CELUI-LÀ — pas du moins cher du catalogue, qui n'est jamais appelé.
  const modeleAppeleDe = code => (catalogue?.modeles || [])
    .filter(m => m.fournisseur === code && m.actif)
    .sort((a, b) => (b.recommande - a.recommande) || (a.ordre - b.ordre))[0] || null
  const modeleAppele = modeleAppeleDe(choisi)?.modele

  // Ce que coûte un fournisseur : entrée + sortie du modèle appelé, en euros. Les deux additionnés
  // parce qu'aucun ne suffit — un modèle à l'entrée bon marché et à la sortie chère coûte cher.
  // Tarif incomplet ou absent : `null`, et la ligne part à la fin plutôt que de passer pour
  // gratuite.
  const coutDe = code => {
    const m = modeleAppeleDe(code)
    if (!m || m.cout_entree_eur == null || m.cout_sortie_eur == null) return null
    return m.cout_entree_eur + m.cout_sortie_eur
  }

  // Les deux zones. `tarification` vient de la base, où l'administrateur l'a mise : rien n'est
  // déduit d'un tarif à zéro, qui voudrait aussi bien dire « pas encore relevé ».
  const tous     = catalogue?.fournisseurs || []
  const gratuits = tous.filter(f => f.tarification === 'gratuit')
  const payants  = tous.filter(f => f.tarification !== 'gratuit')
  // Copie avant tri : `sort` retourne le tableau EN PLACE, et celui-ci vient du catalogue.
  const payantsTries = tri !== 'tarif' ? payants : [...payants].sort((a, b) => {
    const ca = coutDe(a.code), cb = coutDe(b.code)
    if (ca == null && cb == null) return 0
    if (ca == null) return 1
    if (cb == null) return -1
    return ca - cb
  })
  // A-t-il déjà répondu ? C'est ce qui décide si la suppression reste possible.
  const aServi      = !!(fournisseur && fournisseur.appels)

  // Le bouton d'ajout vit dans l'en-tête fixe : il reste sous les yeux quand la liste défile.
  // Tant que le catalogue n'est pas chargé, il n'y a pas de types d'API à proposer au formulaire —
  // d'où le `null` d'attente plutôt qu'un bouton qui ouvrirait une fiche vide.
  useActionsEcran(catalogue ? (
    <button
      onClick={() => setForm({ quoi: 'fournisseur', mode: 'creation', valeurs: { ...FOURNISSEUR_VIDE } })}
      title="Raccorder un nouveau service d’IA à l’application."
      style={BTN_AJOUTER}
    >
      <IcoPlus /> Ajouter un fournisseur
    </button>
  ) : null, [!!catalogue])

  function validerFournisseur() {
    const v = form.valeurs
    if (form.mode === 'creation') return envoyer('/api/admin/ia/fournisseurs', 'POST', v, v.code.trim().toLowerCase())
    return envoyer(`/api/admin/ia/fournisseurs/${encodeURIComponent(v.code)}`, 'PUT', v, v.code)
  }

  function validerModele() {
    const v = { ...form.valeurs, fournisseur: choisi }
    if (form.mode === 'creation') return envoyer('/api/admin/ia/modeles', 'POST', v, choisi)
    return envoyer(`/api/admin/ia/modeles/${encodeURIComponent(choisi)}/${form.origine}`, 'PUT', v, choisi)
  }

  function supprimerFournisseur() {
    if (!confirm(`Supprimer définitivement le fournisseur « ${fournisseur.label} » ?`)) return
    envoyer(`/api/admin/ia/fournisseurs/${encodeURIComponent(fournisseur.code)}`, 'DELETE', null, null)
  }

  // RELEVER LES TARIFS. Le serveur lit la page du fournisseur et remplit le prix de chaque
  // modèle qu'il y retrouve. Le compte rendu dit les DEUX choses : ce qui a été inscrit, et ce
  // qui ne l'a pas été — un modèle absent de la grille n'est pas une panne, mais il faut le
  // savoir, sinon on croit son tarif à jour.
  async function releverTarifs() {
    setOccupe(true)
    try {
      const res = await fetchWithTimeout(
        `/api/admin/ia/fournisseurs/${encodeURIComponent(choisi)}/relever-tarifs`,
        { method: 'POST', credentials: 'include' }, TIMEOUT_STD)
      const d = await res.json().catch(() => ({}))
      if (!res.ok) { showError(d.detail || 'Le relevé a échoué.'); return }
      setReleve(d)
      await charger(choisi)
    } catch (e) {
      showError(e.message === 'timeout' ? MSG_TIMEOUT : 'Le relevé a échoué.')
    } finally {
      setOccupe(false)
    }
  }

  function supprimerModele(m) {
    if (!confirm(`Supprimer définitivement le modèle « ${m.modele} » ?`)) return
    envoyer(`/api/admin/ia/modeles/${encodeURIComponent(choisi)}/${m.modele}`, 'DELETE', null, choisi)
  }

  const maj = (cle, val) => setForm(f => ({ ...f, valeurs: { ...f.valeurs, [cle]: val } }))

  // UNE LIGNE DE LA LISTE. Sortie de la boucle parce qu'il y a maintenant DEUX zones —
  // les gratuits, les payants — et qu'une ligne écrite deux fois finit par diverger : la
  // pastille corrigée d'un côté, oubliée de l'autre.
  function ligne(f) {
    const actif = f.code === choisi
    return (
      <div
        key={f.code}
        onClick={() => { setChoisi(f.code); setForm(null) }}
        title={`Voir le détail de ${f.label}`}
        style={{
          padding: '11px 14px', cursor: 'pointer', borderBottom: '1px solid #f3f4f6',
          borderLeft: actif ? '3px solid #A63045' : '3px solid transparent',
          background: actif ? '#fdf2f4' : 'transparent',
          fontSize: 13, fontWeight: actif ? 600 : 500,
          color: actif ? '#A63045' : '#374151',
        }}
      >
        <div>{f.label}</div>
        {/* CE QUE DIT LA PASTILLE, ET POURQUOI ELLE A CHANGÉ.
            Il n'y a plus UN fournisseur élu et des figurants : il y a une liste, et
            tous ceux qui y sont répondent aux professeurs, dans l'ordre. « EN SERVICE »
            ne voulait donc plus rien dire — la vraie information est la PLACE.

            Et « désactivé » recouvrait deux situations opposées : un fournisseur jamais
            raccordé (il attend une clé) et un fournisseur mis en pause (il attend une
            décision). Affichées pareil, l'admin ne savait pas laquelle il regardait. */}
        <div style={{ marginTop: 3, display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {f.actif && f.cle_configuree && (
            <span style={{ fontSize: 10, fontWeight: 700, color: '#7c3aed' }}
                  title={`${rangDe(f)}. Le premier de la liste est essayé d’abord ; s’il refuse, l’appel passe au suivant sans que le professeur le sache.`}>
              {rangDe(f)}
            </span>
          )}
          {f.actif && !f.cle_configuree && (
            <span style={{ fontSize: 10, fontWeight: 600, color: '#d97706' }}
                  title={`Sa clé « ${f.cle_env || '—'} » n’est pas renseignée sur le serveur : il est activé mais jamais appelé.`}>
              clé manquante
            </span>
          )}
          {!f.actif && (
            <span style={{ fontSize: 10, fontWeight: 600, color: '#9ca3af' }}
                  title={f.appels
                    ? `Mis en pause. Il a déjà répondu à ${f.appels} appel(s) — son historique est conservé, et il reprendra sa place dès qu’on le réactivera.`
                    : 'Raccordé mais jamais appelé : il n’a encore jamais servi.'}>
              {f.appels ? 'en pause' : 'jamais utilisé'}
            </span>
          )}
          {/* LE PRIX, SUR LA LIGNE — sans lui, le tri par tarif est invérifiable : deux ordres
              identiques ne disent pas si le tri a marché ou s'il n'a rien changé. Ce qui est
              montré est ce sur quoi on trie : entrée + sortie du modèle appelé, en euros.
              Non relevé = la ligne part à la fin, et le dit. */}
          {f.tarification !== 'gratuit' && (
            coutDe(f.code) == null ? (
              <span style={{ fontSize: 10, fontWeight: 600, color: '#d97706' }}
                    title="Aucun tarif saisi pour le modèle appelé chez ce fournisseur : il ne peut pas être comparé aux autres, et passe donc en fin de liste.">
                tarif non relevé
              </span>
            ) : (
              <span style={{ fontSize: 10, fontWeight: 600, color: '#6b7280' }}
                    title={`${coutDe(f.code).toFixed(2)} € par million de tokens — entrée + sortie du modèle appelé (${modeleAppeleDe(f.code)?.modele}). C’est ce chiffre qui classe la zone quand le tri est « tarif ».`}>
                {coutDe(f.code).toFixed(2)} € / M
              </span>
            )
          )}
        </div>
      </div>
    )
  }


  return (
    <div className="flex flex-col gap-4">


      {/* Ni titre ni chapô ici : le titre est dans l'en-tête fixe, et le texte qui l'explique est
          son infobulle. Écrire « Fournisseurs » deux fois à trois centimètres d'écart ne dit rien
          de plus et vole la première ligne de l'écran. */}

      {erreur && <p className="text-xs" style={{ color: '#b91c1c' }}>{erreur}</p>}
      {!catalogue && !erreur && <p className="text-xs text-gray-400">Chargement…</p>}

      {catalogue && (
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>

          {/* — Colonne de gauche : les noms, en DEUX ZONES —

              Pourquoi deux zones : « est-ce que ça coûte quelque chose ? » est la première question
              qu'on se pose devant cette liste, et une pastille au milieu des autres ne la voyait
              pas. Le classement vient de la base — l'administrateur l'a dit sur la fiche — et
              JAMAIS d'un tarif à zéro, qui veut aussi bien dire « pas encore relevé ».

              Ce que ces zones NE font PAS : changer l'ordre d'appel. La boucle descend le catalogue
              dans son ordre, gratuits et payants mêlés ; ici on ne fait que regarder. */}
          <div style={{ width: 240, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>

            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827', marginBottom: 5 }}
                  title="Ces fournisseurs ne facturent rien. C'est l'administrateur qui l'a déclaré sur leur fiche.">
                Gratuit
              </h3>
              <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' }}>
                {gratuits.map(ligne)}
              </div>
            </div>

            {payants.length > 0 && (
              <div>
                <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 8, marginBottom: 5 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: '#111827' }}
                      title="Ces fournisseurs facturent leurs appels. C'est l'administrateur qui l'a déclaré sur leur fiche.">
                    Payant
                  </h3>
                  {/* TRIER PUIS APPLIQUER — deux gestes, dans cet ordre.
                      Trier ne change RIEN au fonctionnement : c'est une façon de regarder, pour
                      voir où en sont les fournisseurs avant de décider. « Appliquer » est le
                      moment de la décision : l'ordre affiché devient l'ordre d'appel.
                      Sans le libellé, la combo seule ne disait pas ce qu'elle faisait. */}
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6 }}>
                    <label style={{ display: 'flex', flexDirection: 'column', gap: 2, fontSize: 10, color: '#6b7280' }}>
                      Trier
                      <select
                        value={tri}
                        onChange={e => setTri(e.target.value)}
                        title={TRIS.find(t => t.cle === tri)?.aide}
                        style={{ fontSize: 11, padding: '2px 5px', border: '1px solid #d1d5db',
                                 borderRadius: 6, color: '#374151', background: '#fff', cursor: 'pointer' }}
                      >
                        {TRIS.map(t => <option key={t.cle} value={t.cle}>{t.libelle}</option>)}
                      </select>
                    </label>
                    {/* UN « i », PAS UN BOUTON. Il n'y a rien à valider : l'ordre d'appel suit le
                        tarif tout seul, et l'administrateur est prévenu par courriel quand un prix
                        change. La combo ne fait que REGARDER — par tarif, par qualité — sans jamais
                        rien modifier. */}
                    <InfoGuide
                      titre="Trier"
                      court="Une façon de regarder la liste. Ne change rien à l’ordre d’appel."
                      long={"Ce tri est un CONFORT D’AFFICHAGE : il range la zone « Payant » sous vos yeux, il ne touche à rien." +
                            "\n\nL’ORDRE D’APPEL, lui, se règle tout seul sur le tarif : le fournisseur gratuit d’abord, puis les payants du moins cher au plus cher. Quand un prix change chez un fournisseur, le relevé quotidien l’écrit, le classement suit, et vous recevez un courriel qui vous dit ce qui a bougé. Vous n’avez rien à valider." +
                            "\n\nLa pastille violette sous chaque nom (« 2e appelé ») dit le rang RÉEL, celui que le moteur suit. Elle ne bouge pas quand vous changez de tri : c’est ce qui vous permet de comparer un classement et la réalité." +
                            "\n\n« qualité » affiche l’ordre décidé à la main, celui du catalogue. La qualité d’un modèle ne se mesure nulle part : ce classement-là est un jugement, pas un calcul."}
                    />
                  </div>
                </div>
                <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, overflow: 'hidden' }}>
                  {payantsTries.map(ligne)}
                </div>
              </div>
            )}

          </div>


          {/* — Panneau de droite : détail, puis modèles — */}
          <div style={{ flex: 1, minWidth: 360, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10, padding: '16px 18px' }}>

            {/* Formulaire fournisseur (création ou modification) */}
            {form?.quoi === 'fournisseur' && (
              <>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', marginBottom: 10 }}>
                  {form.mode === 'creation' ? 'Nouveau fournisseur' : `Modifier « ${form.valeurs.label} »`}
                </h3>
                <Saisie nom="code" aide="Identifiant technique : le code utilisé par le moteur. Il ne change plus après création — les modèles et le réglage en service le référencent." valeur={form.valeurs.code} onChange={v => maj('code', v)} fige={form.mode === 'edition'} placeholder="ex. mistral" />
                <Saisie nom="label" aide="Nom affiché : ce que lit l’administrateur dans les listes." valeur={form.valeurs.label} onChange={v => maj('label', v)} placeholder="ex. Mistral AI" />
                <Saisie nom="type_api" aide="Type d’API : détermine quel client l’application construit. Seuls ces types sont compris par le moteur." valeur={form.valeurs.type_api} onChange={v => maj('type_api', v)} options={catalogue.types_api} />
                <Saisie nom="base_url" aide="Adresse d’appel : l’URL de base du service. Laisser vide pour le SDK Anthropic, qui connaît la sienne." valeur={form.valeurs.base_url} onChange={v => maj('base_url', v)} placeholder="https://…" />
                <Saisie nom="cle_env" aide="Variable de la clé : le NOM de la variable d’environnement qui porte la clé — jamais la clé elle-même." valeur={form.valeurs.cle_env} onChange={v => maj('cle_env', v)} placeholder="ex. MISTRAL_API_KEY" />
                <Saisie nom="max_tokens" aide="Réponse maximale, en tokens : ce que ce service accepte d’écrire au plus. Vide = aucun plafond connu." valeur={form.valeurs.max_tokens} onChange={v => maj('max_tokens', v)} type="number" />
                {/* LE SEUL ENDROIT OÙ SE DÉCIDE LA ZONE. Rien ne le devine à partir des tarifs :
                    un prix à zéro peut vouloir dire « offert » comme « pas encore relevé », et un
                    plan gratuit devient payant sans qu'aucun chiffre ne bouge chez nous. */}
                <Saisie nom="lien_tarifs" aide="L’adresse de sa page de tarifs publique. C’est elle que lit le bouton « Relever les tarifs » pour remplir le prix de chaque modèle. Sans elle, les prix se saisissent à la main." valeur={form.valeurs.lien_tarifs} onChange={v => maj('lien_tarifs', v)} placeholder="https://…/tarifs" />
                <Saisie nom="tarification" aide="Gratuit ou payant — c’est VOUS qui le dites, rien ne le déduit. Range le fournisseur dans l’une ou l’autre zone de la liste de gauche ; ne change pas l’ordre d’appel." valeur={form.valeurs.tarification} onChange={v => maj('tarification', v)} options={TARIFICATIONS} />
                <Saisie nom="ordre" aide="Ordre d’appel : sa place dans la liste que le moteur descend. Le plus petit passe en premier." valeur={form.valeurs.ordre} onChange={v => maj('ordre', v)} type="number" />
                <Saisie nom="actif" aide="Décoché, il disparaît du choix du moteur sans être supprimé." valeur={form.valeurs.actif} onChange={v => maj('actif', v)} type="case" />
                <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                  <button onClick={validerFournisseur} disabled={occupe} title="Enregistrer ce fournisseur." style={occupe ? grise(BTN_VALIDER) : BTN_VALIDER}><IcoCheck /> Valider</button>
                  <button onClick={() => setForm(null)} disabled={occupe} title="Abandonner sans enregistrer." style={occupe ? grise(BTN_ANNULER) : BTN_ANNULER}><IcoCroix /> Annuler</button>
                </div>
              </>
            )}

            {/* Détail en lecture */}
            {!form && !fournisseur && <p className="text-xs text-gray-400">Choisissez un fournisseur à gauche.</p>}

            {form?.quoi !== 'fournisseur' && fournisseur && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: '#111827', flex: 1 }}>{fournisseur.label}</h3>
                  <button
                    onClick={() => setForm({ quoi: 'fournisseur', mode: 'edition', valeurs: { ...fournisseur, base_url: fournisseur.base_url || '' } })}
                    title="Modifier les caractéristiques de ce fournisseur."
                    style={BTN_NEUTRE}
                  ><IcoCrayon /> Modifier</button>
                  <button
                    onClick={releverTarifs}
                    disabled={occupe || !fournisseur.lien_tarifs}
                    title={fournisseur.lien_tarifs
                      ? `Lire ${fournisseur.lien_tarifs} et remplir le prix des modèles qu’on y retrouve. Aucune IA n’est appelée : une grille tarifaire se lit.`
                      : 'Impossible : renseignez d’abord « lien_tarifs » sur sa fiche.'}
                    style={(occupe || !fournisseur.lien_tarifs) ? grise(BTN_NEUTRE) : BTN_NEUTRE}
                  ><IcoRelever /> {occupe ? 'Relevé…' : 'Relever les tarifs'}</button>
                  <button
                    onClick={supprimerFournisseur}
                    disabled={aServi || modeles.length > 0}
                    /* CE QUI A SERVI NE SE SUPPRIME PLUS. Les appels passés gardent le CODE du
                       fournisseur, pas son libellé ni ses tarifs : effacer sa ligne rend le
                       journal illisible et les coûts incalculables. Désactiver donne le même
                       résultat visible — plus jamais appelé — sans rien perdre, et se défait. */
                    title={aServi ? `Impossible : ce fournisseur a déjà répondu à ${fournisseur.appels} appel(s). Le supprimer rendrait ces appels illisibles dans le journal. Désactivez-le plutôt : il ne sera plus appelé, et vous pourrez le réactiver.`
                          : modeles.length > 0 ? 'Impossible : supprimez d’abord ses modèles.'
                          : 'Supprimer définitivement ce fournisseur. Possible parce qu’il n’a jamais servi.'}
                    style={(aServi || modeles.length > 0) ? grise(BTN_DETRUIRE) : BTN_DETRUIRE}
                  ><IcoPoubelle /> Supprimer</button>
                </div>

                {releve && (
                  <div style={{ margin: '0 0 10px', padding: '9px 11px', borderRadius: 8, fontSize: 11,
                                background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534' }}>
                    <strong>{releve.releves.length} tarif(s) relevé(s)</strong>
                    {releve.releves.map(r => (
                      <div key={r.modele} style={{ marginTop: 2 }}>
                        {r.modele} : {r.entree} / {r.sortie} {r.devise} par million
                        {!r.change && <span style={{ color: '#65a30d' }}> (inchangé)</span>}
                      </div>
                    ))}
                    {releve.ignores.length > 0 && (
                      <div style={{ marginTop: 6, color: '#92400e' }}>
                        Non trouvés sur la page : {releve.ignores.map(i => i.cherche).join(', ')}.
                        {' '}Renseignez leur « nom_fournisseur » s’ils y figurent sous un autre nom.
                      </div>
                    )}
                    <button onClick={() => setReleve(null)}
                            title="Masquer ce compte rendu."
                            style={{ ...BTN_NEUTRE, height: 22, padding: '0 8px', marginTop: 6 }}>Fermer</button>
                  </div>
                )}
                <Champ nom="code" aide="Identifiant technique : le code utilisé par le moteur et stocké en base."><span style={{ fontFamily: 'monospace' }}>{fournisseur.code}</span></Champ>
                <Champ nom="type_api" aide="Type d’API : détermine quel client l’application construit pour lui parler.">{fournisseur.type_api}</Champ>
                <Champ nom="base_url" aide="Adresse d’appel : l’URL où partent les demandes. {produit} est remplacé par le numéro de produit du compte."><span style={{ fontFamily: 'monospace', fontSize: 11 }}>{fournisseur.base_url || '—'}</span></Champ>
                <Champ nom="cle_env" aide="Variable de la clé : seul le NOM de la variable d’environnement est connu de l’application ; la clé elle-même ne quitte jamais le serveur.">
                  <span style={{ fontFamily: 'monospace', fontSize: 11 }}>{fournisseur.cle_env || '—'}</span>{' '}
                  <Pastille ok={fournisseur.cle_configuree} oui="présente" non="absente" />
                </Champ>
                <Champ nom="max_tokens" aide="Réponse maximale, en tokens : ce que ce fournisseur accepte d’écrire au plus. Ses modèles en héritent, sauf mention contraire.">
                  {nombre(fournisseur.max_tokens)} {fournisseur.max_tokens ? 'tokens' : ''}
                </Champ>
                <Champ nom="lien_tarifs" aide="Sa page de tarifs publique — celle que lit le bouton « Relever les tarifs ».">
                  {fournisseur.lien_tarifs
                    ? <a href={fournisseur.lien_tarifs} target="_blank" rel="noreferrer"
                         style={{ fontSize: 11, color: '#1F6EEB' }}>{fournisseur.lien_tarifs}</a>
                    : <span style={{ color: '#9ca3af' }}>—</span>}
                </Champ>
                <Champ nom="tarification" aide="Gratuit ou payant, tel que l’administrateur l’a déclaré. Décide de la zone dans la liste de gauche, et de rien d’autre.">
                  {fournisseur.tarification}
                </Champ>
                <Champ nom="actif" aide="Un fournisseur désactivé n’apparaît pas dans le choix du moteur.">
                  <Pastille ok={fournisseur.actif} oui="actif" non="désactivé" />
                </Champ>

                {/* — Ses modèles, à la suite du détail — */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '20px 0 8px' }}>
                  <h4 style={{ fontSize: 12, fontWeight: 700, color: '#374151', flex: 1 }}>
                    Modèles
                    <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 600, padding: '1px 8px', borderRadius: 99, background: '#f3f4f6', color: '#6b7280', border: '1px solid #e5e7eb' }}>
                      {modeles.length}
                    </span>
                  </h4>
                  <button
                    onClick={() => setForm({ quoi: 'modele', mode: 'creation', valeurs: { ...MODELE_VIDE } })}
                    title="Offrir un modèle de plus chez ce fournisseur."
                    style={BTN_AJOUTER}
                  ><IcoPlus /> Ajouter un modèle</button>
                </div>

                {/* Formulaire modèle */}
                {form?.quoi === 'modele' && (
                  <div style={{ border: '1px solid #bfdbfe', background: '#eff6ff', borderRadius: 8, padding: '12px 14px', marginBottom: 10 }}>
                    <h5 style={{ fontSize: 12, fontWeight: 700, color: '#1e40af', marginBottom: 6 }}>
                      {form.mode === 'creation' ? 'Nouveau modèle' : `Modifier « ${form.origine} »`}
                    </h5>
                    <Saisie nom="modele" aide="Identifiant API : le nom EXACT attendu par l’API du fournisseur. Une approximation est refusée par lui, pas par nous. Il ne change plus après création." valeur={form.valeurs.modele} onChange={v => maj('modele', v)} fige={form.mode === 'edition'} placeholder="ex. mistral3" />
                    {/* LE MÊME MODÈLE, SON AUTRE NOM. Infomaniak n'accepte que « mistral3 » dans un
                        appel mais publie « mistralai/Ministral-3-14B-Instruct-2512 » dans sa liste et
                        sur sa grille tarifaire. Les deux viennent de lui ; celui-ci sert à LIRE. */}
                    <Saisie nom="nom_fournisseur" aide="Le nom PUBLIC du modèle chez le fournisseur, quand il n’est pas celui qu’on lui envoie. C’est ce nom-là qu’on retrouve sur sa grille tarifaire — sans lui, il faut deviner quelle ligne correspond. Laisser vide si les deux noms sont identiques (Anthropic, Groq)." valeur={form.valeurs.nom_fournisseur} onChange={v => maj('nom_fournisseur', v)} placeholder="ex. mistralai/Ministral-3-14B-Instruct-2512" />
                    <Saisie nom="label" aide="Nom affiché : ce que lit l’administrateur dans le choix du modèle." valeur={form.valeurs.label} onChange={v => maj('label', v)} />
                    <Saisie nom="contexte_max" aide="Fenêtre totale, en tokens : le texte envoyé ET la réponse, ensemble. Au-delà, le fournisseur refuse l’appel." valeur={form.valeurs.contexte_max} onChange={v => maj('contexte_max', v)} type="number" />
                    <Saisie nom="max_tokens" aide="Réponse maximale, en tokens : ce que ce modèle accepte d’écrire au plus. Vide = celle du fournisseur s’applique." valeur={form.valeurs.max_tokens} onChange={v => maj('max_tokens', v)} type="number" />
                    {/* LE PRIX — saisi ici depuis le 15/08/2026.
                        Ces deux colonnes existaient déjà et servaient à l’écran des statistiques,
                        mais aucune route ne les écrivait : seule une migration pouvait les
                        renseigner. Or un tarif change — DeepSeek le 16 août, Anthropic le
                        1er septembre — et attendre un développeur pour saisir deux nombres n’a
                        pas de sens. */}
                    <Saisie nom="cout_entree_million" aide="Prix d’UN MILLION de tokens ENVOYÉS, dans la monnaie du fournisseur, tel qu’il l’affiche sur sa page tarifaire. Vide = pas encore relevé (l’écran le dira plutôt que d’afficher zéro, qui se lirait « gratuit »)." valeur={form.valeurs.cout_entree_million} onChange={v => maj('cout_entree_million', v)} type="number" />
                    <Saisie nom="cout_sortie_million" aide="Prix d’UN MILLION de tokens PRODUITS. Il vaut souvent trois à cinq fois celui de l’entrée : c’est lui qui pèse dans la facture." valeur={form.valeurs.cout_sortie_million} onChange={v => maj('cout_sortie_million', v)} type="number" />
                    <Saisie nom="devise" aide="La monnaie du fournisseur, PAS la nôtre : Infomaniak publie en francs suisses, les autres en dollars. On enregistre tel qu’affiché, l’euro se calcule tout seul au taux du jour (Banque centrale européenne)." valeur={form.valeurs.devise} onChange={v => maj('devise', v)} options={DEVISES} />
                    <Saisie nom="supporte_schema" aide="Sait imposer un format : le modèle peut rendre du JSON contraint. Sans cela, les étapes qui l’exigent échouent." valeur={form.valeurs.supporte_schema} onChange={v => maj('supporte_schema', v)} type="case" />
                    <Saisie nom="supporte_stream" aide="Sait répondre au fil : le modèle accepte le streaming — indispensable aux appels longs." valeur={form.valeurs.supporte_stream} onChange={v => maj('supporte_stream', v)} type="case" />
                    <Saisie nom="supporte_temperature" aide="Accepte le réglage de température. Les Claude Opus 4.x et les modèles 5 la REFUSENT (erreur 400) : décoché, la température réglée dans Génération n'est pas envoyée à ce modèle." valeur={form.valeurs.supporte_temperature} onChange={v => maj('supporte_temperature', v)} type="case" />
                    <Saisie nom="recommande" aide="Le modèle mis en avant chez ce fournisseur. Un seul à la fois : le cocher le retire à l’autre." valeur={form.valeurs.recommande} onChange={v => maj('recommande', v)} type="case" />
                    <Saisie nom="ordre" aide="Ordre d’affichage : position dans la liste des modèles." valeur={form.valeurs.ordre} onChange={v => maj('ordre', v)} type="number" />
                    <Saisie nom="actif" aide="Décoché, il disparaît du choix du modèle sans être supprimé." valeur={form.valeurs.actif} onChange={v => maj('actif', v)} type="case" />
                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                      <button onClick={validerModele} disabled={occupe} title="Enregistrer ce modèle." style={occupe ? grise(BTN_VALIDER) : BTN_VALIDER}><IcoCheck /> Valider</button>
                      <button onClick={() => setForm(null)} disabled={occupe} title="Abandonner sans enregistrer." style={occupe ? grise(BTN_ANNULER) : BTN_ANNULER}><IcoCroix /> Annuler</button>
                    </div>
                  </div>
                )}

                {modeles.length === 0 && !form && (
                  <p className="text-xs text-gray-400">Aucun modèle enregistré pour ce fournisseur.</p>
                )}

                {modeles.map(m => {
                  // LE MODÈLE APPELÉ CHEZ CE FOURNISSEUR — son recommandé, ou le premier actif à
                  // défaut. Il n'y a plus de « modèle en service » global : `mistral3` ne veut
                  // rien dire chez Anthropic, chaque fournisseur appelle le sien.
                  const modeleEnService = m.actif && m.modele === modeleAppele
                  return (
                    <div key={m.modele} style={{
                      border: '1px solid', borderColor: modeleEnService ? '#ddd6fe' : '#e5e7eb',
                      borderRadius: 8, padding: '10px 12px', marginBottom: 8,
                      background: modeleEnService ? '#f5f3ff' : '#fafafa',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 700, color: '#111827' }}>{m.modele}</span>
                        {m.nom_fournisseur && (
                          <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#9ca3af' }}
                                title={`Son nom PUBLIC chez le fournisseur : c’est sous celui-là qu’il figure dans sa liste et sur sa grille tarifaire. L’appel, lui, part avec « ${m.modele} ».`}>
                            = {m.nom_fournisseur}
                          </span>
                        )}
                        <span style={{ fontSize: 12, color: '#6b7280' }}>{m.label}</span>
                        {m.recommande && <span style={{ fontSize: 10, fontWeight: 600, color: '#6b7280' }}>(recommandé)</span>}
                        {modeleEnService && <span style={{ fontSize: 10, fontWeight: 700, color: '#7c3aed' }}
                              title="C’est ce modèle que l’application appelle chez ce fournisseur.">APPELÉ</span>}
                        {!m.actif && <span style={{ fontSize: 10, fontWeight: 600, color: '#9ca3af' }}>désactivé</span>}
                        <span style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                          <button
                            onClick={() => setForm({ quoi: 'modele', mode: 'edition', origine: m.modele, valeurs: { ...m } })}
                            title="Modifier les caractéristiques de ce modèle."
                            style={{ ...BTN_NEUTRE, height: 26, padding: '0 9px' }}
                          ><IcoCrayon /> Modifier</button>
                          <button
                            onClick={() => supprimerModele(m)}
                            disabled={!!m.appels}
                            title={m.appels ? `Impossible : ce modèle a déjà produit ${m.appels} réponse(s). Le supprimer rendrait leur coût incalculable — son tarif disparaîtrait avec lui. Désactivez-le plutôt.`
                                  : 'Supprimer définitivement ce modèle. Possible parce qu’il n’a jamais servi.'}
                            style={{ ...(m.appels ? grise(BTN_DETRUIRE) : BTN_DETRUIRE), height: 26, padding: '0 9px' }}
                          ><IcoPoubelle /> Supprimer</button>
                        </span>
                      </div>
                      <div style={{ marginTop: 6, display: 'flex', gap: 18, flexWrap: 'wrap', fontSize: 11, color: '#6b7280' }}>
                        {/* Mêmes noms que dans le formulaire au-dessus, et que dans la base : un champ,
                            un mot. Le sens en français est dans la bulle d'aide, jamais dans le libellé. */}
                        <span title="Fenêtre totale, en tokens : le texte envoyé ET la réponse, ensemble.">
                          contexte_max : <strong style={{ color: '#374151' }}>{nombre(m.contexte_max)}</strong>
                        </span>
                        <span title="Réponse maximale, en tokens. Vide sur le modèle = celle du fournisseur s’applique.">
                          max_tokens : <strong style={{ color: '#374151' }}>{nombre(m.max_tokens || fournisseur.max_tokens)}</strong>
                        </span>
                        <span title="Sait imposer un format : sait rendre une réponse en JSON contraint.">
                          supporte_schema : <strong style={{ color: '#374151' }}>{m.supporte_schema ? 'oui' : 'non'}</strong>
                        </span>
                        <span title="Accepte le réglage de température. Non = la valeur réglée dans Génération n'est pas envoyée à ce modèle.">
                          supporte_temperature : <strong style={{ color: '#374151' }}>{m.supporte_temperature ? 'oui' : 'non'}</strong>
                        </span>
                        {/* LE PRIX, DANS LES DEUX MONNAIES.
                            Celle du fournisseur d'abord — c'est elle qu'on retrouve sur sa page
                            tarifaire, donc la seule qui permette de vérifier une saisie. L'euro
                            ensuite, entre parenthèses, parce que c'est la seule façon de comparer
                            deux fournisseurs qui n'annoncent pas dans la même monnaie : 0,30 CHF
                            et 0,30 USD ne sont pas le même prix.

                            « non relevé » plutôt qu'un tiret ou un zéro : un zéro se lirait
                            « gratuit », et un tiret ne dirait pas s'il manque ou s'il vaut zéro. */}
                        <span title="Prix d’un million de tokens ENVOYÉS, dans la monnaie du fournisseur. Entre parenthèses, le même montant en euros au taux du jour (Banque centrale européenne).">
                          entrée / M : <strong style={{ color: m.cout_entree_million == null ? '#d97706' : '#374151' }}>
                            {m.cout_entree_million == null ? 'non relevé'
                              : `${m.cout_entree_million} ${m.devise}`}
                          </strong>
                          {m.cout_entree_eur != null && m.devise !== 'EUR' && (
                            <span style={{ color: '#9ca3af' }}> ({m.cout_entree_eur} €)</span>
                          )}
                        </span>
                        <span title="Prix d’un million de tokens PRODUITS. Il vaut souvent trois à cinq fois celui de l’entrée : c’est lui qui pèse dans la facture.">
                          sortie / M : <strong style={{ color: m.cout_sortie_million == null ? '#d97706' : '#374151' }}>
                            {m.cout_sortie_million == null ? 'non relevé'
                              : `${m.cout_sortie_million} ${m.devise}`}
                          </strong>
                          {m.cout_sortie_eur != null && m.devise !== 'EUR' && (
                            <span style={{ color: '#9ca3af' }}> ({m.cout_sortie_eur} €)</span>
                          )}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
