import { useEffect, useState } from 'react'

const STATUT_LABELS = {
  brouillon:  { label: 'Brouillon',  bg: '#f1f5f9', color: '#64748b' },
  publie:     { label: 'Publié',     bg: '#dcfce7', color: '#16a34a' },
  a_reviser:  { label: 'À réviser', bg: '#fff7ed', color: '#d97706' },
}

export default function AdminFiches() {
  const [liste, setListe]         = useState(null)
  const [selected, setSelected]   = useState(null)  // matiere string
  const [fiche, setFiche]         = useState(null)
  const [saving, setSaving]       = useState(false)
  const [generating, setGenerating] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [msg, setMsg]             = useState(null)
  const [erreur, setErreur]       = useState(null)

  function flash(text, isErr = false) {
    if (isErr) setErreur(text)
    else setMsg(text)
    setTimeout(() => { setMsg(null); setErreur(null) }, 3500)
  }

  useEffect(() => {
    fetch('/api/admin/fiches', { credentials: 'include' })
      .then(r => r.json())
      .then(setListe)
      .catch(() => flash('Impossible de charger les fiches.', true))
  }, [])

  function openFiche(matiere) {
    setSelected(matiere)
    setFiche(null)
    fetch(`/api/admin/fiches/${encodeURIComponent(matiere)}`, { credentials: 'include' })
      .then(r => r.json())
      .then(setFiche)
      .catch(() => flash('Impossible de charger la fiche.', true))
  }

  async function save() {
    setSaving(true)
    try {
      const r = await fetch(`/api/admin/fiches/${encodeURIComponent(selected)}`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          statut:        fiche.statut,
          accroche:      fiche.accroche,
          pour_qui:      fiche.pour_qui,
          ameliorations: fiche.ameliorations,
        }),
      })
      if (!r.ok) throw new Error()
      setListe(l => l.map(f => f.matiere === selected
        ? { ...f, statut: fiche.statut, has_content: !!fiche.accroche }
        : f
      ))
      flash('Fiche sauvegardée.')
    } catch {
      flash('Erreur lors de la sauvegarde.', true)
    } finally {
      setSaving(false)
    }
  }

  async function generer() {
    setGenerating(true)
    try {
      const r = await fetch(`/api/admin/fiches/${encodeURIComponent(selected)}/generer`, {
        method: 'POST',
        credentials: 'include',
      })
      if (!r.ok) throw new Error()
      const data = await r.json()
      setFiche(f => ({ ...f, ...data, statut: 'brouillon' }))
      setListe(l => l.map(f => f.matiere === selected ? { ...f, has_content: true } : f))
      flash('Contenu généré — vérifiez et sauvegardez.')
    } catch {
      flash('Erreur lors de la génération.', true)
    } finally {
      setGenerating(false)
    }
  }

  function preview() {
    setShowPreview(true)
  }

  if (!liste) return <p className="text-gray-400 text-sm">Chargement…</p>

  return (
    <div className="flex flex-col gap-6">

      {/* Titre */}
      <div>
        <h2 className="text-base font-semibold text-gray-800">Fiches matières</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Documents de présentation aSchool par matière — consultez, modifiez, générez automatiquement.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Matières',  val: liste.length },
          { label: 'Publiées',  val: liste.filter(f => f.statut === 'publie').length },
          { label: 'Brouillons', val: liste.filter(f => f.statut === 'brouillon').length },
        ].map(({ label, val }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: '#1a3a6e' }}>{val}</div>
            <div className="text-xs text-gray-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-5" style={{ alignItems: 'flex-start' }}>

        {/* Liste des matières */}
        <div style={{ width: 220, flexShrink: 0 }}>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {liste.map((f, i) => {
              const s = STATUT_LABELS[f.statut] || STATUT_LABELS.brouillon
              const isActive = selected === f.matiere
              return (
                <button
                  key={f.matiere}
                  onClick={() => openFiche(f.matiere)}
                  title={`${f.nb_activites} activités disponibles`}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    background: isActive ? '#eff6ff' : 'transparent',
                    borderBottom: i < liste.length - 1 ? '1px solid #f1f5f9' : 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textAlign: 'left',
                    borderLeft: isActive ? '3px solid #1a3a6e' : '3px solid transparent',
                  }}
                >
                  <div>
                    <div style={{ fontSize: 13, fontWeight: isActive ? 600 : 500, color: '#1e293b' }}>
                      {f.matiere}
                    </div>
                    <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 1 }}>
                      {f.nb_activites} activités
                    </div>
                  </div>
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: '2px 7px',
                    borderRadius: 99, background: s.bg, color: s.color,
                    whiteSpace: 'nowrap',
                  }}>
                    {s.label}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Éditeur */}
        <div style={{ flex: 1 }}>
          {!selected && (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400 text-sm">
              Sélectionnez une matière pour consulter ou modifier sa fiche.
            </div>
          )}

          {selected && !fiche && (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400 text-sm">
              Chargement…
            </div>
          )}

          {selected && fiche && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">

              {/* Header éditeur */}
              <div style={{ padding: '14px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: '#1e293b' }}>{selected}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>{fiche.nb_activites} activités disponibles pour cette matière</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <select
                    value={fiche.statut}
                    onChange={e => setFiche(f => ({ ...f, statut: e.target.value }))}
                    title="Statut de la fiche"
                    style={{ fontSize: 12, padding: '5px 8px', borderRadius: 6, border: '1px solid #e2e8f0', color: '#374151', cursor: 'pointer' }}
                  >
                    <option value="brouillon">Brouillon</option>
                    <option value="publie">Publié</option>
                    <option value="a_reviser">À réviser</option>
                  </select>
                  <button
                    onClick={generer}
                    disabled={generating}
                    title="Générer automatiquement le contenu via aSchool (Groq)"
                    style={{
                      padding: '6px 14px', borderRadius: 6, border: '1px solid #a78bfa',
                      background: generating ? '#f5f3ff' : '#ede9fe', color: '#6b21a8',
                      fontSize: 12, fontWeight: 600, cursor: generating ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {generating ? 'Génération…' : 'Générer auto'}
                  </button>
                  <button
                    onClick={preview}
                    title="Prévisualiser la fiche en HTML (nouvel onglet)"
                    style={{
                      padding: '6px 14px', borderRadius: 6, border: '1px solid #bfdbfe',
                      background: '#eff6ff', color: '#1d4ed8',
                      fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    }}
                  >
                    Prévisualiser
                  </button>
                  <button
                    onClick={save}
                    disabled={saving}
                    title="Sauvegarder les modifications"
                    style={{
                      padding: '6px 14px', borderRadius: 6, border: 'none',
                      background: saving ? '#93c5fd' : '#1a3a6e', color: 'white',
                      fontSize: 12, fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {saving ? 'Sauvegarde…' : 'Sauvegarder'}
                  </button>
                </div>
              </div>

              {/* Messages */}
              {msg && (
                <div style={{ margin: '10px 20px 0', padding: '8px 12px', background: '#dcfce7', color: '#166534', borderRadius: 6, fontSize: 12 }}>
                  {msg}
                </div>
              )}
              {erreur && (
                <div style={{ margin: '10px 20px 0', padding: '8px 12px', background: '#fee2e2', color: '#991b1b', borderRadius: 6, fontSize: 12 }}>
                  {erreur}
                </div>
              )}

              {/* Champs */}
              <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 18 }}>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 5 }}>
                    Accroche
                    <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6 }}>2-3 phrases percutantes pour les profs de {selected}</span>
                  </label>
                  <textarea
                    value={fiche.accroche}
                    onChange={e => setFiche(f => ({ ...f, accroche: e.target.value }))}
                    rows={3}
                    placeholder={`Vous enseignez ${selected} ? aSchool génère vos activités pédagogiques en quelques secondes…`}
                    style={{
                      width: '100%', padding: '10px 12px', fontSize: 13, borderRadius: 6,
                      border: '1px solid #e2e8f0', resize: 'vertical', lineHeight: 1.5, color: '#1e293b',
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 5 }}>
                    Pour qui ?
                    <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6 }}>Une ligne par profil (appuyez sur Entrée entre chaque)</span>
                  </label>
                  <textarea
                    value={fiche.pour_qui}
                    onChange={e => setFiche(f => ({ ...f, pour_qui: e.target.value }))}
                    rows={4}
                    placeholder={`Professeurs de ${selected} du collège et du lycée\nFormateurs cherchant des supports adaptés par niveau\n…`}
                    style={{
                      width: '100%', padding: '10px 12px', fontSize: 13, borderRadius: 6,
                      border: '1px solid #e2e8f0', resize: 'vertical', lineHeight: 1.5, color: '#1e293b',
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 5 }}>
                    Ce qui arrive bientôt
                    <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 6 }}>Améliorations futures (une par ligne, commencez par "- ")</span>
                  </label>
                  <textarea
                    value={fiche.ameliorations}
                    onChange={e => setFiche(f => ({ ...f, ameliorations: e.target.value }))}
                    rows={4}
                    placeholder="- Quiz interactifs élèves projetables en classe&#10;- Partage d'activités entre collègues&#10;- Application mobile (PWA)&#10;- Intégration ENT (Pronote)"
                    style={{
                      width: '100%', padding: '10px 12px', fontSize: 13, borderRadius: 6,
                      border: '1px solid #e2e8f0', resize: 'vertical', lineHeight: 1.5, color: '#1e293b',
                    }}
                  />
                </div>

                {fiche.updated_at && (
                  <p style={{ fontSize: 10, color: '#94a3b8', textAlign: 'right' }}>
                    Dernière modification : {new Date(fiche.updated_at).toLocaleString('fr-FR')}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      {showPreview && selected && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={e => { if (e.target === e.currentTarget) setShowPreview(false) }}
        >
          <div style={{ background: '#fff', borderRadius: 10, width: '90vw', maxWidth: 900, height: '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', boxShadow: '0 16px 48px rgba(0,0,0,0.25)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', flexShrink: 0 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>
                Prévisualisation — {selected}
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                <a
                  href={`/api/fiches/${encodeURIComponent(selected)}`}
                  download={`aSchool_${selected}.html`}
                  title="Télécharger la fiche (HTML imprimable)"
                  style={{ padding: '6px 14px', borderRadius: 6, border: '1px solid #bfdbfe', background: '#eff6ff', color: '#1d4ed8', fontSize: 12, fontWeight: 600, textDecoration: 'none' }}
                >
                  Télécharger
                </a>
                <button
                  onClick={() => setShowPreview(false)}
                  title="Fermer"
                  style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #e2e8f0', background: '#f8fafc', color: '#64748b', fontSize: 18, lineHeight: 1, cursor: 'pointer' }}
                >
                  ×
                </button>
              </div>
            </div>
            <iframe
              src={`/api/fiches/${encodeURIComponent(selected)}`}
              title={`Fiche aSchool ${selected}`}
              style={{ flex: 1, border: 'none', width: '100%' }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
