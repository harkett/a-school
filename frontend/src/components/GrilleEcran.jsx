// Écran « Grille d'évaluation » — l'éditeur du TABLEAU (Mes évals → Grilles → une grille).
//
// CE QU'IL N'EST PAS. Ce n'est pas une copie d'ActiviteEcran, et c'est délibéré : cet écran-là
// montre un TEXTE dans une zone de résultat, avec un historique de versions. Une grille est un
// tableau — des colonnes, des lignes, des cases — rangé dans quatre tables. Un SplitPane
// « demande à gauche / résultat à droite » couperait le tableau en deux dans le sens de la
// largeur, c'est-à-dire là où il a le plus besoin de place.
//
// L'ÉCRITURE EST AU GESTE, et l'écran n'a donc AUCUN bouton « Enregistrer » — chaque
// modification part vers le serveur au moment où elle est faite. Les champs de texte partent au
// BLUR et non à la frappe : envoyer une requête par caractère ferait trente appels pour une
// phrase, sans rien apporter à personne. Un geste = un appel, la règle tient dans les deux sens.
//
// APRÈS CHAQUE ÉCRITURE, ON RELIT. Le serveur est l'autorité sur les identifiants, l'ordre et
// ce qu'il a accepté ; recomposer l'état à la main côté écran ferait diverger l'affichage de la
// base au premier refus (un libellé de colonne en double, par exemple).
import { useCallback, useEffect, useState } from 'react'
import JaugeAttente from './JaugeAttente.jsx'
import InfoGuide from './InfoGuide.jsx'
import { aideGrilles } from '../utils/aideGrilles.js'
import { apiFetch, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog.js'
import { demanderConfirmation } from '../confirmDialog.js'
import { ech } from '../utils/echapperHtml.js'
import { documentDepuisHtml } from '../utils/apercuHtml.js'
import ApercuHtmlModale from './ApercuHtmlModale.jsx'
import { IconGrille, IconPdf, IconPrint, IconTrash, IconWord } from './icones.jsx'
import { telechargerWord } from '../utils/exportWord.js'
import { telechargerPdf } from '../utils/exportPdf.js'

// Ce que le professeur voit quand une case est vide. Pas un blanc : un blanc ne dit pas qu'on
// peut écrire là.
const CASE_VIDE = 'Cliquez pour décrire ce niveau…'

const ETIQUETTE = {
  fontSize: 11, fontWeight: 600, color: '#94a3b8',
  textTransform: 'uppercase', letterSpacing: '0.04em',
}

// Tout ce qui vient de la grille est ÉCHAPPÉ (`ech`, utils/echapperHtml.js). Le nettoyage de
// sortie (DOMPurify, apercuHtml.js) reste le dernier filet, jamais le premier.

const COULEURS_A_L_IMPRESSION = '-webkit-print-color-adjust:exact;print-color-adjust:exact'

// LA NOTE MAXIMALE — ce que vaut une copie parfaite : pour chaque critère, le plus haut de ses
// échelons multiplié par son poids. C'est le barème de la grille, et c'est aussi la seule chose
// qui rend le poids VISIBLE : sans total, on peut le régler sans jamais voir ce qu'il change.
// Calculée ici, à une seule place, lue par l'écran ET par l'impression.
function noteMaximale(g) {
  const colonnes = g.niveaux_maitrise || []
  if (!colonnes.length) return 0
  const haut = Math.max(...colonnes.map(n => Number(n.points) || 0))
  return (g.criteres || []).reduce((total, c) => total + haut * (Number(c.poids) || 0), 0)
}

// Un nombre lisible : « 20 » et non « 20 », « 17,5 » et non « 17.5 ».
const nombre = v => Number(v).toLocaleString('fr-FR', { maximumFractionDigits: 2 })

// La grille EN PAGE — ce que le professeur imprime et pose sur sa table de correction. C'est la
// sortie qui compte : une grille qui ne s'imprime pas ne sert pas en classe.
function grilleEnHtml(g) {
  const colonnes = g.niveaux_maitrise || []
  const lignes = g.criteres || []

  const entetes = colonnes.map(n =>
    `<th style="border:1px solid #cbd5e1;padding:6px 8px;background:#f1f5f9;font-size:11px;`
    + `text-align:left;${COULEURS_A_L_IMPRESSION}">${ech(n.libelle)}`
    + `<div style="font-weight:400;color:#64748b">${ech(n.points)} pt</div></th>`).join('')

  const corps = lignes.map(c => {
    const cases = colonnes.map(n =>
      `<td style="border:1px solid #cbd5e1;padding:6px 8px;font-size:11px;vertical-align:top">`
      + `${ech((c.descripteurs || {})[String(n.id)] || '')}</td>`).join('')
    return `<tr style="page-break-inside:avoid">`
      + `<th style="border:1px solid #cbd5e1;padding:6px 8px;background:#f8fafc;font-size:11px;`
      + `text-align:left;vertical-align:top;${COULEURS_A_L_IMPRESSION}">${ech(c.libelle)}`
      + (c.poids !== 1 ? `<div style="font-weight:400;color:#64748b">× ${ech(c.poids)}</div>` : '')
      + `</th>${cases}</tr>`
  }).join('')

  return `<h1>${ech(g.titre)}</h1>`
    + (g.matiere || g.niveau
        ? `<p style="color:#64748b">${ech(g.matiere || '')}${g.matiere && g.niveau ? ' · ' : ''}${ech(g.niveau || '')}</p>`
        : '')
    + `<table style="border-collapse:collapse;width:100%;margin-top:12px">`
    + `<thead><tr><th style="border:1px solid #cbd5e1;padding:6px 8px;background:#f1f5f9;`
    + `font-size:11px;text-align:left;${COULEURS_A_L_IMPRESSION}">Critère</th>${entetes}</tr></thead>`
    + `<tbody>${corps}</tbody></table>`
    + `<p style="margin-top:12px;font-weight:700">Note maximale : ${ech(nombre(noteMaximale(g)))} points</p>`
}


// La grille EN MARKDOWN — la forme que `telechargerWord` et `telechargerPdf` savent déjà lire,
// tableau compris. Aucun troisième composeur de document n'est écrit pour cet écran : les deux
// exports de la maison prennent du markdown, la grille leur en donne.
//
// Les barres verticales des textes sont neutralisées : une seule suffirait à casser la colonne.
function grilleEnMarkdown(g) {
  const colonnes = g.niveaux_maitrise || []
  const propre = v => String(v ?? '').replace(/\|/g, '\\|').replace(/\n+/g, ' ').trim()

  const entete = ['Critère', ...colonnes.map(n => `${propre(n.libelle)} (${nombre(n.points)} pt)`)]
  const lignes = (g.criteres || []).map(c => [
    propre(c.libelle) + (Number(c.poids) !== 1 ? ` (× ${nombre(c.poids)})` : ''),
    ...colonnes.map(n => propre((c.descripteurs || {})[String(n.id)] || '')),
  ])

  const rang = cellules => `| ${cellules.join(' | ')} |`
  return `# ${propre(g.titre)}\n\n`
    + ((g.matiere || g.niveau)
        ? `${propre(g.matiere)}${g.matiere && g.niveau ? ' · ' : ''}${propre(g.niveau)}\n\n` : '')
    + (g.contexte ? `${propre(g.contexte)}\n\n` : '')
    + rang(entete) + '\n'
    + rang(entete.map(() => '---')) + '\n'
    + lignes.map(rang).join('\n') + '\n\n'
    + `**Note maximale : ${nombre(noteMaximale(g))} points**\n`
}


// Un champ qui s'écrit AU BLUR — le geste, pas la frappe. Il garde sa valeur en local le temps
// de la saisie et n'appelle `onValider` que si le texte a réellement changé : sortir d'une case
// sans y toucher ne doit pas produire d'appel.
function ChampAuBlur({ valeur, onValider, multiligne = false, placeholder = '', style = {}, ...reste }) {
  const [local, setLocal] = useState(valeur ?? '')
  useEffect(() => { setLocal(valeur ?? '') }, [valeur])

  const commun = {
    value: local,
    placeholder,
    onChange: e => setLocal(e.target.value),
    onBlur: () => { if ((local ?? '') !== (valeur ?? '')) onValider(local) },
    style: {
      width: '100%', border: '1px solid transparent', borderRadius: 4, padding: '4px 6px',
      fontFamily: 'inherit', fontSize: 12.5, color: '#374151', background: 'transparent',
      resize: 'none', ...style,
    },
    onFocus: e => { e.target.style.background = '#fff'; e.target.style.borderColor = '#cbd5e1' },
    ...reste,
  }
  // Échap remet la valeur d'avant et rend la main : on ne piège jamais le professeur dans une
  // case qu'il a commencé à modifier par erreur.
  const onKeyDown = e => {
    if (e.key === 'Escape') { setLocal(valeur ?? ''); e.target.blur() }
  }
  // `rows` et `type` sont posés AVANT l'étalement : ce sont des DÉFAUTS, et ce que l'appelant
  // passe dans `...reste` doit les remplacer. Écrits après, ils gagnaient — un champ demandé en
  // `type="number"` redevenait du texte, et « ab » tapé dans « points » s'enregistrait en 0 sans
  // que rien ne le dise.
  const finir = e => { e.target.style.background = 'transparent'; e.target.style.borderColor = 'transparent' }
  return multiligne
    ? <textarea rows={3} {...commun} onKeyDown={onKeyDown} onBlurCapture={finir} />
    : <input type="text" {...commun} onKeyDown={onKeyDown} onBlurCapture={finir} />
}


// Une flèche de déplacement. Grisée aux extrémités, avec le curseur interdit : la norme maison
// veut qu'un bouton inactif se voie ET se sente, jamais qu'il ne réponde simplement pas.
function BoutonDeplacer({ sens, vertical = false, desactive, titre, onClick }) {
  const points = vertical
    ? (sens < 0 ? '18 15 12 9 6 15' : '6 9 12 15 18 9')
    : (sens < 0 ? '15 18 9 12 15 6' : '9 18 15 12 9 6')
  return (
    <button
      type="button"
      onClick={desactive ? undefined : onClick}
      disabled={desactive}
      title={titre}
      style={{
        background: 'none', border: 'none', padding: 1, lineHeight: 0, flexShrink: 0,
        color: desactive ? '#e2e8f0' : '#94a3b8',
        cursor: desactive ? 'not-allowed' : 'pointer',
      }}
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points={points} />
      </svg>
    </button>
  )
}


export default function GrilleEcran({ grilleId, onNavigate }) {
  const [grille, setGrille] = useState(null)
  const [chargement, setChargement] = useState(true)
  const [apercu, setApercu] = useState(null)

  // ── Relire la grille : le serveur est l'autorité, l'écran ne recompose rien ──
  const relire = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/contenus/grilles/${grilleId}`, {}, TIMEOUT_STD)
      setGrille(await lireReponse(res))
    } catch (e) {
      showError(messagePourEcran(e))
    } finally {
      setChargement(false)
    }
  }, [grilleId])

  useEffect(() => { relire() }, [relire])

  // Un geste = un appel, puis on relit. Toute écriture de cet écran passe par ici : une seule
  // façon d'échouer, une seule façon de se remettre à jour.
  const geste = useCallback(async (url, methode, corps) => {
    try {
      const res = await apiFetch(url, {
        method: methode,
        headers: { 'Content-Type': 'application/json' },
        body: corps === undefined ? undefined : JSON.stringify(corps),
      }, TIMEOUT_STD)
      await lireReponse(res)
      await relire()
      return true
    } catch (e) {
      showError(messagePourEcran(e))
      await relire()          // l'écran revient à ce que la base contient vraiment
      return false
    }
  }, [relire])

  if (chargement) return <JaugeAttente libelle="Ouverture de votre grille…" />
  if (!grille) return null

  const colonnes = grille.niveaux_maitrise || []
  const lignes = grille.criteres || []

  // DÉPLACER = ÉCHANGER DEUX `ordre`, en deux appels. La donnée existait déjà (chaque PUT porte
  // son `ordre`) ; il manquait le geste. Une colonne mal placée obligeait à tout retaper.
  //
  // Les deux appels ne sont pas dans une transaction : au pire, une interruption entre les deux
  // laisse deux lignes au même rang, et le tri secondaire (`id`) les départage — l'affichage
  // reste juste, il n'y a rien à réparer.
  const deplacer = async (chemin, liste, index, sens) => {
    const cible = index + sens
    if (cible < 0 || cible >= liste.length) return
    const a = liste[index], b = liste[cible]
    const corps = x => (chemin === 'criteres'
      ? { libelle: x.libelle, poids: x.poids }
      : { libelle: x.libelle, points: x.points })
    await geste(`/api/contenus/grilles/${chemin}/${a.id}`, 'PUT', { ...corps(a), ordre: cible })
    await geste(`/api/contenus/grilles/${chemin}/${b.id}`, 'PUT', { ...corps(b), ordre: index })
  }

  // Les trois suppressions passent par le canal unique de la maison (`demanderConfirmation`),
  // jamais par un dialogue écrit ici : un seul dialogue dans l'application, une seule apparence.
  // Chacune dit CE QUI SERA PERDU — une colonne emporte une case par critère, et personne ne s'en
  // doute avant de l'avoir fait une fois.
  const supprimerGrille = async () => {
    const ok = await demanderConfirmation({
      titre: 'Supprimer cette grille ?',
      message: `« ${grille.titre} » sera supprimée, avec ses critères, ses niveaux de maîtrise et `
             + `toutes ses cases.\n\nCette action est définitive.`,
      confirmLabel: 'Supprimer', danger: true,
    })
    if (!ok) return
    if (await geste(`/api/contenus/grilles/${grille.id}`, 'DELETE')) onNavigate('eval-grilles')
  }

  const supprimerCritere = async (c) => {
    const ok = await demanderConfirmation({
      titre: 'Retirer ce critère ?',
      message: `La ligne « ${c.libelle || 'sans titre'} » sera retirée, avec les ${colonnes.length} `
             + `descripteurs qu'elle contient.`,
      confirmLabel: 'Retirer', danger: true,
    })
    if (ok) await geste(`/api/contenus/grilles/criteres/${c.id}`, 'DELETE')
  }

  const supprimerNiveau = async (n) => {
    const ok = await demanderConfirmation({
      titre: 'Retirer ce niveau de maîtrise ?',
      message: `La colonne « ${n.libelle} » sera retirée, avec le descripteur qu'elle porte sur `
             + `chacun de vos ${lignes.length} critères.`,
      confirmLabel: 'Retirer', danger: true,
    })
    if (ok) await geste(`/api/contenus/grilles/niveaux/${n.id}`, 'DELETE')
  }

  const dupliquer = async () => {
    try {
      const res = await apiFetch(`/api/contenus/grilles/${grille.id}/dupliquer`,
                                 { method: 'POST' }, TIMEOUT_STD)
      const copie = await lireReponse(res)
      onNavigate('grille', { id: copie.id })
    } catch (e) {
      showError(messagePourEcran(e))
    }
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

      {/* Barre de titre fixe — même moule que les écrans d'analyse : le titre à gauche, les
          gestes à droite, « Comment ça marche » dans le bouton du header. */}
      <div style={{
        display: 'flex', alignItems: 'center', borderBottom: '2px solid #e2e8f0',
        background: '#fff', padding: '0 24px', gap: 8, flexShrink: 0,
      }}>
        <span
          title="Votre grille d'évaluation — critères, niveaux de maîtrise et descripteurs"
          style={{ padding: '12px 16px', fontSize: 13, fontWeight: 600, color: 'var(--bordeaux)',
                   whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: 7 }}
        >
          <IconGrille taille={16} />
          Grille d'évaluation
        </span>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            type="button" className="btn-secondary" onClick={() => onNavigate('eval-grilles')}
            title="Revenir à la liste de vos grilles"
          >
            <IconGrille taille={13} />
            Mes grilles
          </button>
          <button
            type="button" className="btn-secondary" onClick={dupliquer}
            title="Créer une copie complète et indépendante de cette grille"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            Dupliquer
          </button>
          <button
            type="button" className="btn-secondary"
            onClick={() => telechargerWord(grilleEnMarkdown(grille))}
            title="Télécharger la grille au format Word .docx"
          >
            <IconWord />
            Word
          </button>
          <button
            type="button" className="btn-secondary"
            onClick={() => telechargerPdf(grilleEnMarkdown(grille))}
            title="Télécharger la grille au format PDF"
          >
            <IconPdf />
            PDF
          </button>
          <button
            type="button" className="btn-secondary"
            onClick={() => setApercu(documentDepuisHtml(grilleEnHtml(grille)))}
            title="Voir la grille mise en forme, prête à imprimer (sans quitter aSchool)"
          >
            <IconPrint />
            Imprimer
          </button>
          <button
            type="button" className="btn-secondary"
            onClick={supprimerGrille}
            title="Supprimer définitivement cette grille"
            style={{ color: '#b91c1c', borderColor: '#fecaca' }}
          >
            <IconTrash />
            Supprimer
          </button>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex',
                    flexDirection: 'column', gap: 18, minHeight: 0 }}>

        {/* ── L'en-tête : le titre, la demande, le couple ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <ChampAuBlur
            valeur={grille.titre}
            onValider={v => geste(`/api/contenus/grilles/${grille.id}`, 'PUT',
                                  { titre: v, contexte: grille.contexte || '' })}
            placeholder="Titre de la grille"
            style={{ fontSize: 18, fontWeight: 700, color: '#1e293b', padding: '6px 8px' }}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
                        fontSize: 12, color: '#64748b', paddingLeft: 8 }}>
            {(grille.matiere || grille.niveau) && (
              <span>{grille.matiere}{grille.matiere && grille.niveau ? ' · ' : ''}{grille.niveau}</span>
            )}
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: '#94a3b8' }}>
              Vos modifications sont enregistrées au fur et à mesure
              <InfoGuide {...aideGrilles('enregistrement')} />
            </span>
          </div>
        </div>

        {/* La demande d'origine — relue avant de régénérer l'année suivante. */}
        <div>
          <div style={{ ...ETIQUETTE, marginBottom: 4, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            Ce que vous évaluez
            <InfoGuide {...aideGrilles('demande')} />
          </div>
          <ChampAuBlur
            valeur={grille.contexte}
            multiligne
            onValider={v => geste(`/api/contenus/grilles/${grille.id}`, 'PUT',
                                  { titre: grille.titre, contexte: v })}
            placeholder="Un exposé oral de cinq minutes sur une œuvre…"
            style={{ background: '#f8fafc', border: '1px solid #e2e8f0', fontStyle: 'italic',
                     lineHeight: 1.6 }}
          />
        </div>

        {/* ── LE TABLEAU ── */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#1f2937',
                       display: 'inline-flex', alignItems: 'center', gap: 7 }}>
            Le tableau
            <InfoGuide {...aideGrilles('descripteur')} />
          </h2>
          <span style={{ fontSize: 12, color: '#94a3b8' }}>
            {lignes.length} critère{lignes.length > 1 ? 's' : ''} · {colonnes.length} niveau{colonnes.length > 1 ? 'x' : ''} de maîtrise
          </span>
        </div>

        {/* Le tableau défile DANS SON CADRE, jamais la page : une grille large ne doit pas
            emporter tout l'écran vers la droite. */}
        <div style={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 8,
                      background: '#fff' }}>
          <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 720 }}>
            <thead>
              <tr>
                <th style={{ border: '1px solid #e2e8f0', background: '#f8fafc', padding: '8px 10px',
                             textAlign: 'left', minWidth: 200, width: 220, verticalAlign: 'top' }}>
                  <span style={{ ...ETIQUETTE, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    Critère
                    <InfoGuide {...aideGrilles('criteres')} />
                  </span>
                </th>
                {colonnes.map((n, i) => (
                  <th key={n.id} style={{ border: '1px solid #e2e8f0', background: '#f8fafc',
                                          padding: '6px 8px', textAlign: 'left', minWidth: 170,
                                          verticalAlign: 'top' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 4 }}>
                      <ChampAuBlur
                        valeur={n.libelle}
                        onValider={v => geste(`/api/contenus/grilles/niveaux/${n.id}`, 'PUT',
                                              { libelle: v, points: n.points, ordre: n.ordre })}
                        placeholder="Niveau de maîtrise"
                        style={{ fontWeight: 600, color: '#1e293b', fontSize: 12 }}
                      />
                      <button
                        type="button"
                        onClick={() => supprimerNiveau(n)}
                        title={`Retirer la colonne « ${n.libelle} » — les cases de ce niveau seront perdues`}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2,
                                 color: '#cbd5e1', lineHeight: 0, flexShrink: 0 }}
                      >
                        <IconTrash />
                      </button>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, paddingLeft: 6 }}>
                      <span style={{ fontSize: 11, color: '#94a3b8' }}>points</span>
                      <ChampAuBlur
                        valeur={n.points}
                        type="number"
                        step="0.5"
                        onValider={v => geste(`/api/contenus/grilles/niveaux/${n.id}`, 'PUT',
                                              { libelle: n.libelle, points: Number(v) || 0, ordre: n.ordre })}
                        style={{ width: 60, fontSize: 11, color: '#64748b', padding: '2px 4px' }}
                      />
                      <BoutonDeplacer sens={-1} desactive={i === 0}
                        titre={`Déplacer « ${n.libelle} » vers la gauche`}
                        onClick={() => deplacer('niveaux', colonnes, i, -1)} />
                      <BoutonDeplacer sens={1} desactive={i === colonnes.length - 1}
                        titre={`Déplacer « ${n.libelle} » vers la droite`}
                        onClick={() => deplacer('niveaux', colonnes, i, 1)} />
                    </div>
                  </th>
                ))}
                <th style={{ border: '1px solid #e2e8f0', background: '#f8fafc', padding: '6px',
                             width: 44, verticalAlign: 'top' }}>
                  <button
                    type="button"
                    onClick={() => geste(`/api/contenus/grilles/${grille.id}/niveaux`, 'POST',
                                         { libelle: `Niveau ${colonnes.length + 1}`,
                                           // Un point de plus que la plus haute colonne : à zéro
                                           // en dur, deux ajouts donnaient deux colonnes qui ne
                                           // valaient rien et la note maximale ne bougeait pas.
                                           points: colonnes.length
                                             ? Math.max(...colonnes.map(x => Number(x.points) || 0)) + 1
                                             : 0 })}
                    className="btn-secondary"
                    title="Ajouter un niveau de maîtrise (une colonne, commune à tous les critères)"
                    style={{ padding: '4px 8px', color: '#166534', borderColor: '#bbf7d0' }}
                  >
                    +
                  </button>
                </th>
              </tr>
            </thead>

            <tbody>
              {lignes.map((c, i) => (
                <tr key={c.id}>
                  <th style={{ border: '1px solid #e2e8f0', background: '#fcfcfd', padding: '6px 8px',
                               textAlign: 'left', verticalAlign: 'top' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 4 }}>
                      <ChampAuBlur
                        valeur={c.libelle}
                        multiligne
                        onValider={v => geste(`/api/contenus/grilles/criteres/${c.id}`, 'PUT',
                                              { libelle: v, poids: c.poids, ordre: c.ordre })}
                        placeholder="Ce que l'élève doit démontrer"
                        style={{ fontWeight: 600, color: '#1e293b', fontSize: 12.5 }}
                      />
                      <button
                        type="button"
                        onClick={() => supprimerCritere(c)}
                        title={`Retirer le critère « ${c.libelle} » — ses cases seront perdues`}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2,
                                 color: '#cbd5e1', lineHeight: 0, flexShrink: 0 }}
                      >
                        <IconTrash />
                      </button>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, paddingLeft: 6 }}>
                      <span style={{ fontSize: 11, color: '#94a3b8' }}>poids ×</span>
                      <ChampAuBlur
                        valeur={c.poids}
                        type="number"
                        step="0.5"
                        onValider={v => geste(`/api/contenus/grilles/criteres/${c.id}`, 'PUT',
                                              { libelle: c.libelle, poids: Number(v) || 1, ordre: c.ordre })}
                        style={{ width: 60, fontSize: 11, color: '#64748b', padding: '2px 4px' }}
                      />
                      <BoutonDeplacer sens={-1} vertical desactive={i === 0}
                        titre={`Remonter le critère « ${c.libelle || 'sans titre'} »`}
                        onClick={() => deplacer('criteres', lignes, i, -1)} />
                      <BoutonDeplacer sens={1} vertical desactive={i === lignes.length - 1}
                        titre={`Descendre le critère « ${c.libelle || 'sans titre'} »`}
                        onClick={() => deplacer('criteres', lignes, i, 1)} />
                    </div>
                  </th>

                  {colonnes.map(n => (
                    <td key={n.id} style={{ border: '1px solid #e2e8f0', padding: 2,
                                            verticalAlign: 'top' }}>
                      <ChampAuBlur
                        valeur={(c.descripteurs || {})[String(n.id)] || ''}
                        multiligne
                        onValider={v => geste('/api/contenus/grilles/cellules', 'PUT',
                                              { critere_id: c.id, niveau_maitrise_id: n.id, descripteur: v })}
                        placeholder={CASE_VIDE}
                        style={{ lineHeight: 1.5, minHeight: 62 }}
                      />
                    </td>
                  ))}
                  <td style={{ border: '1px solid #e2e8f0', background: '#fcfcfd' }} />
                </tr>
              ))}

              {/* Une grille sans critère n'est pas une erreur : c'est une grille qu'on commence.
                  La ligne le dit, plutôt que de laisser un tableau à une seule ligne d'en-tête. */}
              {lignes.length === 0 && (
                <tr>
                  <td colSpan={colonnes.length + 2}
                      style={{ border: '1px solid #e2e8f0', padding: '28px 16px', textAlign: 'center',
                               color: '#94a3b8', fontSize: 13 }}>
                    Aucun critère pour l'instant — ajoutez le premier ci-dessous.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => geste(`/api/contenus/grilles/${grille.id}/criteres`, 'POST',
                                 { libelle: '', poids: 1 })}
            title="Ajouter un critère (une ligne du tableau)"
            style={{ color: '#166534', borderColor: '#bbf7d0' }}
          >
            + Ajouter un critère
          </button>

          {/* Le barème de la grille. Il se recalcule à chaque geste — c'est là qu'on voit le
              poids agir, et c'est ce qui manque à une grille pour servir à corriger. */}
          <span style={{ marginLeft: 'auto', fontSize: 13, color: '#1e293b' }}>
            Note maximale : <strong>{nombre(noteMaximale(grille))}</strong> points
          </span>
        </div>
      </div>

      {apercu && <ApercuHtmlModale corps={apercu} onFermer={() => setApercu(null)} />}

    </div>
  )
}
