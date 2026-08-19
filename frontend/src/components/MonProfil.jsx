import { useState, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/contexteAuth.js'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { matieresDuNiveau, matiereIncoherente, profilPretAValider, niveauxRefDisponibles, niveauDisponible } from '../utils/profil.js'
import { showError } from '../errorDialog.js'
import { demanderConfirmation } from '../confirmDialog.js'
import InfoGuide from './InfoGuide.jsx'
import { astucesEcran } from '../utils/astuces.js'
import { aideProfil } from '../utils/aideProfil.js'

// Les astuces de cet écran, lues une fois (catalogue figé) : le « a » ne bouge pas d'un rendu à l'autre.
const astucesProfil = astucesEcran('profil')


// Message de la modale bloquante quand niveau et matière ne vont pas ensemble.
// Langage prof : dit le PROBLÈME puis l'ACTION attendue. `cas` distingue l'ouverture
// (profil déjà incohérent) du changement de niveau (incohérence qu'on vient de créer).
function messageIncoherence(cas, niveau, matiere) {
  const probleme = cas === 'ouverture'
    ? `Votre profil associe la matière « ${matiere} » au niveau « ${niveau} ».\nCe niveau ne propose pas cette matière.`
    : `Vous venez de passer au niveau « ${niveau} ».\nLa matière « ${matiere} » n'y est pas enseignée.`
  return `${probleme}\n\nChoisissez la matière que vous enseignez à ce niveau, puis enregistrez.`
}

// Modale quand le niveau du profil hérité n'est plus disponible (pas de référentiel, donc caché).
function messageNiveauIndisponible(niveau) {
  return `Votre niveau « ${niveau} » n'est pas (ou plus) disponible.\n\n`
    + `Choisissez un niveau disponible, indiquez votre matière, puis enregistrez.`
}

const CLE_OUVERTURE = ['profil', 'ouverture']

export default function MonProfil({ onNavigate }) {
  const { user, refreshUser } = useAuth()
  const queryClient = useQueryClient()
  const [brouillon, setForm] = useState({
    prenom:    user?.prenom    || '',
    nom:       user?.nom       || '',
    subject:   user?.subject   || '',
    niveau:    user?.niveau    || '',
    langue_lv: user?.langue_lv || '',
    mobile:    user?.mobile    || '',
  })
  const [saving, setSaving] = useState(false)

  // LE CHAMP À CORRIGER — celui dont parle le dernier message. Il prend le focus dès que la
  // modale se ferme et porte un liseré rouge tant qu'il est vide : la consigne (« choisissez la
  // matière ») et l'endroit où l'appliquer ne sont plus deux choses séparées.
  const refNiveau  = useRef(null)
  const refMatiere = useRef(null)
  const [champAsignaler, setChampASignaler] = useState(null)   // 'niveau' | 'subject' | null
  // Les deux « viser » lisent la ref AU MOMENT DU CLIC (dans la fonction rendue), jamais au
  // rendu : une ref lue pendant le rendu ne vaut rien, le champ n'est pas encore posé.
  const viserNiveau  = () => { setChampASignaler('niveau');  refNiveau.current?.focus() }
  const viserMatiere = () => { setChampASignaler('subject'); refMatiere.current?.focus() }
  // Un champ signalé qu'on remplit n'a plus rien à signaler.
  const styleSignale = champ => (champAsignaler === champ && !form[champ]
    ? { borderColor: '#dc2626', borderWidth: 2, boxShadow: '0 0 0 3px rgba(220,38,38,0.12)' }
    : undefined)
  const [cahierBusy, setCahierBusy] = useState(false)              // dépôt en cours (sablier sur le bouton)

  // « Ouvrir le PDF d'origine » : ouvre le fichier déposé par l'admin dans un NOUVEL ONGLET
  // (visionneuse du navigateur), jamais dans l'appli. On ouvre l'onglet TOUT DE SUITE (le geste
  // utilisateur est préservé, sinon le bloqueur de pop-up coupe), puis on y charge le PDF. Si le
  // serveur ne peut pas le fournir, on ferme l'onglet et on montre un message humain (jamais une
  // erreur brute — règle des deux publics).
  function ouvrirPdf() {
    const onglet = window.open('', '_blank')
    apiFetch('/api/user/referentiel/pdf', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => { if (!r.ok) throw new Error('indispo'); return r.blob() })
      .then(blob => {
        const url = URL.createObjectURL(blob)
        if (onglet) onglet.location = url
        setTimeout(() => URL.revokeObjectURL(url), 60000)
      })
      .catch(() => {
        if (onglet) onglet.close()
        showError("Le programme officiel de votre niveau n'est pas disponible pour le moment.")
      })
  }

  // « Déposer / Remplacer » : le prof envoie SON PDF (POST = put). Re-déposer REMPLACE l'ancien →
  // confirmation d'abord (jamais de perte au clic direct). Erreurs en langage humain (règle 23).
  async function deposerCahier(file, remplace) {
    if (remplace && !await demanderConfirmation({
      titre: 'Remplacer le cahier des charges ?',
      message: 'L’ancien PDF sera perdu, et aSchool s’appuiera sur le nouveau pour vos prochaines générations.',
      confirmLabel: 'Remplacer',
      danger: true,
    })) return
    setCahierBusy(true)
    const form = new FormData()
    form.append('file', file)
    // La réponse passe par lireReponse comme partout ailleurs : le message du serveur remonte
    // s'il est écrit pour le prof, sinon c'est le message serveur générique. Lue à la main,
    // elle laissait fuiter « Failed to fetch » (réseau coupé) ou « [object Object] » (un 422
    // renvoie un tableau) — le défaut même que corrige l'étape 6.
    apiFetch('/api/user/cahier', { method: 'POST', credentials: 'include', body: form }, TIMEOUT_STD)
      .then(lireReponse)
      .then(d => queryClient.setQueryData(CLE_OUVERTURE, prev => prev && ({ ...prev, cahier: d })))
      .catch(err => showError(`Le dépôt de votre cahier des charges n'a pas abouti.\n\n${messagePourEcran(err)}`))
      .finally(() => setCahierBusy(false))
  }

  // Ouvre le cahier déposé dans un nouvel onglet (même geste sûr que le PDF du programme officiel).
  function ouvrirCahier() {
    const onglet = window.open('', '_blank')
    apiFetch('/api/user/cahier/pdf', { credentials: 'include' }, TIMEOUT_STD)
      .then(r => { if (!r.ok) throw new Error('indispo'); return r.blob() })
      .then(blob => {
        const url = URL.createObjectURL(blob)
        if (onglet) onglet.location = url
        setTimeout(() => URL.revokeObjectURL(url), 60000)
      })
      .catch(() => {
        if (onglet) onglet.close()
        showError("Le cahier des charges n'est pas disponible pour le moment.")
      })
  }

  // Les TROIS lectures de l'écran, ensemble : le programme officiel du niveau (lecture seule),
  // l'état du cahier des charges, et les programmes qui remplissent les menus niveau/matière.
  // Chacune garde son sort : ce qui a répondu s'affiche, ce qui a échoué laisse sa carte en
  // « Réessayer » plutôt qu'en fausse absence. Un seul message pour le prof.
  const { data: lu, refetch } = useQuery({
    queryKey: CLE_OUVERTURE,
    queryFn: async () => {
      const [ref, cah, prog] = await Promise.allSettled([
        apiFetch('/api/user/referentiel', { credentials: 'include' }, TIMEOUT_STD).then(lireReponse),
        apiFetch('/api/user/cahier',      { credentials: 'include' }, TIMEOUT_STD).then(lireReponse),
        apiFetch('/api/programmes',       { credentials: 'include' }, TIMEOUT_STD).then(lireReponse),
      ])
      const data = prog.status === 'fulfilled' ? (prog.value || {}) : null
      return {
        refOfficiel: ref.status === 'fulfilled' ? (ref.value || { disponible: false }) : null,
        cahier:      cah.status === 'fulfilled' ? (cah.value || { present: false })    : null,
        // { disponible, fichier } / { present, fichier } ci-dessus ; les menus ci-dessous.
        niveauxParCycle:   data?.niveaux_par_cycle    || [],
        matieresParCycle:  data?.matieres_par_cycle   || [],   // repli « tout groupé » sans niveau
        matieresParNiveau: data?.matieres_par_niveau  || [],   // scope fin = programme du niveau
        languesLv:         data?.langues_lv           || [],   // catalogue des langues, LU EN BASE
        // Une panne ne se déguise JAMAIS en « aucun programme », « rien déposé » ni en menus
        // vides — c'est l'écran forcé quand le profil est incomplet, le prof y serait coincé
        // sans explication. Un message, un bouton « Réessayer ».
        raté: [ref, cah, prog].find(r => r.status === 'rejected')?.reason || null,
      }
    },
  })
  const refOfficiel       = lu?.refOfficiel ?? null
  const cahier            = lu?.cahier ?? null
  const niveauxParCycle   = lu?.niveauxParCycle || []
  const matieresParCycle  = lu?.matieresParCycle || []
  const matieresParNiveau = lu?.matieresParNiveau || []
  const languesLv         = lu?.languesLv || []
  const chargementRate    = !!lu?.raté
  const charger = () => refetch()

  useEffect(() => { if (lu?.raté) showError(messagePourEcran(lu.raté)) }, [lu?.raté])

  // Le profil hérité peut être devenu FAUX pendant que le prof n'était pas là (un référentiel
  // remplacé, un niveau retiré du programme). Ce n'est pas une correction à écrire dans le
  // formulaire après coup : le formulaire AFFICHÉ est simplement le brouillon débarrassé de ce
  // qui n'existe plus. Ce qu'on lui montre est donc toujours choisissable — et enregistrable.
  const niveauPerimé  = brouillon.niveau && niveauxParCycle.length > 0 && !niveauDisponible(niveauxParCycle, brouillon.niveau)
  const matierePerimée = !niveauPerimé && matiereIncoherente(matieresParNiveau, brouillon.niveau, brouillon.subject)
  const form = niveauPerimé  ? { ...brouillon, niveau: '', subject: '' }
             : matierePerimée ? { ...brouillon, subject: '' }
             : brouillon

  // …et on le DIT, une fois, au moment où on l'apprend — puis on emmène au champ à corriger :
  // le niveau quand c'est lui qui a disparu, la matière quand elle ne va plus avec le niveau.
  useEffect(() => {
    if (niveauPerimé)  showError(messageNiveauIndisponible(brouillon.niveau), { apres: viserNiveau })
    else if (matierePerimée) showError(messageIncoherence('ouverture', brouillon.niveau, brouillon.subject), { apres: viserMatiere })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [niveauPerimé, matierePerimée])

  // Matière en cascade sur le NIVEAU choisi (helper pur testé : utils/profil.js).
  // null = pas de niveau / niveau inconnu → on montre tout, groupé par cycle (repli).
  const matieresNiveau    = matieresDuNiveau(matieresParNiveau, form.niveau)
  const matieresAffichees = matieresNiveau ?? matieresParCycle.flatMap(g => g.matieres)
  // La matière RÉELLEMENT choisie, prise dans la liste servie par la base — c'est elle qui
  // porte `demande_langue`. Tant que les programmes ne sont pas chargés, elle est absente :
  // le champ « Langue enseignée » ne s'affiche pas, il ne s'affiche pas à tort non plus.
  const matiereChoisie    = matieresAffichees.find(m => m.nom === form.subject)
  const peutValider       = profilPretAValider(matieresParNiveau, form.niveau, form.subject)
  // Brouillon (Règle 0) : Valider/Annuler ne s'activent QUE si le formulaire diffère de ce qui
  // est enregistré (l'objet `user`). Rien touché = rien à valider ni à annuler → boutons grisés.
  const modifie =
    form.prenom    !== (user?.prenom    || '') ||
    form.nom       !== (user?.nom       || '') ||
    form.subject   !== (user?.subject   || '') ||
    form.niveau    !== (user?.niveau    || '') ||
    form.langue_lv !== (user?.langue_lv || '') ||
    form.mobile    !== (user?.mobile    || '')

  function set(field, value) {
    setForm(f => ({ ...f, [field]: value }))
  }

  // Changer de niveau peut rendre la matière incohérente (matière hors du programme du
  // nouveau niveau) → modale bloquante + matière vidée (le prof DOIT en rechoisir une).
  // (Les niveaux non disponibles ne sont pas dans la liste → impossible d'en choisir un ici.)
  //
  // LE MESSAGE DIT « choisissez la matière », L'ÉCRAN Y EMMÈNE (16/08/2026) : à la fermeture de
  // la modale, la liste des matières prend le focus et se signale en rouge jusqu'au choix. Le
  // prof lisait la consigne, puis devait chercher lui-même de quel champ elle parlait.
  function changerNiveau(value) {
    const incoherent = matiereIncoherente(matieresParNiveau, value, form.subject)
    if (incoherent) showError(messageIncoherence('changement', value, form.subject), { apres: viserMatiere })
    setForm(f => ({ ...f, niveau: value, subject: incoherent ? '' : f.subject }))
  }

  // LE RÉCAPITULATIF AVANT D'ENREGISTRER (16/08/2026). Le profil décide de tout ce que
  // l'application fabrique ensuite : on relit à voix haute ce qui va être posé, et le prof dit
  // oui. « Corriger » le ramène à son formulaire, rien n'est écrit.
  function recapitulatif() {
    const lignes = [
      ['Prénom', form.prenom],
      ['Nom', form.nom],
      ['Niveau', form.niveau],
      ['Matière', form.subject],
      ['Langue enseignée', form.langue_lv],
    ].filter(([, v]) => v)
    return lignes.map(([champ, valeur]) => `${champ} : ${valeur}`).join('\n')
  }

  async function handleValider(e) {
    e.preventDefault()
    if (!await demanderConfirmation({
      titre: 'Enregistrer ce profil ?',
      message: `${recapitulatif()}\n\nVos activités, séances et séquences seront rattachées à ce couple.`,
      confirmLabel: 'Enregistrer',
      cancelLabel: 'Corriger',
    })) return
    setSaving(true)
    try {
      const res = await apiFetch('/api/user/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(form),
      })
      // lireReponse rend le message DU SERVEUR quand il est écrit pour le prof : le contrôle
      // « cette matière n'est pas enseignée à ce niveau » (profil.py) l'atteint enfin, au lieu
      // d'être remplacé par un « Erreur lors de la sauvegarde » qui n'apprend rien.
      await lireReponse(res)
      // Relecture /auth/me après le put (jamais un recollage local) : le serveur renvoie
      // travail_matiere/travail_niveau résolus — le header et les gardes de profil suivent.
      await refreshUser()
      onNavigate('accueil')
    } catch (e) {
      showError(messagePourEcran(e))
      setSaving(false)
    }
  }

  return (
    <>
    {/* Deux cartouches CÔTE À CÔTE, alignées en haut : « Mon profil » à gauche (largeur fixe
        480), « Programme officiel » en haut à droite. Sur écran étroit, flex-wrap repasse en
        empilé (rien de tassé). */}
    <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>
    <section className="bg-white rounded border border-gray-200 p-6" style={{ maxWidth: 480, flexShrink: 0 }}>
      <div className="section-title mb-5">Mon profil<InfoGuide {...aideProfil('profil')} />{astucesProfil && <InfoGuide {...astucesProfil} />}</div>

      {/* Lecture ratée : les menus niveau/matière sont vides parce qu'on n'a pas pu les lire,
          pas parce qu'il n'y a rien. Le message est déjà en boîte de dialogue — ici, le bouton. */}
      {chargementRate && (
        <button type="button" onClick={charger} className="btn-primary mb-4"
          title="Recharger les niveaux, les matières et vos documents">
          Réessayer
        </button>
      )}

      <form onSubmit={handleValider} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Prénom</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={form.prenom}
              onChange={e => set('prenom', e.target.value)}
              placeholder="Votre prénom"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Nom</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded p-2 text-sm"
              value={form.nom}
              onChange={e => set('nom', e.target.value)}
              placeholder="Votre nom"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">E-mail</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={user?.email || ''}
            readOnly
            style={{ background: '#f8fafc', color: '#94a3b8' }}
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Mobile <span className="text-gray-400">(optionnel)</span>
          </label>
          <input
            type="tel"
            className="w-full border border-gray-300 rounded p-2 text-sm"
            value={form.mobile}
            onChange={e => set('mobile', e.target.value)}
            placeholder="06 00 00 00 00"
          />
        </div>

        {/* Niveau d'abord : il détermine le cycle, donc la liste des matières. */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Niveau par défaut</label>
          <select
            ref={refNiveau}
            aria-invalid={!!styleSignale('niveau')}
            className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
            style={styleSignale('niveau')}
            value={form.niveau}
            onChange={e => changerNiveau(e.target.value)}
          >
            <option value="">— Choisissez —</option>
            {niveauxRefDisponibles(niveauxParCycle).map(grp => (
              <optgroup key={grp.cycle} label={grp.cycle}>
                {grp.niveaux.map(n => <option key={n.id} value={n.nom}>{n.nom}</option>)}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Matière : filtrée sur le NIVEAU choisi (sinon tout, groupé par cycle). */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Matière enseignée</label>
          <select
            ref={refMatiere}
            aria-invalid={!!styleSignale('subject')}
            className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
            style={styleSignale('subject')}
            value={form.subject}
            onChange={e => set('subject', e.target.value)}
          >
            <option value="">— Choisissez —</option>
            {matieresNiveau
              ? matieresNiveau.map(m => <option key={m.id} value={m.nom}>{m.nom}</option>)
              : matieresParCycle.map(grp => (
                  <optgroup key={grp.cycle} label={grp.cycle}>
                    {grp.matieres.map(m => <option key={m.id} value={m.nom}>{m.nom}</option>)}
                  </optgroup>
                ))}
          </select>
        </div>

        {/* Langue enseignée : affichée quand la matière choisie PORTE une langue (drapeau
            `demande_langue` de la matière, envoyé par le serveur) — plus une comparaison avec
            un libellé écrit ici, que le moindre renommage de matière rendait faux. */}
        {matiereChoisie?.demande_langue && (
          <div>
            <label className="block text-xs text-gray-500 mb-1">Langue enseignée</label>
            <select
              className="w-full border border-gray-300 rounded p-2 text-sm bg-white"
              value={form.langue_lv}
              onChange={e => set('langue_lv', e.target.value)}
            >
              <option value="">— Précisez la langue —</option>
              {languesLv.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-1">
          {/* TOUJOURS ACTIF : c'est LA SORTIE de l'écran. Il était grisé tant que rien n'avait
              été modifié — sans conséquence tant que le menu restait cliquable, mais depuis que
              l'écran fige le reste de l'application, un prof qui entre ici sans rien changer
              n'avait plus aucun moyen d'en repartir. */}
          <button
            type="button"
            title="Revenir à l'accueil sans enregistrer"
            onClick={() => onNavigate('accueil')}
            className="btn-secondary"
            disabled={saving}
          >
            Annuler
          </button>
          <button
            type="submit"
            title={peutValider
              ? "Enregistrer le profil et revenir à l'accueil"
              : "Choisissez une matière correspondant à votre niveau pour pouvoir enregistrer"}
            className="btn-primary"
            disabled={saving || !peutValider || !modifie}
          >
            {saving ? 'Enregistrement…' : 'Valider'}
          </button>
        </div>
      </form>
    </section>

    {/* Colonne DROITE : deux cartouches empilées — « Programme officiel » (lecture seule) puis
        « Mon cahier des charges » (dépôt libre du prof). */}
    <div style={{ flex: 1, minWidth: 280, display: 'flex', flexDirection: 'column', gap: 16 }}>

    {/* Programme officiel de votre niveau — lecture seule (le prof consulte, il n'écrit rien) :
        le NOM EXACT du document déposé + un bouton qui OUVRE LE PDF D'ORIGINE dans un nouvel
        onglet (visionneuse du navigateur), jamais dans l'appli. */}
    <section className="bg-white rounded border border-gray-200 p-6">
      <div className="section-title mb-3">Programme officiel de votre niveau<InfoGuide {...aideProfil('programme')} /></div>
      {refOfficiel === null ? (
        chargementRate ? (
          <button type="button" onClick={charger} className="btn-secondary"
            title="Recharger le programme officiel de votre niveau">
            Réessayer
          </button>
        ) : (
          <div className="text-sm text-gray-400">Chargement…</div>
        )
      ) : refOfficiel.disponible ? (
        <div className="flex items-center justify-between gap-3">
          <span
            className="text-sm text-gray-700 truncate"
            title={refOfficiel.fichier}
            style={{ minWidth: 0 }}
          >
            {refOfficiel.fichier}
          </span>
          <button
            type="button"
            className="btn-secondary"
            style={{ flexShrink: 0 }}
            onClick={ouvrirPdf}
            title="Ouvrir le PDF d'origine dans un nouvel onglet"
          >
            Ouvrir le PDF d'origine
          </button>
        </div>
      ) : (
        <div className="text-sm text-gray-500">
          Aucun programme officiel n'est encore disponible pour votre niveau.
        </div>
      )}
    </section>

    {/* Mon cahier des charges — document interne à l'école/structure, déposé par le prof lui-même.
        Un seul PDF par prof (re-déposer remplace, avec confirmation). Le pourquoi et le texte : plus tard. */}
    <section className="bg-white rounded border border-gray-200 p-6">
      <div className="section-title mb-3">Mon cahier des charges<InfoGuide {...aideProfil('cahier')} /></div>
      {cahier === null ? (
        chargementRate ? (
          <button type="button" onClick={charger} className="btn-secondary"
            title="Recharger l'état de votre cahier des charges">
            Réessayer
          </button>
        ) : (
          <div className="text-sm text-gray-400">Chargement…</div>
        )
      ) : cahier.present ? (
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm text-gray-700 truncate" title={cahier.fichier} style={{ minWidth: 0 }}>
            {cahier.fichier}
          </span>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <button type="button" className="btn-secondary" onClick={ouvrirCahier}
              title="Ouvrir votre cahier des charges dans un nouvel onglet">
              Ouvrir
            </button>
            <label className="btn-secondary"
              style={{ cursor: cahierBusy ? 'wait' : 'pointer', opacity: cahierBusy ? 0.6 : 1, display: 'inline-flex', alignItems: 'center' }}
              title="Remplacer par un autre PDF">
              {cahierBusy ? 'Dépôt…' : 'Remplacer'}
              <input type="file" accept="application/pdf,.pdf" className="hidden" disabled={cahierBusy}
                onChange={e => { const f = e.target.files[0]; e.target.value = ''; if (f) deposerCahier(f, true) }} />
            </label>
          </div>
        </div>
      ) : (
        <div>
          <p className="text-sm text-gray-500 mb-3">
            Déposez le cahier des charges de votre établissement (PDF).
          </p>
          <label className="btn-primary"
            style={{ cursor: cahierBusy ? 'wait' : 'pointer', opacity: cahierBusy ? 0.6 : 1, display: 'inline-flex', alignItems: 'center', gap: 6 }}
            title="Choisir un PDF à déposer">
            {cahierBusy ? 'Dépôt…' : 'Déposer un PDF'}
            <input type="file" accept="application/pdf,.pdf" className="hidden" disabled={cahierBusy}
              onChange={e => { const f = e.target.files[0]; e.target.value = ''; if (f) deposerCahier(f, false) }} />
          </label>
        </div>
      )}
    </section>

    </div>
    </div>
    </>
  )
}
