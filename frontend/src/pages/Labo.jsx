// ── LABO — Ajout d'un référentiel · ÉTAPE 1 : fournir le document ─────────────────────────
// Bac à sable : on met la procédure au point isolément, avec les VRAIS appels sur la base
// réelle (aucune maquette, aucune donnée en dur), avant de l'intégrer dans Admin → Référentiels.
//
// L'ÉCRAN EST CELUI QUE L'ADMIN CONNAÎT. Disposition, onglets, libellés, styles : tout est
// recopié de pages/AdminReferentiels.jsx (colonne des catalogues + carte « Document PDF »).
// Ce qui est neuf dans ce chantier, c'est la plomberie et l'enchaînement des étapes — pas
// l'écran. Rien n'est redessiné, rien n'est « amélioré » au passage.
//
// LE BACK DU LABO EST À LUI. Toutes les routes de cet écran sont sous /api/admin/labo/… et
// vivent dans backend/pedagogie/referentiels_labo.py. L'ancien back (referentiels_admin.py)
// n'est plus appelé d'ici : ce qu'on corrige au labo ne doit rien changer à l'écran existant.
//
// LE COUPLE D'ABORD, LE PDF ENSUITE. L'admin choisit cycle · niveau (cascade recopiée de l'écran
// existant, lue par get /admin/programmes — l'arbre complet des programmes), puis dépose
// le document : il sait ce qu'il dépose. Plus de détection du couple par l'IA, et plus de zone
// d'attente — la place du fichier est connue d'entrée, il y va tout de suite et sa fiche naît
// avec lui. Deux portes, une à la fois (onglets), qui rendent la même chose :
//   POST /api/admin/labo/referentiels/preparer-depot  — le fichier (multipart : file, cycle_id, niveau_id)
//   POST /api/admin/labo/referentiels/preparer-lien   — le lien ({cycle_id, niveau_id, url})
import { useEffect, useState } from 'react'
import { fetchWithTimeout, TIMEOUT_STD, TIMEOUT_LONG, TIMEOUT_XLONG } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import { demanderConfirmation } from '../confirmDialog.js'
import { Spinner } from '../components/icones.jsx'
import InfoGuide from '../components/InfoGuide.jsx'

// Pastille d'étape — recopiée telle quelle d'AdminReferentiels.jsx, où elle n'est pas exportée.
function Pastille({ etat, titre }) {
  const couleur = { vert: '#16a34a', rouge: '#dc2626', jaune: '#facc15' }[etat] || '#facc15'
  return (
    <span title={titre} style={{ display: 'inline-block', width: 11, height: 11, borderRadius: '50%',
      background: couleur, border: '1px solid rgba(0,0,0,0.12)', flexShrink: 0,
      verticalAlign: 'middle', marginRight: 8 }} />
  )
}

// Frise de progression — LE parcours, à la place du paragraphe qui décrivait l'ancien ordre
// (« fournissez le PDF, puis validez ») et ne correspondait plus à l'écran. Elle dit la même
// chose, mais elle le dit en montrant OÙ ON EN EST : fait ✓ vert, en cours bordeaux, à venir gris.
//
// Inspirée de components/FriseProgression.jsx (écran Créer), pas importée : celle-là prend les
// états de la génération (type, texte, résultat). Ici les états sont LUS de la progression réelle
// du référentiel, jamais recopiés.
//
// UNE ÉTAPE PAR CARTE, ET SEULEMENT CELLES QUI EXISTENT. Les suivantes (matières, découpe) ne
// sont pas encore reconstruites dans le labo : les afficher en gris promettrait un parcours qui
// n'est pas là. Chacune entrera dans cette liste le jour où sa carte entrera dans l'écran.
function Frise({ etapes }) {
  const courant = etapes.findIndex(e => !e.fait)
  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', rowGap: 8 }}>
      {etapes.map((e, i) => {
        const estCourant = i === courant
        const bg   = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#fff'
        const fg   = (e.fait || estCourant) ? '#fff' : '#94a3b8'
        const bord = e.fait ? '#16a34a' : estCourant ? 'var(--bordeaux)' : '#cbd5e1'
        return (
          <span key={e.n} style={{ display: 'flex', alignItems: 'center' }}>
            {i > 0 && (
              <span style={{ width: 30, height: 2, borderRadius: 2, margin: '0 9px',
                             background: etapes[i - 1].fait ? '#16a34a' : '#e2e8f0' }} />
            )}
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }} title={e.aide}>
              <span style={{ width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                             display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                             fontSize: 12, fontWeight: 800, fontVariantNumeric: 'tabular-nums',
                             background: bg, color: fg, border: `1.5px solid ${bord}`,
                             boxShadow: estCourant ? '0 0 0 4px rgba(140,29,64,0.14)' : 'none' }}>
                {e.fait ? '✓' : e.n}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap',
                             color: estCourant ? '#1e293b' : e.fait ? '#64748b' : '#94a3b8' }}>
                {e.label}
              </span>
            </span>
          </span>
        )
      })}
    </div>
  )
}

export default function Labo() {
  const [refsListe, setRefsListe] = useState([])   // colonne 2 : référentiels déposés (GET /liste)
  const [arbre, setArbre] = useState([])           // arbre COMPLET cycles → niveaux (GET /admin/programmes)
  const [cycleId, setCycleId] = useState('')       // LE COUPLE, choisi AVANT le document
  const [niveauId, setNiveauId] = useState('')
  const [niveau, setNiveau] = useState('')         // son nom, pour les routes qui lisent par couple
  const [mode, setMode] = useState('depot')        // 'depot' | 'lien'
  const [url, setUrl] = useState('')
  const [nomFichier, setNomFichier] = useState('') // nom du PDF choisi (zone « Par dépôt »)
  const [busy, setBusy] = useState(false)
  const [apercu, setApercu] = useState(null)       // la réponse du serveur au dépôt qui vient d'aboutir
  const [showPdf, setShowPdf] = useState(false)    // fenêtre de relecture du document du couple
  const [refCourant, setRefCourant] = useState(null)  // la ligne de la colonne actuellement ouverte
  const [supprBusy, setSupprBusy] = useState(false)
  const [blocages, setBlocages] = useState({ bloques: 0, a_informer: 0, profs: [] })
  // Le panneau de déblocage : matières attendues × matières du nouveau référentiel, et le choix
  // de l'admin pour chacune. null = panneau fermé.
  const [corresp, setCorresp] = useState(null)
  // Aide « Trouver le lien » : branchée seulement si le serveur a sa clé (get /recherche-dispo).
  // `pistes` = null tant qu'on n'a rien cherché, [] si la recherche n'a rien rendu.
  const [rechDispo, setRechDispo] = useState(false)
  const [pistes, setPistes] = useState(null)
  const [rechBusy, setRechBusy] = useState(false)
  // CE QU'ON VA DEMANDER AU MOTEUR, ÉCRIT NOIR SUR BLANC. L'admin le lit et le corrige AVANT de
  // chercher — c'est son texte qui part, pas une phrase fabriquée dans son dos. Il se repropose
  // (cycle + niveau) à chaque changement de couple, jamais par-dessus une saisie en cours.
  const [saisieQuestion, setSaisieQuestion] = useState(null)   // { couple, texte } — voir plus bas
  // La piste qu'on REGARDE avant de la choisir (fenêtre de relecture). Le PDF est lu là où il
  // est, chez l'Éducation nationale : rien n'est téléchargé chez nous, rien n'est déposé.
  const [apercuLien, setApercuLien] = useState(null)
  // Les DOCUMENTS du couple — les morceaux déposés, avant la fusion. Lus en base (GET /documents),
  // jamais devinés du disque. `docsInfo` porte les totaux et les plafonds, calculés par le serveur.
  const [docs, setDocs] = useState([])
  const [docsInfo, setDocsInfo] = useState(null)
  const [docsBusy, setDocsBusy] = useState(false)
  const [voirDoc, setVoirDoc] = useState(null)     // le morceau qu'on relit avant la fusion

  // La liste des référentiels déposés, lue EN BASE (GET /liste). Aucune donnée recopiée.
  // Déclarée AVANT l'effet qui l'appelle (eslint react-hooks refuse l'ordre inverse).
  function chargerListe() {
    fetchWithTimeout('/api/admin/labo/referentiels/liste', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setRefsListe(d.referentiels || []) })
      .catch(() => {})
  }

  // Arbre COMPLET cycles → niveaux (tous les niveaux, même sans matière) : la source de la
  // cascade « Cycle et niveau ». Lu en base via /admin/programmes (get, zéro copie) — la même
  // source que l'écran existant. Le labo ne crée jamais un cycle ni un niveau : ils se créent à
  // une seule place, l'écran Programmes. Ici, on ne fait que choisir.
  function chargerArbre() {
    fetchWithTimeout('/api/admin/programmes', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setArbre(d.cycles || []) })
      .catch(() => {})
  }

  useEffect(() => {
    chargerListe(); chargerArbre()
    // Le bouton « Trouver le lien » n'existe que si le serveur peut vraiment chercher : sans clé,
    // on ne montre pas une commande qui répondrait par une erreur.
    fetchWithTimeout('/api/admin/labo/referentiels/recherche-dispo', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d) setRechDispo(Boolean(d.disponible)) })
      .catch(() => {})
  }, [])

  // Clic sur une ligne de la colonne : sélectionne le couple. La suite de l'écran (carte Couple,
  // matières, découpe) n'existe pas encore dans le labo — elle viendra étape par étape.
  // Qui est en attente sur ce niveau — lu EN BASE. Rend le bouton de déblocage visible tant
  // qu'il reste des lignes, et permet de relire la liste après coup.
  function chargerBlocages(r) {
    if (!r) { setBlocages({ bloques: 0, a_informer: 0, profs: [] }); return }
    const q = `cycle_id=${Number(r.cycle_id)}&niveau=${encodeURIComponent(r.niveau)}`
    fetchWithTimeout(`/api/admin/labo/referentiels/blocages?${q}`, { credentials: 'include' }, TIMEOUT_STD)
      .then(x => (x.ok ? x.json() : null))
      .then(d => { if (d) setBlocages(d) })
      .catch(() => {})
  }

  // Clic sur une ligne de la colonne. Deux cas, et ils ne s'ouvrent pas pareil : un référentiel
  // EN PLACE ouvre sa fiche ; un couple EN COURS rouvre sa composition, là où elle en était.
  function ouvrirRef(r) {
    setCycleId(String(r.cycle_id)); setNiveauId(String(r.niveau_id)); setNiveau(r.niveau)
    setRefCourant(r.en_cours ? null : r); setApercu(null); oublierPistes()
    setNomFichier(''); setUrl('')
    chargerBlocages(r.en_cours ? null : r)
    chargerDocuments(r.niveau_id)
  }

  // « + Nouveau » : remet l'écran en création — aucun couple choisi, champs de saisie vides,
  // aucun document en cours de composition.
  function nouveau() {
    setCycleId(''); setNiveauId(''); setNiveau(''); setRefCourant(null)
    setBlocages({ bloques: 0, a_informer: 0, profs: [] })
    setApercu(null); setNomFichier(''); setUrl(''); oublierPistes()
    setDocs([]); setDocsInfo(null); setVoirDoc(null)
  }

  // Supprimer POUR DE BON le référentiel du couple ouvert — le geste qu'on fait quand l'Éducation
  // nationale publie une nouvelle version : on ne rafistole pas, on efface et on refait la
  // procédure depuis le début.
  //
  // DEUX boîtes, l'une après l'autre. La première ÉNUMÈRE ce qui part, avec les comptes LUS EN
  // BASE (get supprimer-bilan) — l'admin lit ce qu'il perd, il ne le devine pas. La seconde est le
  // garde-fou : maintenant qu'il a vu la liste, on redemande. C'est seulement là que ça part.
  async function supprimerReferentiel(r) {
    setSupprBusy(true)
    try {
      const q = `cycle_id=${Number(r.cycle_id)}&niveau=${encodeURIComponent(r.niveau)}`
      const rb = await fetchWithTimeout(`/api/admin/labo/referentiels/supprimer-bilan?${q}`,
        { credentials: 'include' }, TIMEOUT_STD)
      const b = await rb.json().catch(() => ({}))
      if (!rb.ok) { showError(b.detail || `Lecture impossible (${rb.status}).`); return }
      if (!b.existe) { showError('Aucun référentiel à supprimer pour ce couple.'); return }

      const lignes = [
        `• ${b.matieres} matière(s)`,
        `• ${b.unites} unité(s) de découpe`,
        `• ${b.types} type(s) d’activité et leurs ${b.precisions} précision(s)`,
        `• le document PDF${b.fichier ? ` « ${b.fichier} »` : ''}${b.pdf ? '' : ' (déjà absent du disque)'}`,
      ].join('\n')
      // Les profs NOMMÉMENT, jamais un nombre : l'admin doit savoir qui il met en attente.
      const qui = (b.profs_liste || []).map(p =>
        `• ${[p.prenom, p.nom].filter(Boolean).join(' ') || '(sans nom)'} — ${p.email}${p.matiere ? ` — ${p.matiere}` : ''}`).join('\n')
      const alerte = b.profs > 0
        ? `\n\n${b.profs} professeur(s) travaillent sur ce référentiel :\n\n${qui}\n\n`
          + 'Ils seront mis en attente : ils ne pourront plus générer sur ce niveau, et ils recevront '
          + 'un message le leur expliquant. Leur matière sera rebranchée quand vous les débloquerez, '
          + 'après la nouvelle procédure.'
        : ''
      // Ce qui PART et ce qui RESTE, tous les deux : une liste de pertes sans son contrepoids
      // laisse croire qu'on efface plus que ça (le couple, les comptes). Chiffres lus en base.
      if (!await demanderConfirmation({
        titre: `Supprimer le référentiel « ${r.cycle} · ${r.niveau} » ?`,
        message: 'Action irréversible.\n\nSeront définitivement supprimés :\n\n'
          + `${lignes}\n\n`
          + 'Ne sont pas touchés : le cycle, le niveau, et les comptes des professeurs.\n\n'
          + 'Les matières et les unités se reconstruisent en refaisant la procédure avec le '
          + `nouveau document.${alerte}`,
        confirmLabel: 'Continuer',
      })) return

      if (!await demanderConfirmation({
        titre: 'Confirmer la suppression',
        message: `Êtes-vous sûr de vouloir supprimer le référentiel « ${r.cycle} · ${r.niveau} » ?`
          + (b.profs > 0 ? `\n\n${b.profs} professeur(s) seront mis en attente au même instant.` : '')
          + '\n\nCette action est définitive.',
        icone: 'interdit',
        confirmLabel: b.profs > 0 ? 'Supprimer et mettre en attente' : 'Supprimer définitivement',
        danger: true,
      })) return

      const rs = await fetchWithTimeout('/api/admin/labo/referentiels/supprimer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        // Le geste ASSUMÉ : c'est ce drapeau, posé seulement après les deux boîtes, qui autorise
        // le serveur à mettre les profs en attente. Sans lui, il refuse comme avant.
        body: JSON.stringify({ cycle_id: Number(r.cycle_id), niveau: r.niveau, bloquer_profs: b.profs > 0 }),
      }, TIMEOUT_LONG)
      const d = await rs.json().catch(() => ({}))
      if (!rs.ok) { showError(d.detail || `Suppression impossible (${rs.status}).`); return }
      nouveau()        // le couple ouvert n'existe plus : l'écran repart en création
      chargerListe()   // et la colonne se relit EN BASE (zéro copie)
      if (d.profs_bloques) {
        await demanderConfirmation({
          titre: 'Référentiel supprimé',
          message: `${d.profs_bloques} professeur(s) sont en attente et ont été prévenus.\n\n`
            + 'Déposez le nouveau document et menez la procédure jusqu’au découpage, puis revenez '
            + 'sur ce couple pour les débloquer.',
          boutonUnique: true, confirmLabel: 'J’ai compris',
        })
      }
    } catch (e) { showError(`Suppression impossible.\n\n${e.message}`) }
    finally { setSupprBusy(false) }
  }

  // Le déblocage — geste EXPLICITE, jamais déclenché par la fin de la découpe : l'admin seul sait
  // si la nouvelle procédure est vraiment en place.
  //
  // UNE MATIÈRE QU'UN PROF UTILISE NE DISPARAÎT PAS, ELLE EST REMPLACÉE. Un programme qui change
  // renomme ou fusionne ses matières ; l'admin DÉSIGNE donc, pour chacune de celles que les profs
  // attendent, celle qui prend sa place. Rien n'est deviné, rien ne se perd en silence. Le panneau
  // ci-dessous n'est pas un dialogue de confirmation : c'est un choix à faire, ligne par ligne.
  function ouvrirDeblocage(r) {
    setSupprBusy(true)
    const q = `cycle_id=${Number(r.cycle_id)}&niveau=${encodeURIComponent(r.niveau)}`
    fetchWithTimeout(`/api/admin/labo/referentiels/correspondances?${q}`,
      { credentials: 'include' }, TIMEOUT_STD)
      .then(async x => {
        const d = await x.json().catch(() => ({}))
        if (!x.ok) { showError(d.detail || `Lecture impossible (${x.status}).`); return }
        if (!d.prete) { showError(d.empechement || 'Déblocage impossible pour l’instant.'); return }
        // Nom identique dans le nouveau document = remplaçante évidente, proposée d'office.
        // Le reste attend une décision : '' tant que l'admin n'a pas choisi.
        const choix = {}
        for (const a of d.attendues) choix[a.nom] = a.propose != null ? String(a.propose) : ''
        setCorresp({ ...d, ref: r, choix })
      })
      .catch(e => showError(`Lecture impossible.\n\n${e.message}`))
      .finally(() => setSupprBusy(false))
  }

  async function confirmerDeblocage() {
    const { ref: r, attendues, choix } = corresp
    const correspondances = {}
    for (const a of attendues) correspondances[a.nom] = choix[a.nom] === 'DISPARUE' ? null : Number(choix[a.nom])
    setSupprBusy(true)
    try {
      const rd = await fetchWithTimeout('/api/admin/labo/referentiels/debloquer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(r.cycle_id), niveau: r.niveau, correspondances }),
      }, TIMEOUT_LONG)
      const d = await rd.json().catch(() => ({}))
      if (!rd.ok) { showError(d.detail || `Déblocage impossible (${rd.status}).`); return }
      setCorresp(null)
      const nom = p => `• ${[p.prenom, p.nom].filter(Boolean).join(' ') || '(sans nom)'} — ${p.email}`
      const remplaces = d.remplaces || []
      const perdus = d.non_rebranches || []
      // On rend compte des TROIS issues, nommément — et un remplacement se relit des deux côtés.
      await demanderConfirmation({
        titre: 'Professeurs débloqués',
        message: `${(d.rebranches || []).length} professeur(s) ont retrouvé leur matière.\n\n`
          + (remplaces.length
            ? `${remplaces.length} ont changé de matière :\n\n`
              + remplaces.map(p => `${nom(p)} — « ${p.avant} » → « ${p.apres} »`).join('\n') + '\n\n'
            : '')
          + (perdus.length
            ? `${perdus.length} n’ont PAS pu être rebranchés — leur matière a disparu du programme. `
              + `Ils sont libérés et invités à rechoisir dans leur profil :\n\n`
              + perdus.map(nom).join('\n')
            : 'Aucun professeur laissé sans matière.'),
        icone: perdus.length ? 'interdit' : undefined,
        boutonUnique: true, confirmLabel: 'J’ai compris',
      })
      chargerBlocages(r)
    } catch (e) { showError(`Déblocage impossible.\n\n${e.message}`) }
    finally { setSupprBusy(false) }
  }

  // Après un dépôt réussi. Le document est rangé et sa ligne est en base — mais RIEN N'EST
  // CLÔTURÉ : le couple n'a pas encore de référentiel, on peut en déposer d'autres. La liste des
  // documents revient avec la réponse, l'écran l'affiche, et c'est « Fusionner » qui finira.
  // Document DÉJÀ CONNU (même contenu ailleurs) : on prévient, on ne bloque pas — un même
  // programme peut légitimement servir deux niveaux.
  async function apresDepot(d) {
    setNiveau(d.niveau)
    setDocs(d.documents || [])
    setNomFichier(''); setUrl('')
    chargerListe(); chargerArbre(); chargerDocuments(d.niveau_id)
    if (!d.deja) return
    await demanderConfirmation({
      titre: 'Ce document est déjà connu',
      message: `Ce document est déjà le référentiel de ${d.deja.cycle} · ${d.deja.niveau}.`
        + (d.deja.fichier ? `\n\nIl y est enregistré sous le nom « ${d.deja.fichier} ».` : '')
        + '\n\nC’est le même fichier, quel que soit son nom : la comparaison porte sur son contenu.'
        + '\n\nVotre dépôt a bien été enregistré — vous pouvez continuer.',
      icone: 'interdit',
      boutonUnique: true, confirmLabel: 'J’ai compris',
    })
  }

  // La liste des documents du couple, LUE EN BASE. L'écran ne garde rien : il relit.
  // Rend l'état pour qui veut décider dessus (la fusion s'en sert après un échec réseau).
  async function chargerDocuments(nid) {
    if (!nid) { setDocs([]); setDocsInfo(null); return null }
    try {
      const r = await fetchWithTimeout(
        `/api/admin/labo/referentiels/documents?niveau_id=${Number(nid)}`,
        { credentials: 'include' }, TIMEOUT_STD)
      if (!r.ok) return null
      const d = await r.json()
      setDocs(d.documents || []); setDocsInfo(d)
      return d
    } catch { return null }
  }

  // Retirer un morceau : sa ligne et son fichier partent ensemble. Refusé après la fusion — le
  // serveur le dit, et l'écran ne propose même pas le bouton.
  async function retirerDocument(doc) {
    if (!await demanderConfirmation({
      titre: 'Retirer ce document ?',
      message: `« ${doc.fichier} » (${doc.pages} page(s)) sera retiré de la composition et effacé `
        + 'du disque.\n\nLes autres documents ne bougent pas.',
      icone: 'interdit', confirmLabel: 'Retirer', danger: true,
    })) return
    setDocsBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/labo/referentiels/documents/retirer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: doc.id }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      chargerDocuments(niveauId); chargerListe()
    } catch (e) { showError(`Retrait impossible.\n\n${e.message}`) }
    finally { setDocsBusy(false) }
  }

  // L'ordre de la fusion est une DONNÉE : il part en base à chaque déplacement, il ne vit pas
  // dans l'écran. On envoie la liste ENTIÈRE — le serveur refuse un ordre partiel.
  async function deplacerDocument(i, sens) {
    const suite = docs.slice()
    const j = i + sens
    if (j < 0 || j >= suite.length) return
    ;[suite[i], suite[j]] = [suite[j], suite[i]]
    setDocs(suite)                       // l'écran suit tout de suite, la base confirme
    try {
      const r = await fetchWithTimeout('/api/admin/labo/referentiels/documents/ordre', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niveau_id: Number(niveauId), documents: suite.map(d => d.id) }),
      }, TIMEOUT_STD)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setDocs(d.documents || suite)
    } catch (e) {
      showError(`Ordre non enregistré.\n\n${e.message}`)
      chargerDocuments(niveauId)         // la base a raison, pas l'écran
    }
  }

  // CONSTITUER — le geste qui clôture l'étape : le referentiel.pdf est fabriqué, la fiche est
  // créée, les documents lui sont rattachés. Après, on n'empile plus.
  //
  // DEUX CAS, ET L'ADMIN DOIT SAVOIR LEQUEL IL DÉCLENCHE. Avec un seul document, le serveur le
  // reprend TEL QUEL : pas d'IA, rien de réécrit — la confirmation le dit, sinon on ferait croire
  // à une opération qui n'a pas lieu. À partir de deux, l'IA lit et supprime les redites.
  async function constituer() {
    if (!docs.length) { showError('Déposez d’abord au moins un document.'); return }
    if (!await demanderConfirmation({
      titre: parIA ? `Fusionner ${docs.length} documents ?` : 'Valider ce référentiel ?',
      message: (parIA
          ? 'L’IA va lire ces documents et en tirer UN référentiel : elle garde le meilleur, '
            + 'une seule fois, et écarte les redites.\n\n'
          : 'Ce document devient le référentiel tel quel : rien n’est réécrit, rien n’est résumé, '
            + 'l’IA n’est pas appelée.\n\n')
        + `Le référentiel de « ${cycleNom} · ${niveau} » sera créé. Les documents d’origine `
        + 'restent en place.\n\n'
        + 'Pour changer la composition ensuite, il faudra supprimer le référentiel et refaire la '
        + 'procédure.',
      confirmLabel: parIA ? 'Fusionner' : 'Valider',
    })) return
    setDocsBusy(true)
    try {
      // TIMEOUT_XLONG, et pas LONG : quand l'IA travaille, elle lit des centaines de milliers de
      // caractères et l'appel dépasse 45 s. Abandonner avant le serveur fabriquait un faux échec
      // sur un travail déjà payé — et le reclic tombait sur « ce couple a déjà un référentiel ».
      const r = await fetchWithTimeout('/api/admin/labo/referentiels/constituer', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau_id: Number(niveauId) }),
      }, TIMEOUT_XLONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setApercu(d)
      setRefCourant({ cycle_id: d.cycle_id, cycle: d.cycle, niveau_id: d.niveau_id,
                      niveau: d.niveau, complet: false, fichier: d.filename })
      chargerListe(); chargerArbre(); chargerDocuments(d.niveau_id)
      if (d.deja) {
        await demanderConfirmation({
          titre: 'Ce référentiel est déjà connu',
          message: `Le document obtenu est identique au référentiel de ${d.deja.cycle} · ${d.deja.niveau}.`
            + '\n\nLa comparaison porte sur le contenu, pas sur le nom. Votre référentiel a bien '
            + 'été créé — vous pouvez continuer.',
          icone: 'interdit', boutonUnique: true, confirmLabel: 'J’ai compris',
        })
      }
      setShowPdf(true)
    } catch (e) {
      // AVANT DE CONCLURE À L'ÉCHEC, ON RELIT. Une coupure de la liaison n'arrête pas le serveur :
      // le travail a pu aboutir pendant qu'on n'écoutait plus. Annoncer un échec ferait recommencer
      // un travail déjà fait — et déjà facturé.
      const etat = await chargerDocuments(niveauId)
      if (etat && etat.constitue) {
        setRefCourant({ cycle_id: Number(cycleId), cycle: cycleNom, niveau_id: Number(niveauId),
                        niveau, complet: false, fichier: etat.fichier })
        chargerListe(); chargerArbre()
        await demanderConfirmation({
          titre: 'Le référentiel a bien été créé',
          message: 'La liaison a été coupée avant la réponse, mais le serveur est allé au bout : '
            + `le référentiel de « ${cycleNom} · ${niveau} » existe.\n\nRien à refaire.`,
          boutonUnique: true, confirmLabel: 'J’ai compris',
        })
        return
      }
      showError(`Constitution du référentiel impossible.\n\n${e.message}`)
    }
    finally { setDocsBusy(false) }
  }

  // Les pistes appartiennent à UN couple : dès qu'il bouge, elles partent — et la fenêtre de
  // relecture avec elles, sinon on regarderait le document d'un couple qu'on a quitté.
  function oublierPistes() { setPistes(null); setApercuLien(null) }

  // « Chercher » — LA QUESTION EST CELLE QUE L'ADMIN A SOUS LES YEUX, pas une que le serveur
  // fabrique dans son dos. Elle est affichée avant la recherche, pré-remplie avec le couple, et
  // c'est son texte à lui qui part. Le serveur ne filtre rien : ce que le moteur trouve est montré
  // tel quel. Rien n'est téléchargé, rien n'est déposé — un clic sur une piste REMPLIT le champ du
  // lien, et c'est « Récupérer » qui engage le dépôt.
  async function chercherLien() {
    if (!coupleChoisi) { showError('Choisissez d’abord le cycle et le niveau.'); return }
    if (!question.trim()) { showError('Écrivez d’abord ce qu’il faut chercher.'); return }
    setRechBusy(true)
    try {
      const r = await fetchWithTimeout('/api/admin/labo/referentiels/chercher-lien', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau_id: Number(niveauId),
                               question: question.trim() }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      setPistes(d.pistes || [])
    } catch (e) { showError(`Recherche impossible.\n\n${e.message}`) }
    finally { setRechBusy(false) }
  }

  async function recupererLien() {
    if (!coupleChoisi) { showError('Choisissez d’abord le cycle et le niveau.'); return }
    if (!url.trim()) { showError('Collez d’abord le lien du PDF.'); return }
    setBusy(true); setApercu(null)
    try {
      const r = await fetchWithTimeout('/api/admin/labo/referentiels/preparer-lien', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id: Number(cycleId), niveau_id: Number(niveauId), url: url.trim() }),
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      // Pas d'`await` ici : le dépôt est terminé (le bouton doit se dégriser tout de suite), et
      // la suite — fenêtre du PDF ou dialogue — attend l'admin, pas le serveur.
      apresDepot(d)
    } catch (e) { showError(`Récupération impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  async function recupererDepot(file) {
    if (!file) return
    if (!coupleChoisi) { showError('Choisissez d’abord le cycle et le niveau.'); return }
    setNomFichier(file.name)
    setBusy(true); setApercu(null)
    try {
      const form = new FormData()
      form.append('file', file)
      // Le couple voyage AVEC le fichier : c'est lui qui décide où le document est rangé.
      form.append('cycle_id', String(Number(cycleId)))
      form.append('niveau_id', String(Number(niveauId)))
      const r = await fetchWithTimeout('/api/admin/labo/referentiels/preparer-depot', {
        method: 'POST', credentials: 'include', body: form,
      }, TIMEOUT_LONG)
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || `Erreur ${r.status}`)
      apresDepot(d)
    } catch (e) { showError(`Lecture du fichier impossible.\n\n${e.message}`) }
    finally { setBusy(false) }
  }

  // LE COUPLE COMMANDE : tant qu'il n'est pas choisi, le document ne peut pas être déposé — on ne
  // saurait pas où le ranger. Les niveaux proposés sont ceux du cycle choisi, et rien d'autre.
  const coupleChoisi = Boolean(cycleId && niveauId)
  // UN document = on le prend tel quel ; DEUX ou plus = l'IA fusionne. C'est le SERVEUR qui
  // tranche (referentiels_labo.py, route `constituer`) ; ici on ne fait que nommer le bouton et
  // annoncer ce qui va se passer. L'écran ne décide de rien, il dit.
  const parIA = docs.length > 1
  const cycleCourant = arbre.find(c => String(c.id) === String(cycleId)) || {}
  const cycleNom = cycleCourant.nom || (refCourant ? refCourant.cycle : '')
  const niveauxDuCycle = cycleCourant.niveaux || []

  // La question se REPROPOSE à chaque couple : le cycle et le niveau, rien d'autre — les deux
  // seules choses qu'on sache à coup sûr du document cherché. Elle est écrasée sans état d'âme au
  // changement de couple : celle du couple précédent n'a plus de sens ici.
  // La saisie de l'admin est donc gardée AVEC le couple auquel elle appartient : dès qu'on change
  // de couple elle ne correspond plus, et la proposition reprend la main — sans rien à effacer.
  const coupleCle = `${cycleNom}|${niveau}`
  const question = saisieQuestion?.couple === coupleCle
    ? saisieQuestion.texte
    : `${cycleNom} ${niveau}`.trim()
  const setQuestion = (texte) => setSaisieQuestion({ couple: coupleCle, texte })

  // Les étapes de la frise, LUES de l'état réel de l'écran — jamais un compteur qu'on avance à la
  // main. Un couple ouvert depuis la colonne a forcément les deux : il a son référentiel.
  const etapes = [
    { n: 1, label: 'Cycle et niveau', fait: coupleChoisi || Boolean(refCourant),
      aide: 'Choisissez le couple du document : c’est lui qui décide où il est rangé.' },
    { n: 2, label: 'Document PDF', fait: Boolean(apercu || refCourant),
      aide: 'Fournissez le référentiel officiel de ce couple, par dépôt ou par lien.' },
  ]

  const champ = { width: '100%', border: '1px solid #d1d5db', borderRadius: 6, padding: '8px 10px', fontSize: 13 }
  // Les deux flèches d'ordre : même gabarit, la couleur et le curseur disent seuls si elles servent.
  const flecheDoc = { width: 24, height: 24, flexShrink: 0, borderRadius: 5, fontSize: 11,
                      background: '#fff', border: '1px solid #e2e8f0', lineHeight: 1 }
  const onglet = (actif) => ({
    fontSize: 12, padding: '6px 14px', borderRadius: 6, cursor: 'pointer',
    border: actif ? '1px solid #1F6EEB' : '1px solid #e2e8f0',
    background: actif ? '#eff6ff' : '#f8fafc', color: actif ? '#1d4ed8' : '#64748b', fontWeight: 600,
  })

  return (
    <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>

      {/* Colonne 2 — liste des référentiels déposés (get /liste). Clic = ouvre le couple à droite. */}
      <aside style={{ width: 240, flexShrink: 0, background: '#fff', border: '1px solid #e2e8f0',
        borderRadius: 12, overflow: 'hidden',
        position: 'sticky', top: 0, alignSelf: 'flex-start' }}>
        <div style={{ padding: '10px 12px', borderBottom: '1px solid #e2e8f0', fontSize: 12,
          fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Catalogues ({refsListe.length})
        </div>
        {/* « + Nouveau » en premier, couleur distincte, sélectionné par défaut (aucun référentiel ouvert). */}
        {(() => {
          const nouveauActif = !refsListe.some(r => String(r.cycle_id) === String(cycleId) && r.niveau === niveau)
          return (
            <button type="button" onClick={nouveau}
              title="Créer un nouveau référentiel (choisir un couple, déposer le PDF)"
              style={{ width: '100%', height: 42, cursor: 'pointer',
                border: '1px solid #334155', borderRadius: 8, fontWeight: 600, fontSize: 13,
                background: nouveauActif ? '#334155' : '#0f172a', color: '#fff',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              <span aria-hidden="true" style={{ fontSize: 22, lineHeight: 0, fontWeight: 400 }}>＋</span>
              Nouveau
            </button>
          )
        })()}
        {refsListe.length === 0 ? (
          <div style={{ padding: 12, fontSize: 12, color: '#94a3b8' }}>Aucun référentiel déposé.</div>
        ) : refsListe.map(r => {
          const actif = String(cycleId) === String(r.cycle_id) && niveau === r.niveau
          return (
            // `en_cours` : des documents déposés, le référentiel pas encore constitué. La ligne est
            // là pour qu'un travail commencé ne disparaisse pas de l'écran quand l'admin s'en va.
            <button key={r.id || `encours-${r.niveau_id}`} type="button" onClick={() => ouvrirRef(r)}
              title={r.en_cours
                ? `${r.cycle} · ${r.niveau} — ${r.documents} document(s) déposé(s), référentiel à constituer`
                : `${r.cycle} · ${r.niveau}`}
              style={{ display: 'block', width: '100%', textAlign: 'left', padding: '9px 12px',
                border: 'none', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', fontSize: 13,
                background: actif ? '#eff6ff' : '#fff', color: actif ? '#1d4ed8' : '#1e293b',
                fontWeight: actif ? 600 : 400 }}>
              <Pastille etat={r.en_cours ? 'jaune' : r.complet ? 'vert' : 'rouge'}
                titre={r.en_cours ? 'Documents déposés, référentiel à constituer'
                  : r.complet ? 'Procédure complète' : 'Procédure à terminer'} />
              {r.cycle} · {r.niveau}
              {r.en_cours && (
                <span style={{ marginLeft: 6, fontSize: 11, color: '#b45309' }}>
                  {r.documents} doc.
                </span>
              )}
              {r.forcage_motif && <span title="Validé en forçage" style={{ marginLeft: 6, color: '#b45309' }}>⚠</span>}
            </button>
          )
        })}
      </aside>

      {/* Colonne 3 — l'écran de travail du référentiel. */}
      <div className="flex flex-col gap-6" style={{ flex: 1, minWidth: 0 }}>
      <div className="flex flex-col gap-3">
        <h2 className="text-base font-semibold text-gray-800">Référentiels</h2>
        <Frise etapes={etapes} />
      </div>

      {/* Carte — le référentiel ouvert par la colonne. Elle ne porte pour l'instant que le geste
          de suppression ; le reste de la procédure viendra étape par étape. Bouton rouge repris
          tel quel de l'écran Référentiels. */}
      {refCourant && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center justify-between gap-4 flex-wrap">
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={refCourant.complet ? 'vert' : 'rouge'}
              titre={refCourant.complet ? 'Procédure complète' : 'Procédure à terminer'} />
            {refCourant.cycle} · {refCourant.niveau}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {/* Débloquer : visible tant qu'il reste des professeurs en attente sur ce niveau.
                Geste explicite — jamais déclenché par la fin de la découpe. */}
            {blocages.bloques > 0 && (
              <button type="button" onClick={() => ouvrirDeblocage(refCourant)} disabled={supprBusy}
                title={`Rendre la main aux ${blocages.bloques} professeur(s) en attente : vous désignez la matière du nouveau référentiel qui remplace chacune de celles qu'ils attendent`}
                style={{ height: 30, display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                  fontSize: 12, fontWeight: 700, padding: '0 12px', borderRadius: 6,
                  cursor: supprBusy ? 'not-allowed' : 'pointer',
                  background: supprBusy ? '#e2e8f0' : '#1F6EEB', color: supprBusy ? '#94a3b8' : '#fff',
                  border: 'none' }}>
                <span aria-hidden="true">🔓</span> Débloquer {blocages.bloques} professeur(s)
              </button>
            )}
            <button type="button" onClick={() => supprimerReferentiel(refCourant)} disabled={supprBusy}
              title="Supprimer définitivement ce référentiel (efface la fiche, ses matières, ses unités, ses types et le PDF)"
              style={{ height: 30, display: 'inline-flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
                fontSize: 12, fontWeight: 700, padding: '0 12px', borderRadius: 6,
                cursor: supprBusy ? 'not-allowed' : 'pointer',
                background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
              <span aria-hidden="true">⛔</span> Supprimer le référentiel
            </button>
          </div>
        </div>
      )}

      {/* Carte 1 — Cycle et niveau : le PREMIER geste de l'ajout, avant le document. Cascade
          recopiée telle quelle d'AdminReferentiels.jsx (carte « Couple ») : mêmes libellés,
          mêmes styles, même garde-fou quand un cycle n'a aucun niveau. Le dépôt ne propose QUE
          l'existant — créer un niveau se fait à une seule place, l'écran Programmes.
          Masquée quand un couple est déjà ouvert par la colonne : il a son référentiel. */}
      {!refCourant && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
          <div>
            <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
              <Pastille etat={coupleChoisi ? 'vert' : 'rouge'} titre="Vert = un couple est choisi." />
              Cycle et niveau
            </h2>
            <p className="text-sm text-gray-500" style={{ margin: 0 }}>
              Choisissez le cycle et le niveau du document que vous allez déposer. C’est ce couple qui décide où le document est rangé.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label className="block text-xs text-gray-500 mb-1">Cycle</label>
              <select style={{ ...champ, background: '#fff' }} value={cycleId}
                onChange={e => { setCycleId(e.target.value); setNiveauId(''); setNiveau('')
                                 oublierPistes(); setDocs([]); setDocsInfo(null) }}
                title="Choisissez d'abord le cycle — les niveaux de ce cycle apparaissent à droite">
                <option value="">— Choisissez un cycle —</option>
                {arbre.map(c => <option key={c.id} value={c.id}>{c.nom}</option>)}
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 180 }}>
              <label className="block text-xs text-gray-500 mb-1">Niveau</label>
              <select style={{ ...champ, background: '#fff' }} value={niveauId} disabled={!cycleId}
                onChange={e => {
                  const id = e.target.value
                  setNiveauId(id)
                  const n = niveauxDuCycle.find(x => String(x.id) === String(id))
                  setNiveau(n ? n.nom : '')
                  oublierPistes()   // les pistes appartiennent à UN couple : il change, elles partent
                  chargerDocuments(id)   // …et les documents aussi : on relit ceux de ce couple
                }}
                title={cycleId ? 'Choisissez le niveau du cycle' : 'Choisissez d’abord le cycle'}>
                <option value="">{cycleId ? '— Choisissez un niveau —' : '—'}</option>
                {niveauxDuCycle.map(n => <option key={n.id} value={n.id}>{n.nom}</option>)}
              </select>
              {cycleId && niveauxDuCycle.length === 0 && (
                <p style={{ fontSize: 12, color: '#b45309', marginTop: 4 }}>
                  Ce cycle n’a encore aucun niveau — créez-le d’abord dans l’écran Programmes (bouton « + Niveau »).
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Carte 2 — Document PDF. Elle N'APPARAÎT PAS tant que le couple n'est pas complet : le
          document ne peut pas être déposé sans lui (sa place en dépend), et une carte affichée
          mais inerte donne à croire qu'on peut s'en servir.
          UN RÉFÉRENTIEL PEUT TENIR EN PLUSIEURS PDF : on empile les documents, on les ordonne, on
          en retire, et c'est « Fusionner » qui clôture — c'est lui qui fabrique le référentiel et
          crée la fiche. Tant qu'il n'est pas cliqué, rien n'est arrêté. */}
      {(coupleChoisi || refCourant) && (
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-800" style={{ margin: 0 }}>
            <Pastille etat={(apercu || refCourant) ? 'vert' : docs.length ? 'jaune' : 'rouge'}
              titre="Vert = le couple a son référentiel. Jaune = des documents sont déposés, le référentiel reste à constituer." />
            Document PDF
          </h2>
          <p className="text-sm text-gray-500" style={{ margin: 0 }}>
            {refCourant
              ? 'Ce couple a son référentiel. Pour en changer, supprimez d’abord celui-ci.'
              : docs.length
                ? (parIA
                    ? 'Ces documents sont dans l’ordre où l’IA les lira. Fusionnez quand la composition vous convient : elle en tire un seul référentiel, sans redite.'
                    : 'Ce document suffit-il ? Validez-le, il devient le référentiel tel quel. S’il en manque, ajoutez-les : à partir de deux, l’IA les fusionne.')
                : 'Fournissez le référentiel officiel de ce couple, par dépôt ou par lien. Un programme publié en plusieurs PDF se dépose en plusieurs fois.'}
          </p>
        </div>
        {!refCourant && (<>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button type="button" title="Déposer le fichier PDF du référentiel" style={onglet(mode === 'depot')} onClick={() => setMode('depot')}>Par dépôt</button>
          <button type="button" title="Fournir le référentiel par un lien vers le PDF" style={onglet(mode === 'lien')} onClick={() => setMode('lien')}>Par lien</button>
          {/* Le « i » du dépôt par lien — même composant que les écrans du prof (survol = une
              phrase, clic = la fiche encadrée, qui reste jusqu'au ✕). Le texte long DIT CE QUE
              LE SERVEUR FAIT VRAIMENT (referentiels_labo.py : téléchargement suivi de
              redirections, 30 s, puis les contrôles de _deposer), il ne le promet pas. */}
          <InfoGuide
            titre="Par lien"
            court="Collez l’adresse du PDF officiel : le serveur va le chercher lui-même."
            long={"Collez l’adresse (URL) du PDF officiel du référentiel — celle d’Éduscol ou du Bulletin officiel — puis cliquez « Récupérer ».\n\nVous ne l’avez pas sous la main ? Le cadre « Ce qu’on demande au moteur de recherche » vous propose une recherche, pré-remplie avec le cycle et le niveau. Corrigez-la comme vous voulez : c’est votre texte, tel quel, qui part au moteur. Les résultats reviennent dans SON ordre, sans être triés ni filtrés — à vous de juger, le bouton « Voir » ouvre chaque document. Un clic met un lien dans le champ ; rien n’est déposé tant que vous n’avez pas cliqué « Récupérer ».\n\nC’est le serveur qui télécharge le document, pas votre navigateur : il suit les redirections et abandonne au bout de 30 secondes. Le nom du fichier est repris de la fin du lien.\n\nAvant de le garder, il le contrôle comme un dépôt : c’est bien un PDF, il ne dépasse ni la taille ni le nombre de pages autorisés. Un document refusé ne laisse aucune trace — la place de ce couple n’est pas touchée.\n\nAccepté, il devient immédiatement le référentiel du couple choisi : il prend sa place et sa fiche naît avec lui. Pour en déposer un autre, il faudra d’abord supprimer celui-ci.\n\nPas de lien sous la main ? L’onglet « Par dépôt » fait la même chose avec un fichier de votre ordinateur."}
          />
        </div>
        {mode === 'lien' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label className="block text-xs text-gray-500 mb-1">Lien du PDF</label>
              <input style={champ} value={url} onChange={e => setUrl(e.target.value)}
                disabled={!coupleChoisi} placeholder="https://…/referentiel.pdf" />
            </div>
            <button type="button" className="btn-primary" onClick={recupererLien}
              disabled={busy || !coupleChoisi}
              title={coupleChoisi ? 'Télécharger le PDF depuis ce lien et le ranger sous ce couple'
                : 'Choisissez d’abord le cycle et le niveau'}
              style={{ height: 36, cursor: (busy || !coupleChoisi) ? 'not-allowed' : 'pointer',
                opacity: coupleChoisi ? 1 : 0.6 }}>
              {busy ? 'Récupération…' : 'Récupérer'}
            </button>
          </div>

          {/* LA RECHERCHE, À DÉCOUVERT. Ce qui part au moteur est écrit là, modifiable, et c'est
              exactement ce texte qui est envoyé. Rien n'est filtré au retour : les résultats
              arrivent dans l'ordre du moteur. Cette zone n'existe que si le serveur a sa clé. */}
          {rechDispo && (
            <div style={{ border: '1px solid #e9d5ff', background: '#faf5ff', borderRadius: 8,
              padding: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label style={{ fontSize: 11.5, color: '#7c3aed', fontWeight: 700,
                textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                Ce qu’on demande au moteur de recherche
              </label>
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                <input style={{ ...champ, flex: 1, background: '#fff' }} value={question}
                  onChange={e => setQuestion(e.target.value)} disabled={!coupleChoisi || rechBusy}
                  title="Écrivez ce qu’il faut chercher — c’est ce texte, tel quel, qui part au moteur"
                  onKeyDown={e => { if (e.key === 'Enter') chercherLien() }}
                  placeholder="Cycle et niveau, ou ce que vous voulez chercher" />
                <button type="button" onClick={chercherLien}
                  disabled={rechBusy || busy || !coupleChoisi || !question.trim()}
                  title={coupleChoisi ? 'Envoyer cette recherche — les liens trouvés vous sont proposés, rien n’est déposé'
                    : 'Choisissez d’abord le cycle et le niveau'}
                  style={{ height: 36, display: 'inline-flex', alignItems: 'center', gap: 6,
                    whiteSpace: 'nowrap', fontSize: 13, fontWeight: 500, padding: '0 14px',
                    borderRadius: 6, border: 'none',
                    background: (rechBusy || busy || !coupleChoisi || !question.trim()) ? '#e2e8f0' : '#7c3aed',
                    color: (rechBusy || busy || !coupleChoisi || !question.trim()) ? '#94a3b8' : '#fff',
                    cursor: (rechBusy || busy || !coupleChoisi || !question.trim()) ? 'not-allowed' : 'pointer' }}>
                  {rechBusy ? <><Spinner /> Recherche…</> : <><span aria-hidden="true">🔎</span> Chercher</>}
                </button>
              </div>
            </div>
          )}

          {/* Les pistes trouvées. Un clic REMPLIT le champ, rien de plus : le dépôt reste un geste
              à part. Le titre et l'adresse sont montrés en entier — l'admin juge sur pièce. */}
          {pistes && (
            <div style={{ border: '1px solid #e9d5ff', background: '#faf5ff', borderRadius: 8,
              padding: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {pistes.length === 0 ? (
                <div style={{ fontSize: 12.5, color: '#6b21a8' }}>
                  Le moteur n’a rien trouvé pour cette recherche. Reformulez-la, ou collez
                  l’adresse à la main.
                </div>
              ) : (<>
                <div style={{ fontSize: 11.5, color: '#7c3aed', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                  {pistes.length} résultat(s), dans l’ordre du moteur — cliquez pour remplir le champ
                </div>
                {/* Deux gestes par ligne, distincts : REGARDER (« Voir ») et CHOISIR (le reste de
                    la ligne). Ni l'un ni l'autre ne dépose — « Récupérer » reste seul à le faire. */}
                {pistes.map(p => (
                  <div key={p.url} style={{ display: 'flex', alignItems: 'center', gap: 8,
                    padding: '6px 8px', borderRadius: 6,
                    background: url === p.url ? '#ede9fe' : '#fff',
                    border: `1px solid ${url === p.url ? '#a78bfa' : '#e2e8f0'}` }}>
                    <button type="button" onClick={() => setUrl(p.url)}
                      title={`Mettre ce lien dans le champ (rien n’est déposé) — ${p.url}`}
                      style={{ flex: 1, minWidth: 0, textAlign: 'left', background: 'none',
                        border: 'none', padding: 0, cursor: 'pointer' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 12.5, fontWeight: 600, color: '#1e293b' }}>{p.titre}</span>
                        {/* PDF ou page web : une INDICATION, pas un tri. Seul un PDF se dépose ;
                            une page peut quand même mener au bon document, on ne la cache pas. */}
                        <span title={p.pdf ? 'Ce lien est un PDF : « Récupérer » peut le déposer'
                          : 'Ce lien est une page web, pas un PDF — « Récupérer » le refusera'}
                          style={{ fontSize: 10, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
                            flexShrink: 0, background: p.pdf ? '#ede9fe' : '#f1f5f9',
                            color: p.pdf ? '#6d28d9' : '#94a3b8' }}>
                          {p.pdf ? 'PDF' : 'page web'}
                        </span>
                      </span>
                      <span style={{ display: 'block', fontSize: 11, color: '#64748b',
                        wordBreak: 'break-all', marginTop: 2 }}>{p.url}</span>
                    </button>
                    <button type="button" onClick={() => setApercuLien(p)}
                      title="Ouvrir ce PDF pour le vérifier avant de le choisir — rien n’est déposé"
                      style={{ height: 28, flexShrink: 0, display: 'inline-flex', alignItems: 'center',
                        gap: 5, fontSize: 12, fontWeight: 600, padding: '0 10px', borderRadius: 6,
                        cursor: 'pointer', background: '#fff', color: '#6d28d9',
                        border: '1px solid #c4b5fd' }}>
                      <span aria-hidden="true">👁</span> Voir
                    </button>
                  </div>
                ))}
              </>)}
            </div>
          )}
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label className="block text-xs text-gray-500 mb-1">Fichier PDF</label>
              <input style={champ} value={nomFichier} readOnly placeholder="Aucun fichier choisi" />
            </div>
            <input id="pdf-depot" type="file" accept="application/pdf,.pdf" style={{ display: 'none' }}
              disabled={busy || !coupleChoisi} onChange={e => recupererDepot(e.target.files[0])} />
            <label htmlFor={coupleChoisi ? 'pdf-depot' : undefined} className="btn-primary"
              title={coupleChoisi ? 'Choisir le fichier PDF du référentiel à téléverser'
                : 'Choisissez d’abord le cycle et le niveau'}
              style={{ cursor: (busy || !coupleChoisi) ? 'not-allowed' : 'pointer',
                opacity: (busy || !coupleChoisi) ? 0.6 : 1,
                display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              {busy ? <><Spinner /> Lecture…</> : 'Choisir le fichier'}
            </label>
          </div>
        )}
        </>)}

        {/* LES MORCEAUX DÉPOSÉS — la composition du référentiel, lue en base. Chaque ligne se
            relit (« Voir »), se déplace (▲▼ : l'ordre est celui de la fusion) et se retire.
            Une fois fusionnée, la liste reste affichée mais ne bouge plus : elle dit de quoi le
            référentiel est fait. */}
        {docs.length > 0 && (
          <div style={{ border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 8, padding: '7px 10px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 11.5, fontWeight: 700, color: '#475569',
                textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                {docs.length} document(s) {refCourant ? 'retenu(s)' : 'déposé(s)'}
              </span>
              {docsInfo && (
                // Ce qu'on donne À LIRE à l'IA. Aucun plafond ici : des documents longs, c'est
                // normal — c'est même la raison d'être de la fusion. Le plafond, lui, porte sur
                // ce qu'elle PRODUIT, et il est rappelé sous le bouton.
                <span style={{ fontSize: 11.5, fontWeight: 600, color: '#64748b' }}
                  title="Ce que l’IA va lire pour en tirer le référentiel">
                  {docsInfo.total_pages} page(s) à lire · {docsInfo.total_ko} Ko
                </span>
              )}
            </div>
            {docs.map((d, i) => (
              <div key={d.id} style={{ display: 'flex', alignItems: 'center', gap: 8,
                padding: '7px 10px', borderBottom: i < docs.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', width: 16,
                  flexShrink: 0, fontVariantNumeric: 'tabular-nums' }}>{i + 1}</span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: 'block', fontSize: 12.5, fontWeight: 600, color: '#1e293b',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {d.fichier}
                  </span>
                  <span style={{ fontSize: 11, color: '#64748b' }}>
                    {d.pages} page(s) · {d.taille_ko} Ko · {d.source === 'lien' ? 'par lien' : 'par dépôt'}
                  </span>
                </span>
                {!refCourant && (
                  <>
                    <button type="button" onClick={() => deplacerDocument(i, -1)}
                      disabled={i === 0 || docsBusy} title="Monter ce document dans l’ordre de fusion"
                      style={{ ...flecheDoc, cursor: (i === 0 || docsBusy) ? 'not-allowed' : 'pointer',
                        color: i === 0 ? '#cbd5e1' : '#475569' }}>▲</button>
                    <button type="button" onClick={() => deplacerDocument(i, 1)}
                      disabled={i === docs.length - 1 || docsBusy}
                      title="Descendre ce document dans l’ordre de fusion"
                      style={{ ...flecheDoc, cursor: (i === docs.length - 1 || docsBusy) ? 'not-allowed' : 'pointer',
                        color: i === docs.length - 1 ? '#cbd5e1' : '#475569' }}>▼</button>
                  </>
                )}
                <button type="button" onClick={() => setVoirDoc(d)}
                  title="Ouvrir ce document pour le vérifier"
                  style={{ height: 26, flexShrink: 0, display: 'inline-flex', alignItems: 'center',
                    gap: 4, fontSize: 11.5, fontWeight: 600, padding: '0 9px', borderRadius: 6,
                    cursor: 'pointer', background: '#fff', color: '#1d4ed8',
                    border: '1px solid #bfdbfe' }}>
                  <span aria-hidden="true">👁</span> Voir
                </button>
                {!refCourant && (
                  <button type="button" onClick={() => retirerDocument(d)} disabled={docsBusy}
                    title="Retirer ce document de la composition (il sera effacé)"
                    style={{ height: 26, flexShrink: 0, display: 'inline-flex', alignItems: 'center',
                      gap: 4, fontSize: 11.5, fontWeight: 600, padding: '0 9px', borderRadius: 6,
                      cursor: docsBusy ? 'not-allowed' : 'pointer', background: '#fee2e2',
                      color: '#dc2626', border: '1px solid #fecaca' }}>
                    <span aria-hidden="true">⛔</span> Retirer
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* LE GESTE QUI CLÔTURE. Il n'apparaît que tant que le couple n'a pas sa fiche.
            Il ne dit PAS la même chose selon le nombre de documents, et c'est le fond du sujet :
            avec un seul, il n'y a rien à fusionner — le document EST le référentiel, on le valide.
            Annoncer « Fusionner » là serait promettre un travail qui n'a pas lieu (et le violet de
            l'IA, une dépense qui n'existe pas). Le serveur tranche pareil, de son côté. */}
        {!refCourant && docs.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 10 }}>
            <span style={{ fontSize: 11.5, color: '#64748b', textAlign: 'right' }}>
              {parIA
                ? <>L’IA lit ces documents et en tire un référentiel de {docsInfo ? docsInfo.max_pages : 15} pages
                    maximum, sans redite.<br /></>
                : <>Ce document devient le référentiel tel quel : rien n’est réécrit, l’IA n’est pas appelée.<br /></>}
              Ensuite, on ne peut plus ajouter de document.
            </span>
            <button type="button" onClick={constituer} disabled={docsBusy}
              title={parIA ? 'Faire lire ces documents à l’IA et créer le référentiel de ce couple'
                : 'Prendre ce document tel quel comme référentiel de ce couple'}
              style={{ height: 36, display: 'inline-flex', alignItems: 'center', gap: 6,
                whiteSpace: 'nowrap', fontSize: 13, fontWeight: 600, padding: '0 16px',
                borderRadius: 6, border: 'none',
                background: docsBusy ? '#e2e8f0' : (parIA ? '#7c3aed' : '#16a34a'),
                color: docsBusy ? '#94a3b8' : '#fff',
                cursor: docsBusy ? 'not-allowed' : 'pointer' }}>
              {docsBusy
                ? <><Spinner /> {parIA ? 'Fusion en cours…' : 'Création…'}</>
                : parIA
                  ? <><span aria-hidden="true">🧩</span> Fusionner</>
                  : <><span aria-hidden="true">✔</span> Valider le référentiel</>}
            </button>
          </div>
        )}

        {(apercu || (refCourant && refCourant.fichier)) && (
          <div style={{ fontSize: 12, color: '#475569' }}>
            Référentiel : <strong>{apercu ? apercu.filename : refCourant.fichier}</strong>
            {apercu && <> · {apercu.pages} page(s) · {apercu.taille_ko} Ko</>}{' '}
            <button type="button" onClick={() => setShowPdf(true)}
              title="Ouvrir le référentiel de ce couple"
              style={{ background: 'none', border: 'none', padding: 0, color: '#1d4ed8',
                fontSize: 12, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}>
              Voir le PDF
            </button>
          </div>
        )}
      </div>
      )}
      </div>

      {/* Panneau de déblocage — LE choix de l'admin : à gauche ce que les professeurs attendent,
          à droite ce que le nouveau document propose. Une ligne par matière attendue, et rien ne
          part tant qu'elles n'ont pas toutes une réponse : une matière utilisée ne disparaît pas,
          elle est remplacée. « Elle disparaît vraiment » n'apparaît que si plus personne ne
          l'attend — le serveur refuse de toute façon les autres cas. */}
      {corresp && (() => {
        const complet = corresp.attendues.every(a => corresp.choix[a.nom] !== '')
        const majChoix = (nom, v) => setCorresp(c => ({ ...c, choix: { ...c.choix, [nom]: v } }))
        return (
          <div onClick={() => !supprBusy && setCorresp(null)}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
              display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
            <div onClick={e => e.stopPropagation()}
              style={{ background: '#fff', borderRadius: 12, width: '92%', maxWidth: 720,
                maxHeight: '88vh', display: 'flex', flexDirection: 'column', overflow: 'hidden',
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
              <div style={{ padding: '14px 18px', borderBottom: '1px solid #e2e8f0' }}>
                <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#1e293b' }}>
                  Débloquer les professeurs de « {corresp.ref.cycle} · {corresp.ref.niveau} »
                </h3>
                <p style={{ margin: '6px 0 0', fontSize: 12.5, color: '#64748b' }}>
                  Une matière qu’un professeur utilise ne disparaît pas : elle est remplacée.
                  Indiquez, pour chacune, la matière du nouveau programme qui prend sa place.
                </p>
              </div>
              <div style={{ padding: '14px 18px', overflowY: 'auto', display: 'flex',
                flexDirection: 'column', gap: 10 }}>
                {corresp.attendues.length === 0 && (
                  <div style={{ fontSize: 13, color: '#64748b' }}>
                    Aucune matière n’est attendue : les professeurs en attente n’avaient pas de
                    matière rattachée à ce référentiel.
                  </div>
                )}
                {corresp.attendues.map(a => (
                  <div key={a.nom} style={{ display: 'flex', alignItems: 'center', gap: 10,
                    flexWrap: 'wrap' }}>
                    <div style={{ flex: '1 1 200px', minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{a.nom}</div>
                      <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                        {a.profs} professeur(s) l’attendent
                      </div>
                    </div>
                    <span aria-hidden="true" style={{ color: '#94a3b8' }}>→</span>
                    <select value={corresp.choix[a.nom]} onChange={e => majChoix(a.nom, e.target.value)}
                      title={`Matière du nouveau programme qui remplace « ${a.nom} »`}
                      style={{ ...champ, flex: '1 1 220px', width: 'auto',
                        borderColor: corresp.choix[a.nom] === '' ? '#fca5a5' : '#d1d5db' }}>
                      <option value="">— à désigner —</option>
                      {corresp.matieres.map(m => (
                        <option key={m.id} value={String(m.id)}>{m.nom}</option>
                      ))}
                      {a.peut_disparaitre && <option value="DISPARUE">Elle disparaît vraiment</option>}
                    </select>
                  </div>
                ))}
              </div>
              <div style={{ padding: '12px 18px', borderTop: '1px solid #e2e8f0', display: 'flex',
                justifyContent: 'flex-end', gap: 8 }}>
                <button type="button" onClick={() => setCorresp(null)} disabled={supprBusy}
                  title="Fermer sans rien changer"
                  style={{ height: 32, padding: '0 14px', borderRadius: 6, fontSize: 12.5,
                    fontWeight: 700, border: '1px solid #fecaca', background: '#fee2e2',
                    color: '#dc2626', cursor: supprBusy ? 'not-allowed' : 'pointer' }}>
                  Annuler
                </button>
                <button type="button" onClick={confirmerDeblocage} disabled={supprBusy || !complet}
                  title={complet
                    ? 'Rebrancher les professeurs sur les matières désignées et leur rendre la main'
                    : 'Désignez d’abord la matière qui remplace chacune des matières attendues'}
                  style={{ height: 32, padding: '0 14px', borderRadius: 6, fontSize: 12.5,
                    fontWeight: 700, border: 'none', color: '#fff',
                    background: (supprBusy || !complet) ? '#cbd5e1' : '#1F6EEB',
                    cursor: (supprBusy || !complet) ? 'not-allowed' : 'pointer' }}>
                  {supprBusy ? <><Spinner /> Déblocage…</> : 'Débloquer'}
                </button>
              </div>
            </div>
          </div>
        )
      })()}

      {/* Fenêtre de relecture d'UN MORCEAU déjà déposé — avant la fusion, et après elle pour
          savoir ce qu'on a assemblé. Servi par notre serveur, depuis le dossier du couple. */}
      {voirDoc && (
        <div onClick={() => setVoirDoc(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', minWidth: 0,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {voirDoc.fichier} · {voirDoc.pages} page(s)
              </span>
              <button type="button" onClick={() => setVoirDoc(null)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1,
                  color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <iframe title={voirDoc.fichier}
              src={`/api/admin/labo/referentiels/document-pdf?document_id=${Number(voirDoc.id)}`}
              style={{ flex: 1, width: '100%', border: 'none' }} />
          </div>
        </div>
      )}

      {/* Fenêtre de relecture d'une PISTE — avant tout dépôt. Le PDF est affiché DEPUIS le site
          officiel : notre serveur ne le télécharge pas, la base ne bouge pas, rien n'est rangé.
          Deux sorties, parce qu'un site peut refuser d'être affiché dans un cadre : la fenêtre,
          et le lien « ouvrir dans un nouvel onglet » qui marche toujours. */}
      {apercuLien && (
        <div onClick={() => setApercuLien(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              gap: 10, padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', minWidth: 0,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {apercuLien.titre}
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                <a href={apercuLien.url} target="_blank" rel="noopener noreferrer"
                  title="Ouvrir ce PDF dans un nouvel onglet du navigateur"
                  style={{ fontSize: 12, fontWeight: 600, color: '#1d4ed8' }}>
                  Ouvrir dans un onglet
                </a>
                {/* Choisir DEPUIS la fenêtre : on vient de lire le document, c'est le bon moment.
                    Ça remplit le champ et referme — le dépôt reste « Récupérer ». */}
                <button type="button" onClick={() => { setUrl(apercuLien.url); setApercuLien(null) }}
                  title="Mettre ce lien dans le champ (rien n’est déposé)"
                  style={{ height: 28, fontSize: 12, fontWeight: 700, padding: '0 12px',
                    borderRadius: 6, border: 'none', background: '#7c3aed', color: '#fff',
                    cursor: 'pointer' }}>
                  Choisir ce lien
                </button>
                <button type="button" onClick={() => setApercuLien(null)} title="Fermer"
                  style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1,
                    color: '#64748b', cursor: 'pointer' }}>×</button>
              </span>
            </div>
            <iframe title={apercuLien.titre} src={apercuLien.url}
              style={{ flex: 1, width: '100%', border: 'none' }} />
          </div>
        </div>
      )}

      {/* Fenêtre de relecture : le document DU COUPLE, repliable (clic dehors ou ×). Il est rangé
          à sa place définitive dès le dépôt — le couple suffit à le retrouver, il n'y a plus de
          jeton. Patron recopié d'AdminReferentiels.jsx. */}
      {showPdf && (apercu || refCourant) && (
        <div onClick={() => setShowPdf(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)', zIndex: 2000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div onClick={e => e.stopPropagation()}
            style={{ background: '#fff', borderRadius: 12, width: '90%', maxWidth: 900, height: '88vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 14px', borderBottom: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                {(apercu ? apercu.filename : refCourant.fichier) || 'Référentiel'}
              </span>
              <button type="button" onClick={() => setShowPdf(false)} title="Fermer"
                style={{ background: 'none', border: 'none', fontSize: 20, lineHeight: 1, color: '#64748b', cursor: 'pointer' }}>×</button>
            </div>
            <iframe
              title="Référentiel PDF"
              src={`/api/admin/labo/referentiels/pdf?cycle_id=${Number(apercu ? apercu.cycle_id : refCourant.cycle_id)}`
                + `&niveau=${encodeURIComponent(apercu ? apercu.niveau : refCourant.niveau)}`}
              style={{ flex: 1, width: '100%', border: 'none' }} />
          </div>
        </div>
      )}
    </div>
  )
}
