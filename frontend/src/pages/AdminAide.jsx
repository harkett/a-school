const SECTIONS = [
  {
    categorie: 'Surveillance',
    items: [
      {
        titre: 'Sessions',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
          </svg>
        ),
        contenu: [
          'Affiche tous les enseignants connectés en temps réel (mis à jour toutes les 90 secondes).',
          'Les informations disponibles : navigateur, système d\'exploitation, adresse IP, heure de connexion, dernière activité.',
          'La colonne "En ligne" (point vert) indique une activité dans les 90 dernières secondes.',
          'Le bouton "Déconnecter" ferme la session immédiatement et envoie un e‑mail automatique à l\'utilisateur. Une raison peut être renseignée — elle apparaît dans l\'e‑mail.',
          'Il est impossible de déconnecter la session administrateur depuis cette interface.',
        ],
      },
      {
        titre: 'Serveur',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="20" height="4" rx="1"/><rect x="2" y="10" width="20" height="4" rx="1"/><rect x="2" y="17" width="20" height="4" rx="1"/>
          </svg>
        ),
        contenu: [
          'Métriques VPS en temps réel : CPU, RAM, espace disque, uptime.',
          'Graphe des connexions sur les 30 derniers jours.',
          'Répartition des connexions par heure de la journée (utile pour planifier les maintenances).',
          'Taille de la base de données SQLite.',
          'Seuils d\'alerte automatiques : CPU > 85 %, RAM > 90 %, disque > 85 % déclenchent une alerte dans l\'onglet Alertes.',
        ],
      },
    ],
  },
  {
    categorie: 'Notifications',
    items: [
      {
        titre: 'Alertes',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
        ),
        contenu: [
          'Les alertes sont générées automatiquement toutes les 5 minutes par le serveur.',
          'Trois niveaux : Info (bleu), Warning (orange), Critical (rouge).',
          'Déclencheurs : ressources serveur critiques, pic de tentatives de connexion échouées (> 10/h sur la même IP), inactivité prolongée.',
          'Un badge rouge dans le menu indique le nombre d\'alertes non lues.',
          'Marquer une alerte comme lue la retire du compteur mais la conserve dans l\'historique.',
        ],
      },
      {
        titre: 'Feedbacks',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        ),
        contenu: [
          'Centralise tous les retours des enseignants : feedbacks libres, notations (étoiles) et idées de fonctionnalités.',
          'Quatre statuts disponibles : Nouveau → En cours → Traité → Archivé.',
          'Changer le statut permet de suivre le traitement sans perdre l\'historique.',
          'Un badge rouge dans le menu indique le nombre de feedbacks au statut "Nouveau".',
          'Les idées de fonctionnalités arrivent ici depuis la page "Bientôt disponible" de l\'application.',
        ],
      },
    ],
  },
  {
    categorie: 'Utilisateurs',
    items: [
      {
        titre: 'Profs',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <line x1="23" y1="11" x2="17" y2="11"/><line x1="20" y1="8" x2="20" y2="14"/>
          </svg>
        ),
        contenu: [
          'Liste tous les enseignants inscrits et vérifiés (e‑mail confirmé).',
          'Les colonnes sont triables. Les filtres permettent de chercher par nom/e‑mail, par matière ou par statut (actif/désactivé).',
          'Actions disponibles sur chaque ligne :',
          '— Crayon : modifier le profil (prénom, nom, matière, niveau).',
          '— Clé : envoyer un lien de réinitialisation du mot de passe par e‑mail.',
          '— Power (orange/vert) : désactiver ou réactiver le compte. Un compte désactivé ne peut plus se connecter, mais ses données sont conservées. La désactivation est réversible.',
          '— Enveloppe : envoyer un e‑mail personnalisé à ce prof (objet + corps, avec variables {prenom} et {email}).',
          '— Corbeille : supprimer définitivement le compte et toutes ses données (activités, feedbacks, tokens). Irréversible.',
        ],
        astuce: 'Le compte demo@aschool.fr est le compte système qui héberge les 24 activités d\'exemple de la Bibliothèque. Désactiver ce compte masque instantanément tous les exemples pour tous les profs. Le réactiver les fait réapparaître. C\'est le seul mécanisme pour piloter l\'affichage des exemples.',
      },
      {
        titre: 'Mail groupé',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 2L11 13"/><path d="M22 2L15 22 11 13 2 9l20-7z"/>
          </svg>
        ),
        contenu: [
          'Permet d\'envoyer un message à plusieurs enseignants en une seule opération.',
          'Étapes : (1) rédiger l\'objet et le corps du message, (2) sélectionner les destinataires, (3) envoyer.',
          'La sélection se fait par cases à cocher. La case dans l\'en-tête sélectionne/désélectionne tous les profs visibles (selon les filtres actifs).',
          'Les filtres matière et statut permettent de cibler rapidement un groupe (ex. : tous les profs de Maths actifs).',
          'Variables disponibles dans le message : {prenom} et {email} sont remplacés automatiquement pour chaque destinataire.',
          'Les e‑mails sont envoyés un par un. Un résumé (X envoyés / Y erreurs) s\'affiche à la fin.',
          'Chaque envoi est enregistré dans le journal d\'audit.',
        ],
      },
      {
        titre: 'Activités',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        ),
        contenu: [
          'Vue d\'ensemble du catalogue pédagogique : 12 matières, activités disponibles par matière, sous-types.',
          'Statistiques d\'usage : nombre total d\'activités générées, répartition par matière.',
          'Permet de vérifier rapidement quelle matière est la plus utilisée et d\'identifier d\'éventuels déséquilibres.',
        ],
      },
    ],
  },
  {
    categorie: 'Accès & Sécurité',
    items: [
      {
        titre: 'Connexions',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        ),
        contenu: [
          'Journal chronologique de toutes les connexions : qui s\'est connecté, quand, depuis quelle IP.',
          'Différencie les connexions enseignants des connexions administrateur.',
          'Utile pour détecter une connexion suspecte (IP inhabituelle, heure anormale).',
          'Limité aux 200 dernières entrées.',
        ],
      },
      {
        titre: 'Tentatives',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        ),
        contenu: [
          'Recense toutes les tentatives de connexion échouées : identifiant tenté, IP, navigateur.',
          'La colonne "Bloqué" indique les IP automatiquement bloquées après 10 échecs en 1 heure.',
          'Permet d\'identifier une attaque par force brute ou une tentative d\'intrusion ciblée.',
        ],
      },
      {
        titre: 'Audit',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
        ),
        contenu: [
          'Trace toutes les actions sensibles effectuées via le backoffice.',
          'Actions enregistrées : suppression de compte, désactivation/réactivation, réinitialisation de mot de passe, déconnexion forcée, modification des paramètres, envoi de mail groupé, changement du mot de passe admin.',
          'Chaque entrée indique : l\'action, la cible, l\'IP de l\'administrateur, la date et heure.',
          'Ce journal ne peut pas être modifié ou supprimé depuis l\'interface.',
        ],
      },
    ],
  },
  {
    categorie: 'Configuration',
    items: [
      {
        titre: 'Paramètres',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        ),
        contenu: [
          'Personnalisation de l\'e‑mail de bienvenue envoyé lors de la validation d\'un nouveau compte.',
          'Variables disponibles dans le modèle : {prenom} et {email}.',
          'Le bouton "Tester" envoie l\'e‑mail de bienvenue à l\'adresse de l\'administrateur pour vérification.',
          'Les modifications sont sauvegardées en base de données et prises en compte immédiatement.',
        ],
      },
      {
        titre: 'Mon compte',
        icon: (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
          </svg>
        ),
        contenu: [
          'Permet de changer le mot de passe du compte administrateur.',
          'Le nouveau mot de passe est stocké en base de données sous forme hachée (bcrypt) — il remplace et prime sur le mot de passe défini dans le fichier .env.',
          'Minimum 8 caractères requis.',
          'Cette action est enregistrée dans le journal d\'audit.',
        ],
      },
    ],
  },
]

export default function AdminAide() {
  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ margin: '0 0 6px', fontSize: 15, fontWeight: 700, color: '#1e293b' }}>
          Documentation administrateur
        </h2>
        <p style={{ margin: 0, fontSize: 13, color: '#64748b', lineHeight: 1.6 }}>
          Référence complète des fonctionnalités du backoffice A‑SCHOOL.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
        {SECTIONS.map(section => (
          <div key={section.categorie}>
            <div style={{
              fontSize: 11, fontWeight: 700, color: '#94a3b8',
              textTransform: 'uppercase', letterSpacing: '0.8px',
              marginBottom: 12,
            }}>
              {section.categorie}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {section.items.map(item => (
                <div key={item.titre} style={{
                  background: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: 10,
                  overflow: 'hidden',
                }}>
                  {/* En-tête */}
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '14px 20px',
                    borderBottom: '1px solid #f1f5f9',
                    background: '#f8fafc',
                  }}>
                    <span style={{ color: '#475569' }}>{item.icon}</span>
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                      {item.titre}
                    </span>
                  </div>

                  {/* Contenu */}
                  <div style={{ padding: '14px 20px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {item.contenu.map((ligne, i) => (
                      <p key={i} style={{
                        margin: 0, fontSize: 13, color: '#475569', lineHeight: 1.65,
                        paddingLeft: ligne.startsWith('—') ? 12 : 0,
                      }}>
                        {ligne}
                      </p>
                    ))}

                    {item.astuce && (
                      <div style={{
                        marginTop: 10,
                        padding: '10px 14px',
                        background: '#fffbeb',
                        border: '1px solid #fde68a',
                        borderRadius: 7,
                        display: 'flex',
                        gap: 10,
                        alignItems: 'flex-start',
                      }}>
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 1 }}>
                          <circle cx="12" cy="12" r="10"/>
                          <line x1="12" y1="8" x2="12" y2="12"/>
                          <line x1="12" y1="16" x2="12.01" y2="16"/>
                        </svg>
                        <p style={{ margin: 0, fontSize: 12, color: '#92400e', lineHeight: 1.65 }}>
                          <strong>Astuce — </strong>{item.astuce}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
