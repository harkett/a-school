import { useState, useEffect } from 'react'

const TIPS = [
  {
    texte: 'Si votre navigateur propose de traduire cette page, choisissez « Ne jamais traduire ce site ». La traduction automatique perturbe la génération des activités.',
    lien: { label: 'Pourquoi ?' },
    modal: {
      titre: 'Pourquoi ne pas traduire la page ?',
      lignes: [
        'La traduction automatique modifie le texte source et les consignes — aSchool reçoit alors des mots incorrects et génère des activités incohérentes ou vides.',
        'La page aSchool est entièrement en français : la traduction n\'apporte rien et perturbe tout.',
        '— Edge : cliquez sur l\'icône de traduction dans la barre d\'adresse → « Ne jamais traduire ce site ».',
      ],
    },
  },
  {
    texte: 'aSchool apprend votre style : plus vous sauvegardez d\'activités du même type, plus il s\'adapte à votre façon d\'enseigner.',
    lien: { label: 'En savoir plus' },
    modal: {
      titre: 'Comment aSchool apprend votre style ?',
      lignes: [
        'À chaque sauvegarde, aSchool conserve votre activité comme exemple.',
        'À partir de la 3ème sauvegarde d\'un même type, il s\'en inspire automatiquement pour adapter le ton, la formulation des questions et le niveau de langue.',
        'Cela fonctionne par type d\'activité : vos exemples de résumés n\'influencent pas vos analyses, et inversement.',
        'Plus vous sauvegardez, plus les activités générées vous ressemblent.',
      ],
    },
  },
  { texte: 'Votre niveau par défaut est mémorisé d\'une session à l\'autre — vous n\'avez pas à le resélectionner à chaque connexion.' },
  { texte: 'L\'option « Avec correction » génère automatiquement un corrigé complet sous l\'activité.' },
  { texte: 'Depuis « Mes activités », rechargez une activité précédente et régénérez-la avec un nouveau texte source.' },
  { texte: 'Complétez votre profil (matière, niveau par défaut) pour que aSchool s\'adapte à votre contexte dès la connexion.' },
  { texte: 'La précision « Mélange » demande à aSchool de combiner tous les types disponibles pour cette activité. Le détail des types s\'affiche sous le sélecteur.' },
  { texte: 'Pour retrouver un texte dont vous avez un souvenir vague, consultez Gallica (gallica.bnf.fr) ou Wikisource, puis copiez-collez dans aSchool.' },
  { texte: 'Problème de connexion persistant ? Supprimez les cookies du site : F12 → Application → Cookies → tout supprimer.' },
]

function getPhrase(count) {
  if (count === 0) return 'Votre premier cours personnalisé est à portée de clic.'
  if (count < 3)  return 'Bon début ! Sauvegardez vos activités — aSchool apprend à vous connaître.'
  if (count < 10) return `${count} activités créées. aSchool commence à reconnaître votre style.`
  if (count < 30) return `${count} activités créées. aSchool reconnaît maintenant votre façon d'enseigner.`
  return `${count} activités créées — vous faites partie des profs les plus actifs de la plateforme.`
}

const SUB_LABEL = { fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 7 }
const EMPTY_MSG = { fontSize: 12, color: '#cbd5e1', fontStyle: 'italic' }

export default function Accueil({ user, matiereLabel, niveau, onNavigate, onCharger, onChargerSequence }) {
  const [data,     setData]     = useState(null)
  const [tipModal, setTipModal] = useState(null)
  const [tipIndex, setTipIndex] = useState(
    () => parseInt(localStorage.getItem('aschool_tip_index') || '0') % TIPS.length
  )
  const isMobile = window.innerWidth < 768

  useEffect(() => {
    fetch('/api/dashboard', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d) })
      .catch(() => {})
  }, [])

  function goTip(dir) {
    setTipIndex(i => {
      const next = (i + dir + TIPS.length) % TIPS.length
      localStorage.setItem('aschool_tip_index', String(next))
      return next
    })
  }

  const hour     = new Date().getHours()
  const greeting = hour < 12 ? 'Bonjour' : hour < 18 ? 'Bon après-midi' : 'Bonsoir'
  const prenom   = user?.prenom || ''
  const phrase   = data !== null ? getPhrase(data.mes_activites) : ''
  const tip      = TIPS[tipIndex]
  const derniereActivite  = data?.recentes?.[0] ?? null
  const derniereSequence  = data?.derniere_sequence ?? null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* ── Bandeau de bienvenue ── */}
      <div style={{
        background: 'linear-gradient(135deg, #1e40af 0%, #5b21b6 55%, var(--bordeaux) 100%)',
        borderRadius: 12, padding: '22px 28px', color: '#fff',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ fontSize: 21, fontWeight: 800, letterSpacing: '-0.02em' }}>
            {greeting}{prenom ? `, ${prenom}` : ''} !
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

      {/* ── Contenu principal ── */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 210px', gap: 12, alignItems: 'start' }}>

        {/* ── Mes dernières créations ── */}
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b' }}>Mes dernières créations</div>

          {/* Activité */}
          <div>
            <div style={SUB_LABEL}>Activité</div>
            {derniereActivite ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '9px 12px', borderRadius: 7, background: '#f8fafc', border: '1px solid #f1f5f9' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {derniereActivite.activite_label}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>
                    {derniereActivite.matiere} · {derniereActivite.niveau}{derniereActivite.objet ? ` · ${derniereActivite.objet.substring(0, 28)}${derniereActivite.objet.length > 28 ? '…' : ''}` : ''}
                  </div>
                </div>
                <button
                  onClick={() => onCharger(derniereActivite)}
                  title="Recharger cette activité dans Mes outils"
                  style={{ flexShrink: 0, padding: '4px 10px', fontSize: 11, fontWeight: 600, background: 'none', border: '1px solid var(--bordeaux)', borderRadius: 5, color: 'var(--bordeaux)', cursor: 'pointer', whiteSpace: 'nowrap' }}
                >
                  Recharger →
                </button>
              </div>
            ) : (
              <div style={EMPTY_MSG}>Aucune activité sauvegardée pour l'instant.</div>
            )}
            <button onClick={() => onNavigate('mes-activites')} title="Voir toutes mes activités sauvegardées"
              style={{ marginTop: 7, background: 'none', border: 'none', padding: 0, fontSize: 11, color: '#64748b', cursor: 'pointer', textDecoration: 'underline' }}>
              Voir toutes mes activités →
            </button>
          </div>

          {/* Séquence */}
          <div>
            <div style={SUB_LABEL}>Séquence</div>
            {derniereSequence ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '9px 12px', borderRadius: 7, background: '#f8fafc', border: '1px solid #f1f5f9' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {derniereSequence.theme}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>
                    {derniereSequence.matiere} · {derniereSequence.niveau} · {derniereSequence.duree} min
                  </div>
                </div>
                <button
                  onClick={() => onChargerSequence(derniereSequence)}
                  title="Recharger cette séquence dans Mes outils"
                  style={{ flexShrink: 0, padding: '4px 10px', fontSize: 11, fontWeight: 600, background: 'none', border: '1px solid #7c3aed', borderRadius: 5, color: '#7c3aed', cursor: 'pointer', whiteSpace: 'nowrap' }}
                >
                  Recharger →
                </button>
              </div>
            ) : (
              <div style={EMPTY_MSG}>Aucune séquence sauvegardée pour l'instant.</div>
            )}
            <button onClick={() => onNavigate('mes-sequences')} title="Voir toutes mes séquences sauvegardées"
              style={{ marginTop: 7, background: 'none', border: 'none', padding: 0, fontSize: 11, color: '#64748b', cursor: 'pointer', textDecoration: 'underline' }}>
              Voir toutes mes séquences →
            </button>
          </div>

          {/* Analyse */}
          <div>
            <div style={SUB_LABEL}>Analyse</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {[
                { label: 'Ambiguïtés', page: 'ambiguites', title: 'Détecter les ambiguïtés cognitives d\'un exercice ou énoncé' },
                { label: 'Consignes',  page: 'consigne',   title: 'Analyser la qualité didactique d\'une consigne' },
                { label: 'Équité',     page: 'equite',     title: 'Auditer l\'équité pédagogique d\'une évaluation' },
              ].map(a => (
                <button
                  key={a.page}
                  onClick={() => onNavigate(a.page)}
                  title={a.title}
                  style={{ padding: '5px 12px', fontSize: 11, fontWeight: 600, background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 6, color: '#475569', cursor: 'pointer' }}
                >
                  {a.label} →
                </button>
              ))}
            </div>
          </div>

        </div>

        {/* ── Colonne droite ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>

          {/* CTA */}
          <div style={{ background: 'var(--bordeaux)', borderRadius: 10, padding: '18px 14px', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ color: '#fff', fontSize: 13, fontWeight: 700 }}>Prêt à créer ?</div>
            <button
              onClick={() => onNavigate('mes-outils')}
              title="Aller dans Mes outils"
              style={{ background: '#fff', border: 'none', borderRadius: 7, padding: '8px 14px', fontSize: 13, fontWeight: 700, color: 'var(--bordeaux)', cursor: 'pointer' }}
            >
              Mes outils →
            </button>
          </div>

          {/* Lien vers stats */}
          <button
            onClick={() => onNavigate('mes-stats')}
            title="Consulter mes statistiques et la vitalité de la plateforme"
            style={{ background: '#f0f9ff', border: '1px solid #bfdbfe', borderRadius: 10, padding: '12px 14px', textAlign: 'left', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 4 }}
          >
            <div style={{ fontSize: 12, fontWeight: 700, color: '#1d4ed8' }}>Mes statistiques</div>
            <div style={{ fontSize: 11, color: '#3b82f6', lineHeight: 1.4 }}>Activités, séquences, score d'adaptation et vitalité →</div>
          </button>

          {/* Astuce — texte clampé à 4 lignes */}
          <div style={{ background: '#f5f3ff', border: '1px solid #c4b5fd', borderRadius: 10, padding: '12px 13px', fontSize: '11.5px', color: '#5b21b6', display: 'flex', flexDirection: 'column', gap: 7 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em', color: '#7c3aed' }}>Astuce</span>
              <span style={{ fontSize: 10, color: '#a78bfa' }}>{tipIndex + 1}/{TIPS.length}</span>
            </div>
            <p style={{
              margin: 0, lineHeight: 1.55,
              display: '-webkit-box',
              WebkitLineClamp: 4,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {tip.texte}
            </p>
            {tip.lien && (
              <button onClick={() => setTipModal(tip.modal)} style={{ background: 'none', border: 'none', padding: 0, color: '#5b21b6', textDecoration: 'underline', cursor: 'pointer', fontSize: '11px', textAlign: 'left' }}>
                {tip.lien.label} →
              </button>
            )}
            <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
              <button onClick={() => goTip(-1)} title="Astuce précédente" style={{ background: 'none', border: '1px solid #c4b5fd', borderRadius: 4, padding: '3px 6px', cursor: 'pointer', color: '#5b21b6', display: 'flex', alignItems: 'center' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
              </button>
              <button onClick={() => goTip(1)} title="Astuce suivante" style={{ background: 'none', border: '1px solid #c4b5fd', borderRadius: 4, padding: '3px 6px', cursor: 'pointer', color: '#5b21b6', display: 'flex', alignItems: 'center' }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
            </div>
          </div>

        </div>
      </div>

      {/* Modal astuce */}
      {tipModal && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 600 }}
          onClick={e => { if (e.target === e.currentTarget) setTipModal(null) }}
        >
          <div style={{ background: '#fff', borderRadius: 10, padding: 24, width: 420, maxWidth: '92vw', boxShadow: '0 8px 32px rgba(0,0,0,0.18)', display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#3b0764' }}>{tipModal.titre}</div>
              <button onClick={() => setTipModal(null)} title="Fermer" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af', fontSize: 18, lineHeight: 1, flexShrink: 0, padding: '0 2px' }}>×</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {tipModal.lignes.map((l, i) => (
                <p key={i} style={{ fontSize: 13, color: '#374151', lineHeight: 1.6, margin: 0 }}>{l}</p>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setTipModal(null)} title="Fermer" style={{ padding: '7px 20px', fontSize: 13, borderRadius: 6, border: 'none', background: '#5b21b6', color: '#fff', cursor: 'pointer', fontWeight: 600 }}>Compris</button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
