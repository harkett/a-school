import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchWithTimeout, lireReponse, messagePourEcran, TIMEOUT_STD } from '../utils/api.js'
import { showError } from '../errorDialog'
import { demanderConfirmation } from '../confirmDialog'

// LA page « Programmes & contenu » : tout le contenu pédagogique dans UN SEUL tableau qui se
// déroule — cycle → niveau (le couple) → référentiel, matières, types d'activité (et leurs
// précisions) — ET les actions du programme officiel au même endroit (fusion de l'ancien
// écran Programmes, 30/07) : cocher les matières du programme dans le niveau déplié,
// « + Cycle » / « + Niveau » dans l'arbre, catalogue des matières (créer, activer/désactiver)
// dans son panneau. Source unique = la base : chaque affichage est un get direct, chaque
// écriture est suivie d'une RELECTURE complète (read-after-write, jamais de miroir local).
// Le référentiel, lui, se gère toujours dans l'écran Référentiel (chaîne à étapes, autre métier).

// Badge d'origine d'un type — même vérité que sur l'écran Référentiel : le lien dit qui l'a
// posé (source), le catalogue dit d'où vient le type (origine).
function BadgeType({ source, origine }) {
  const b = source === 'ia'
    ? (origine === 'ia'
        ? { texte: 'IA', bg: '#f3e8ff', fg: '#7e22ce' }
        : { texte: 'SYSTÈME · IA', bg: '#e0f2fe', fg: '#0369a1' })
    : source === 'admin'
      ? { texte: 'ADMIN', bg: '#e0e7ff', fg: '#4338ca' }
      : { texte: 'SYSTÈME', bg: '#f1f5f9', fg: '#64748b' }
  return (
    <span style={{ marginLeft: 8, padding: '1px 7px', borderRadius: 4, fontSize: 10, fontWeight: 600, background: b.bg, color: b.fg, whiteSpace: 'nowrap' }}>
      {b.texte}
    </span>
  )
}

// Pastille d'état compacte (référentiel : PDF, épuré, découpe…).
function Etat({ ok, texte }) {
  return (
    <span style={{
      padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap',
      background: ok ? '#dcfce7' : '#f1f5f9', color: ok ? '#16a34a' : '#94a3b8',
    }}>{texte}</span>
  )
}

const CHEVRON = (ouvert) => (
  <span aria-hidden="true" style={{
    display: 'inline-block', width: 14, fontSize: 10, color: '#94a3b8',
    transform: ouvert ? 'rotate(90deg)' : 'none', transition: 'transform 0.12s',
  }}>▶</span>
)

// Styles partagés des petites rangées d'ajout (mêmes que l'ex-écran Programmes).
const CHAMP_AJOUT = { flex: 1, minWidth: 0, border: '1px solid #d1d5db', borderRadius: 6, padding: '6px 8px', fontSize: 12 }
const btnAjout = (busy) => ({
  whiteSpace: 'nowrap', fontSize: 12, fontWeight: 600, padding: '6px 10px', borderRadius: 6,
  border: '1px solid #cbd5e1', background: '#f8fafc', color: '#334155', cursor: busy ? 'wait' : 'pointer',
})

export default function AdminContenu() {
  const [cycles, setCycles]       = useState([])   // arbre contenu (référentiel, matières du programme, types)
  const [catalogue, setCatalogue] = useState([])   // TOUTES les matières (inactives incluses)
  const [paires, setPaires]       = useState([])   // paires matière × niveau (état actif)
  const [loading, setLoading] = useState(true)
  const [panne, setPanne]     = useState(false)    // lecture échouée (réseau/serveur)
  const [busy, setBusy]       = useState(false)    // une écriture (et sa relecture) est en cours
  const [nivOuverts, setNivOuverts] = useState(() => new Set())      // niveaux dépliés
  const [typesOuverts, setTypesOuverts] = useState(() => new Set())  // `${niveauId}|${typeId}` → précisions dépliées
  const navigate = useNavigate()

  // Lecture COMPLÈTE en base : l'arbre (contenu) + le programme (catalogue matières, paires).
  // Une panne (réseau, serveur) n'affiche JAMAIS le faux « Aucun cycle en base. » : erreur en
  // modale (règle maison) et l'écran ne garde qu'un bouton « Réessayer ».
  async function recharger() {
    try {
      const [rc, rp] = await Promise.all([
        fetchWithTimeout('/api/admin/contenu',    { credentials: 'include' }, TIMEOUT_STD),
        fetchWithTimeout('/api/admin/programmes', { credentials: 'include' }, TIMEOUT_STD),
      ])
      if (rc.status === 401 || rp.status === 401) { navigate('/admin/login'); return }
      const [contenu, prog] = await Promise.all([lireReponse(rc), lireReponse(rp)])
      setCycles(contenu.cycles || [])
      setCatalogue(prog.matieres || [])
      setPaires(prog.paires || [])
      setPanne(false)
    } catch (err) {
      setPanne(true)
      showError(messagePourEcran(err))
    }
  }

  useEffect(() => { recharger().finally(() => setLoading(false)) }, [])  // eslint-disable-line react-hooks/exhaustive-deps

  // Enveloppe commune des écritures : écrit, montre l'erreur en modale, puis RELIT la base
  // (read-after-write — succès OU échec, l'écran raconte toujours l'état réel des tables).
  async function ecrire(action) {
    setBusy(true)
    let ok = false
    try { await action(); ok = true }
    catch (err) { showError(messagePourEcran(err)) }
    finally {
      await recharger()
      setBusy(false)
    }
    return ok
  }

  function togglePaire(matiere_id, niveau_id, actif) {
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/programmes/paire', {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matiere_id, niveau_id, actif }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  function creerCycle(nom) {
    const n = (nom || '').trim()
    if (!n) { showError('Indiquez le nom du cycle.'); return Promise.resolve(false) }
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/cycles', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom: n }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  function creerNiveau(cycle_id, nom) {
    const n = (nom || '').trim()
    if (!n) { showError('Indiquez le nom du niveau.'); return Promise.resolve(false) }
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/niveaux', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cycle_id, nom: n }),
      }, TIMEOUT_STD)
      const d = await lireReponse(r)
      // Le niveau tout neuf s'ouvre : on voit tout de suite où cocher ses matières.
      setNivOuverts(prev => { const s = new Set(prev); s.add(d.id); return s })
    })
  }

  function creerMatiere(nom) {
    const n = (nom || '').trim()
    if (!n) { showError('Indiquez le nom de la matière.'); return Promise.resolve(false) }
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/matieres', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom: n }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  async function toggleMatiere(m) {
    if (m.actif && !await demanderConfirmation({
      titre: `Désactiver la matière « ${m.nom} » ?`,
      message: "Elle disparaîtra des menus des profs et ne sera plus cochable dans les programmes.\n\nDésactivation réversible : rien n'est supprimé, son historique et ses paires restent en base.",
      confirmLabel: 'Désactiver',
    })) return false
    return ecrire(async () => {
      const r = await fetchWithTimeout('/api/admin/matieres/actif', {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matiere_id: m.id, actif: !m.actif }),
      }, TIMEOUT_STD)
      await lireReponse(r)
    })
  }

  function basculerNiveau(id) {
    setNivOuverts(prev => {
      const s = new Set(prev)
      if (s.has(id)) s.delete(id); else s.add(id)
      return s
    })
  }
  function basculerType(cle) {
    setTypesOuverts(prev => {
      const s = new Set(prev)
      if (s.has(cle)) s.delete(cle); else s.add(cle)
      return s
    })
  }

  function paireActive(matiere_id, niveau_id) {
    const p = paires.find(p => p.matiere_id === matiere_id && p.niveau_id === niveau_id)
    return !!(p && p.actif)
  }

  if (loading) return <p className="text-sm text-gray-400 p-6">Chargement…</p>

  // Panne de lecture : l'erreur est déjà passée en modale ; l'écran ne garde que « Réessayer ».
  if (panne) return (
    <div style={{ textAlign: 'center', padding: '3rem' }}>
      <button
        type="button"
        onClick={() => { setLoading(true); recharger().finally(() => setLoading(false)) }}
        title="Relancer la lecture du contenu pédagogique"
        style={{ padding: '9px 24px', borderRadius: 8, border: '1px solid #cbd5e1',
                 background: '#fff', color: '#334155', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}
      >
        Réessayer
      </button>
    </div>
  )

  const nbNiveaux = cycles.reduce((n, c) => n + c.niveaux.length, 0)
  const matieresActives = catalogue.filter(m => m.actif)

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-3">
        <h2 className="text-sm font-semibold text-gray-700">Programmes &amp; contenu</h2>
        <span className="text-xs text-gray-400">
          {cycles.length} cycle{cycles.length > 1 ? 's' : ''} · {nbNiveaux} niveau{nbNiveaux > 1 ? 'x' : ''} · {matieresActives.length} matière{matieresActives.length > 1 ? 's' : ''}
        </span>
      </div>

      <p className="text-xs text-gray-500 mb-3" style={{ maxWidth: 760, lineHeight: 1.5 }}>
        Tout le contenu pédagogique, lu en direct dans la base — et le programme officiel se règle
        ici même : dépliez un niveau pour <b>cocher ses matières</b>, ajoutez cycles et niveaux
        directement dans l'arbre, gérez le catalogue dans le panneau <b>Matières</b>. Décocher ou
        désactiver <b>désactive</b> (l'historique reste intact, rien n'est supprimé). Seul le
        référentiel se gère ailleurs : écran <b>Référentiel</b>.
      </p>

      <MatieresPanel
        catalogue={catalogue}
        busy={busy}
        onCreer={creerMatiere}
        onToggle={toggleMatiere}
      />

      <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <tbody>
            {cycles.length === 0 && (
              <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td colSpan={2} style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8', fontSize: 13 }}>
                  Aucun cycle en base.
                </td>
              </tr>
            )}
            {cycles.map(cycle => (
              <CycleBloc
                key={cycle.id}
                cycle={cycle}
                matieresActives={matieresActives}
                paireActive={paireActive}
                busy={busy}
                nivOuverts={nivOuverts}
                typesOuverts={typesOuverts}
                basculerNiveau={basculerNiveau}
                basculerType={basculerType}
                onTogglePaire={togglePaire}
                onCreerNiveau={creerNiveau}
              />
            ))}
            <AjoutCycleRow busy={busy} onCreer={creerCycle} />
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Panneau « Matières » : le catalogue (créer, activer/désactiver) — SA cartouche, SON état. ──
function MatieresPanel({ catalogue, busy, onCreer, onToggle }) {
  const [ouvert, setOuvert] = useState(false)
  const [nom, setNom] = useState('')
  const inactives = catalogue.filter(m => !m.actif)

  async function creer() {
    const ok = await onCreer(nom)
    if (ok) setNom('')
  }

  return (
    <div style={{ background: 'white', borderRadius: 10, border: '1px solid #e2e8f0', overflow: 'hidden', marginBottom: 12 }}>
      <button
        type="button"
        onClick={() => setOuvert(o => !o)}
        title={ouvert ? 'Replier le catalogue des matières' : 'Déplier le catalogue des matières (créer, activer, désactiver)'}
        style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%', textAlign: 'left',
                 border: 'none', background: ouvert ? '#fcfdff' : 'white', cursor: 'pointer',
                 padding: '10px 16px', fontSize: 13 }}
      >
        {CHEVRON(ouvert)}
        <span style={{ fontWeight: 600, color: '#1e293b' }}>Matières</span>
        <span style={{ fontSize: 11, color: '#94a3b8' }}>
          {catalogue.length - inactives.length} active{catalogue.length - inactives.length > 1 ? 's' : ''}
          {inactives.length > 0 && <> · {inactives.length} inactive{inactives.length > 1 ? 's' : ''}</>}
        </span>
      </button>

      {ouvert && (
        <div style={{ padding: '4px 16px 14px', borderTop: '1px solid #f1f5f9', background: '#fcfdff' }}>
          <p style={{ margin: '8px 0 10px', fontSize: 11.5, color: '#94a3b8' }}>
            Le catalogue complet. Désactiver retire la matière des menus des profs — réversible,
            rien n'est supprimé. Cocher où elle s'enseigne se fait niveau par niveau, dans l'arbre dessous.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {catalogue.length === 0 && (
              <span style={{ fontSize: 12.5, color: '#94a3b8' }}>Aucune matière en base.</span>
            )}
            {catalogue.map(m => (
              <span
                key={m.id}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '3px 10px',
                         borderRadius: 6, fontSize: 12, border: '1px solid #e2e8f0',
                         background: m.actif ? '#f1f5f9' : '#fff',
                         color: m.actif ? '#334155' : '#94a3b8' }}
              >
                {m.nom}{!m.actif && <span style={{ fontSize: 10 }}>(inactive)</span>}
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onToggle(m)}
                  title={m.actif
                    ? `Désactiver « ${m.nom} » (réversible : historique et paires conservés)`
                    : `Réactiver « ${m.nom} » : elle redevient cochable et réapparaît chez les profs`}
                  style={{ border: 'none', background: 'none', padding: 0, fontSize: 11, fontWeight: 600,
                           color: m.actif ? '#A63045' : '#16a34a', cursor: busy ? 'wait' : 'pointer' }}
                >
                  {m.actif ? 'désactiver' : 'réactiver'}
                </button>
              </span>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 12, maxWidth: 420 }}>
            <input
              style={CHAMP_AJOUT} value={nom} disabled={busy}
              placeholder="Nom de la matière…" title="Nom de la nouvelle matière (ex. Philosophie)"
              onChange={e => setNom(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') creer() }}
            />
            <button type="button" style={btnAjout(busy)} onClick={creer} disabled={busy}
              title="Créer cette matière (active d'emblée ; cochez ensuite ses niveaux dans l'arbre)">+ Matière</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Rangée « + Cycle » en pied d'arbre — SA cartouche, SON état. ──
function AjoutCycleRow({ busy, onCreer }) {
  const [nom, setNom] = useState('')

  async function creer() {
    const ok = await onCreer(nom)
    if (ok) setNom('')
  }

  return (
    <tr>
      <td colSpan={2} style={{ padding: '10px 16px', background: '#f8fafc' }}>
        <div style={{ display: 'flex', gap: 6, maxWidth: 420 }}>
          <input
            style={CHAMP_AJOUT} value={nom} disabled={busy}
            placeholder="Nom du cycle…" title="Nom du nouveau cycle (ex. CAP)"
            onChange={e => setNom(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') creer() }}
          />
          <button type="button" style={btnAjout(busy)} onClick={creer} disabled={busy}
            title="Créer ce cycle (il apparaît dans l'arbre, prêt à recevoir ses niveaux)">+ Cycle</button>
        </div>
      </td>
    </tr>
  )
}

// ── Rangée « + Niveau » d'un cycle — SA cartouche, SON état. ──
function AjoutNiveauRow({ cycle, busy, onCreer }) {
  const [nom, setNom] = useState('')

  async function creer() {
    const ok = await onCreer(cycle.id, nom)
    if (ok) setNom('')
  }

  return (
    <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
      <td colSpan={2} style={{ padding: '6px 16px 10px 40px' }}>
        <div style={{ display: 'flex', gap: 6, maxWidth: 420 }}>
          <input
            style={CHAMP_AJOUT} value={nom} disabled={busy}
            placeholder={`Nom du niveau dans « ${cycle.nom} »…`}
            title="Nom du nouveau niveau de ce cycle (ex. CAP Cuisine)"
            onChange={e => setNom(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') creer() }}
          />
          <button type="button" style={btnAjout(busy)} onClick={creer} disabled={busy}
            title="Créer ce niveau dans ce cycle (il s'ouvre aussitôt pour cocher ses matières)">+ Niveau</button>
        </div>
      </td>
    </tr>
  )
}

function CycleBloc({ cycle, matieresActives, paireActive, busy, nivOuverts, typesOuverts,
                     basculerNiveau, basculerType, onTogglePaire, onCreerNiveau }) {
  return (
    <>
      {/* ─ Ligne CYCLE ─ */}
      <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
        <td colSpan={2} style={{ padding: '10px 16px' }}>
          <span style={{ fontWeight: 700, color: '#1e293b', fontSize: 13.5 }}>{cycle.nom}</span>
          <span style={{ marginLeft: 10, fontSize: 11, color: '#94a3b8' }}>
            {cycle.niveaux.length} niveau{cycle.niveaux.length > 1 ? 'x' : ''}
          </span>
        </td>
      </tr>

      {cycle.niveaux.length === 0 && (
        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
          <td colSpan={2} style={{ padding: '8px 16px 8px 40px', color: '#94a3b8', fontSize: 12.5 }}>
            Aucun niveau dans ce cycle.
          </td>
        </tr>
      )}

      {cycle.niveaux.map(niveau => (
        <NiveauBloc
          key={niveau.id}
          niveau={niveau}
          ref_={niveau.referentiel}
          ouvert={nivOuverts.has(niveau.id)}
          matieresActives={matieresActives}
          paireActive={paireActive}
          busy={busy}
          typesOuverts={typesOuverts}
          basculerNiveau={basculerNiveau}
          basculerType={basculerType}
          onTogglePaire={onTogglePaire}
        />
      ))}

      <AjoutNiveauRow cycle={cycle} busy={busy} onCreer={onCreerNiveau} />
    </>
  )
}

function NiveauBloc({ niveau, ref_, ouvert, matieresActives, paireActive, busy,
                      typesOuverts, basculerNiveau, basculerType, onTogglePaire }) {
  // Variantes lues dans l'arbre (paires actives du niveau) : affichées sur la case cochée.
  const variantes = {}
  for (const m of niveau.matieres) {
    if (m.variante) (variantes[m.id] = variantes[m.id] || []).push(m.variante)
  }

  return (
    <>
      {/* ─ Ligne NIVEAU (cliquable) ─ */}
      <tr
        onClick={() => basculerNiveau(niveau.id)}
        style={{ borderBottom: '1px solid #f1f5f9', cursor: 'pointer', background: ouvert ? '#fcfdff' : 'white' }}
      >
        <td style={{ padding: '9px 16px 9px 28px', whiteSpace: 'nowrap' }}>
          {CHEVRON(ouvert)}
          <span style={{ fontWeight: 600, color: '#1e293b', marginLeft: 4 }}>{niveau.nom}</span>
        </td>
        <td style={{ padding: '9px 16px', textAlign: 'right' }}>
          {ref_ === null ? (
            <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: '#fef3c7', color: '#b45309', whiteSpace: 'nowrap' }}>
              vide — à remplir
            </span>
          ) : (
            <span style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <Etat ok texte="PDF déposé" />
              <Etat ok={ref_.epure} texte={ref_.epure ? 'texte épuré' : 'épuré manquant'} />
              <Etat ok={ref_.decoupe_valide} texte={ref_.decoupe_valide ? 'découpe validée' : 'découpe en cours'} />
              <span style={{ fontSize: 11, color: '#64748b', alignSelf: 'center', whiteSpace: 'nowrap' }}>
                {ref_.nb_unites} unité{ref_.nb_unites > 1 ? 's' : ''} · {niveau.matieres.length} matière{niveau.matieres.length > 1 ? 's' : ''} · {niveau.types.length} type{niveau.types.length > 1 ? 's' : ''}
              </span>
            </span>
          )}
        </td>
      </tr>

      {/* ─ Détail du niveau (déplié) ─ */}
      {ouvert && (
        <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
          <td colSpan={2} style={{ padding: '4px 16px 14px 52px', background: '#fcfdff' }}>

            {/* Provenance du référentiel */}
            {ref_ !== null && (ref_.source || ref_.date_doc) && (
              <p style={{ margin: '8px 0 0', fontSize: 11.5, color: '#94a3b8' }}>
                {ref_.source ? <>Source : {ref_.source}</> : null}
                {ref_.source && ref_.date_doc ? ' · ' : null}
                {ref_.date_doc ? <>Document daté : {ref_.date_doc}</> : null}
              </p>
            )}

            {/* Matières du programme : cases à cocher sur le catalogue actif — décocher DÉSACTIVE
                la paire (l'historique reste). Après chaque coche : PATCH puis relecture en base. */}
            <p style={{ margin: '12px 0 6px', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Matières au programme ({niveau.matieres.length})
            </p>
            {matieresActives.length === 0 ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>
                Aucune matière active au catalogue — créez-la dans le panneau « Matières » ci-dessus.
              </p>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {matieresActives.map(m => {
                  const coche = paireActive(m.id, niveau.id)
                  return (
                    <label
                      key={m.id}
                      title={`${m.nom} en ${niveau.nom} : ${coche ? 'enseignée (décocher pour désactiver — réversible)' : 'non enseignée (cocher pour l’ajouter au programme)'}`}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '3px 10px',
                               borderRadius: 6, fontSize: 12, cursor: busy ? 'wait' : 'pointer',
                               background: coche ? '#f0fdf4' : '#fff',
                               border: `1px solid ${coche ? '#bbf7d0' : '#e2e8f0'}`,
                               color: coche ? '#166534' : '#64748b' }}
                    >
                      <input
                        type="checkbox"
                        checked={coche}
                        disabled={busy}
                        onChange={() => onTogglePaire(m.id, niveau.id, !coche)}
                        style={{ cursor: busy ? 'wait' : 'pointer', width: 13, height: 13 }}
                      />
                      {m.nom}{coche && variantes[m.id] ? ` (${variantes[m.id].join(', ')})` : ''}
                    </label>
                  )
                })}
              </div>
            )}

            {/* Types d'activité du couple */}
            <p style={{ margin: '14px 0 6px', fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Types d'activité ({niveau.types.length})
            </p>
            {ref_ === null ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Pas encore de référentiel : aucun type d'activité rattaché.</p>
            ) : niveau.types.length === 0 ? (
              <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8' }}>Aucun type d'activité rattaché à ce couple pour le moment.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {niveau.types.map(t => {
                  const cle = `${niveau.id}|${t.id}`
                  const tOuvert = typesOuverts.has(cle)
                  return (
                    <div key={t.id}>
                      <button
                        onClick={() => basculerType(cle)}
                        style={{
                          display: 'inline-flex', alignItems: 'center', cursor: 'pointer',
                          border: 'none', background: 'none', padding: '3px 0', fontSize: 12.5,
                          color: '#1e293b', textAlign: 'left',
                        }}
                      >
                        {CHEVRON(tOuvert)}
                        <span style={{ fontWeight: 500, marginLeft: 4 }}>{t.label}</span>
                        <BadgeType source={t.source} origine={t.origine} />
                        <span style={{ marginLeft: 8, fontSize: 11, color: '#94a3b8' }}>
                          {t.precisions.length} précision{t.precisions.length > 1 ? 's' : ''}
                        </span>
                      </button>
                      {tOuvert && (
                        t.precisions.length === 0 ? (
                          <p style={{ margin: '2px 0 4px 34px', fontSize: 12, color: '#94a3b8' }}>Aucune précision pour ce type d'activité sur ce couple.</p>
                        ) : (
                          <ul style={{ margin: '2px 0 4px 34px', padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {t.precisions.map((p, i) => (
                              <li key={i} style={{ fontSize: 12, color: '#475569' }}>· {p}</li>
                            ))}
                          </ul>
                        )
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}
