import CoupleBandeau from './CoupleBandeau'
import useIsMobile from '../hooks/useIsMobile'

// LA hauteur de la barre du haut, en un seul endroit — App.jsx s'en sert pour décaler la page
// d'autant. Elle reste à 65 px : le logo et son sous-titre y tiennent l'un sous l'autre depuis
// que l'image a été recadrée sur sa partie utile (07/08/2026). Elle valait 1536 × 1024 pixels
// dont 600 × 190 de dessin — 88 % de vide transparent. C'est ce vide, et non la barre, qui
// obligeait à afficher le logo en 140 px de haut pour qu'il paraisse lisible : il débordait
// alors de la barre, qui le rognait en haut et en bas. Image nettoyée, le compte est bon.
export const HAUTEUR_HEADER = 65

// Header sur DEUX lignes utiles (décision du 25/07) : à droite, trois colonnes empilées —
// « assistance » (« Comment ça marche » selon le contexte de la page + « Feedback » partout,
// sa demande du 25/07), « couple » (Matière - Niveau, l'UNIQUE afficheur du couple de
// travail, avec son bouton « Changer niveau et/ou matière » juste dessous) et « compte »
// (l'identité au-dessus de « Se déconnecter »). onOuvrirGuide null = la page n'a pas de
// mode d'emploi → le bouton est CACHÉ (pas grisé).
// `bloque` : le professeur vient de s'inscrire, son profil est vide, et TOUT l'écran est éteint
// sauf la carte « Mon profil ». Le bandeau, lui, ne s'éteint PAS — il porte la seule phrase qui
// dit quoi faire, et le logo, qu'une application sérieuse ne grise jamais. Ce sont ses BOUTONS
// qui deviennent inertes : ils mèneraient ailleurs, et cet ailleurs n'existe pas encore.
export default function Header({ matiere, niveau, email, prenom, nom, profilNomIncomplet, onLogout, onNavigate, onFeedback,
                                 sessionMatiere, coupleAjuste, onValiderCouple, onRevenirProfil, onOuvrirGuide,
                                 bloque = false }) {
  const nomAffiche = [prenom, nom].filter(Boolean).join(' ') || email
  const matiereNiveau = [matiere, niveau].filter(Boolean).join(' - ')
  const isMobile = useIsMobile()   // réagit au redimensionnement ; calculé une fois, il était figé
  return (
    <header
      className="flex items-center justify-between px-6"
      style={{ backgroundColor: 'var(--bleu)', height: HAUTEUR_HEADER, overflow: 'hidden', position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100 }}
    >
      {/* LOGO PUIS SOUS-TITRE, L'UN SOUS L'AUTRE (07/08/2026). Le titre était posé À CÔTÉ du
          logo, en 1,4 rem : il repassait sur deux lignes et mangeait la largeur dont la barre a
          besoin pour le couple, le compte et les boutons. Sous le logo et en petit, il tient sur
          une ligne et rend cette place. `whiteSpace: nowrap` fige ce gain : le jour où la barre
          se resserre encore, c'est le sous-titre qui s'efface (il l'est déjà sur mobile), pas la
          mise en page qui se casse. */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', justifyContent: 'center', minWidth: 0 }}>
        <img src="/Logo_aSchool_blanc.png" alt="aSchool" title="Générateur d'activités pédagogiques" style={{ height: 34, width: 'auto', display: 'block' }} />
        <span style={{
          color: 'rgba(255,255,255,0.9)', fontSize: '0.75rem', fontWeight: 500,
          lineHeight: 1.1, marginTop: 3, whiteSpace: 'nowrap',
          display: isMobile ? 'none' : undefined,
        }}>
          Générateur d'activités pédagogiques
        </span>
      </div>
      <div className="flex items-center gap-4 text-sm">
        {/* LA CONSIGNE, ET ELLE DOIT SE VOIR. Écrite en rouge sombre sur pastille claire, elle
            respire lentement — assez pour attirer l'œil, pas assez pour agacer. Quand tout le
            reste de l'écran est éteint, c'est la seule chose qui dit au nouvel inscrit ce qu'on
            attend de lui ; discrète, elle le laisse devant une application qu'il croit en panne. */}
        {(bloque || profilNomIncomplet) && (
          <>
            <style>{`
              @keyframes aschool-consigne {
                0%, 100% { opacity: 1;    box-shadow: 0 0 0 0 rgba(255,255,255,0.5) }
                50%      { opacity: 0.72; box-shadow: 0 0 0 6px rgba(255,255,255,0) }
              }
            `}</style>
            <button
              onClick={() => onNavigate('mon-profil')}
              title="Ouvrir « Mon profil » — indiquez votre niveau et votre matière pour commencer"
              style={{
                background: '#fff', color: '#b91c1c', border: 'none', borderRadius: 999,
                padding: isMobile ? '4px 10px' : '6px 16px', cursor: 'pointer',
                fontSize: isMobile ? '0.72rem' : '0.85rem', fontWeight: 700,
                fontFamily: 'inherit', whiteSpace: 'nowrap', lineHeight: 1.2,
                display: 'inline-flex', alignItems: 'center', gap: 7,
                animation: 'aschool-consigne 1.8s ease-in-out infinite',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   strokeWidth="2.5" strokeLinecap="round" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10" /><line x1="12" y1="7" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              {bloque ? 'Complétez votre profil pour commencer' : 'Merci de compléter votre profil'}
            </button>
          </>
        )}
        {!isMobile && <span style={{ color: 'rgba(255,255,255,0.35)' }}>|</span>}
        {/* CE QUI SUIT EST INERTE TANT QUE LE PROFIL EST VIDE : ces boutons mènent ailleurs, et
            cet ailleurs n'existe pas encore. Ils restent VISIBLES — pâlis, pas effacés — pour
            qu'on voie ce qui attend une fois le profil rempli. */}
        <div style={bloque
                    ? { display: 'flex', alignItems: 'center', gap: '1rem',
                        opacity: 0.45, pointerEvents: 'none' }
                    : { display: 'flex', alignItems: 'center', gap: '1rem' }}
             aria-hidden={bloque || undefined}>
        {/* Colonne assistance : le mode d'emploi de la page (si elle en a un) + le feedback */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          {onOuvrirGuide && (
            <button
              onClick={onOuvrirGuide}
              title="Ouvrir le mode d'emploi de cet écran — une fenêtre déplaçable et étirable, avec un exemple pour votre classe."
              style={{
                color: 'white', border: '1px solid rgba(255,255,255,0.4)', borderRadius: '6px',
                padding: '0.18rem 0.7rem', fontSize: '0.75rem', background: 'none', cursor: 'pointer',
                display: 'inline-flex', alignItems: 'center', gap: '5px', whiteSpace: 'nowrap', fontFamily: 'inherit',
              }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              Comment ça marche
            </button>
          )}
          <button
            onClick={onFeedback}
            title="Envoyer un retour, une idée ou signaler un problème — nous lisons tout."
            style={{
              color: 'white', border: '1px solid rgba(255,255,255,0.4)', borderRadius: '6px',
              padding: '0.18rem 0.7rem', fontSize: '0.75rem', background: 'none', cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: '5px', whiteSpace: 'nowrap', fontFamily: 'inherit',
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Feedback
          </button>
        </div>
        {!isMobile && <span style={{ color: 'rgba(255,255,255,0.35)' }}>|</span>}
        {/* Colonne couple : l'afficheur unique du couple, son bouton de changement DESSOUS */}
        <div data-guide="couple" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
          <span style={{ color: 'white', fontWeight: 600, fontSize: isMobile ? '0.72rem' : undefined, whiteSpace: 'nowrap' }}>
            {matiereNiveau}
          </span>
          <CoupleBandeau
            sessionMatiere={sessionMatiere}
            niveau={niveau}
            coupleAjuste={coupleAjuste}
            onValider={onValiderCouple}
            onRevenirProfil={onRevenirProfil}
          />
        </div>
        {!isMobile && <span style={{ color: 'rgba(255,255,255,0.35)' }}>|</span>}
        {/* Colonne compte : l'identité AU-DESSUS du bouton Se déconnecter */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
          <button
            onClick={() => onNavigate('mon-profil')}
            title="Voir et modifier mon profil"
            style={{
              color: 'rgba(255,255,255,0.8)', cursor: 'pointer', background: 'none', border: 'none',
              padding: 0, fontSize: isMobile ? '0.72rem' : 'inherit', fontFamily: 'inherit', whiteSpace: 'nowrap',
            }}
          >
            <span style={{ borderBottom: '1px dotted rgba(255,255,255,0.4)' }}>{nomAffiche}</span>
          </button>
          <button
            onClick={onLogout}
            title="Fermer votre session et revenir à la page de connexion"
            style={{
              color: 'white', border: '1px solid rgba(255,255,255,0.4)',
              borderRadius: '6px', padding: '0.3rem 0.85rem',
              fontSize: '0.8rem', background: 'none', cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: '5px',
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            {isMobile ? 'Déconnecter' : 'Se déconnecter'}
          </button>
        </div>
        </div>
      </div>
    </header>
  )
}
