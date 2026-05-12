import { useState } from 'react'

const IconBook = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
  </svg>
)

const IconSliders = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
    <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
    <line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>
  </svg>
)

const IconBulb = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/>
    <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
  </svg>
)

const IconAlert = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
)

const IconTarget = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
  </svg>
)

const IconUser = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)

const IconSparkle = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
  </svg>
)

const ChevronDown = ({ open }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2"
    style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.25s ease', flexShrink: 0 }}>
    <polyline points="6 9 12 15 18 9"/>
  </svg>
)

const IconMobile = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
    <line x1="12" y1="18" x2="12.01" y2="18"/>
  </svg>
)

const ShareIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline', verticalAlign: 'middle', marginBottom: '1px' }}>
    <polyline points="8 6 12 2 16 6"/>
    <line x1="12" y1="2" x2="12" y2="15"/>
    <path d="M20 13v7a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-7"/>
  </svg>
)

const Step = ({ n, children }) => (
  <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
    <span style={{ flexShrink: 0, width: 22, height: 22, borderRadius: '50%', background: 'var(--bleu)', color: '#fff', fontSize: 11, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>{n}</span>
    <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.55 }}>{children}</span>
  </div>
)

function telechargerProcedure(titre, html) {
  const w = window.open('', '_blank')
  w.document.write(`<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <title>${titre}</title>
    <style>
      body { font-family: system-ui, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; color: #1e293b; }
      h1 { font-size: 20px; font-weight: 700; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0; }
      .step { display: flex; gap: 12px; margin-bottom: 14px; align-items: flex-start; }
      .num { min-width: 26px; height: 26px; border-radius: 50%; background: #1d4ed8; color: #fff; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
      .note { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #166534; margin-top: 16px; }
      .warn { background: #fef3c7; border: 1px solid #fcd34d; border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #92400e; margin-bottom: 16px; }
      .info { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #1e40af; margin-bottom: 16px; }
      footer { margin-top: 32px; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 12px; }
      @media print { button { display: none; } }
    </style>
  </head><body>
    <h1>${titre}</h1>
    ${html}
    <footer>aSchool — aschool.fr</footer>
    <script>window.onload = () => window.print()</script>
  </body></html>`)
  w.document.close()
}

const sections = [
  {
    id: 'install-ios',
    titre: 'Installer aSchool sur iPhone (iOS)',
    Icon: IconMobile,
    contenu: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ background: '#fef3c7', border: '1px solid #fcd34d', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: '#92400e' }}>
          Fonctionne uniquement avec <strong>Safari</strong> — pas Chrome, pas Firefox.
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <Step n="1">Ouvrez <strong>aschool.fr</strong> dans Safari et connectez-vous.</Step>
          <Step n="2">Appuyez sur l'icône <strong>Partage</strong> <ShareIcon /> en bas au centre de Safari.</Step>
          <Step n="3">Faites défiler la liste vers le bas et appuyez sur <strong>« Sur l'écran d'accueil »</strong>.</Step>
          <Step n="4">Vérifiez que le nom affiché est <strong>aSchool</strong>, puis appuyez sur <strong>Ajouter</strong>.</Step>
          <Step n="5">L'icône aSchool apparaît sur votre écran d'accueil. Ouvrez-la — l'app se lance en plein écran, sans barre Safari.</Step>
        </div>
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: '#166534' }}>
          Une fois installée, aSchool fonctionne même avec une connexion faible — l'interface se charge instantanément.
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
          <button
            title="Télécharger la procédure en PDF"
            onClick={() => telechargerProcedure('Installer aSchool sur iPhone (iOS)', `
              <div class="warn">Fonctionne uniquement avec <strong>Safari</strong> — pas Chrome, pas Firefox.</div>
              <div class="step"><div class="num">1</div><div>Ouvrez <strong>aschool.fr</strong> dans Safari et connectez-vous.</div></div>
              <div class="step"><div class="num">2</div><div>Appuyez sur l'icône <strong>Partage</strong> (↑) en bas au centre de Safari.</div></div>
              <div class="step"><div class="num">3</div><div>Faites défiler la liste vers le bas et appuyez sur <strong>« Sur l'écran d'accueil »</strong>.</div></div>
              <div class="step"><div class="num">4</div><div>Vérifiez que le nom affiché est <strong>aSchool</strong>, puis appuyez sur <strong>Ajouter</strong>.</div></div>
              <div class="step"><div class="num">5</div><div>L'icône aSchool apparaît sur votre écran d'accueil. Ouvrez-la — l'app se lance en plein écran, sans barre Safari.</div></div>
              <div class="note">Une fois installée, aSchool fonctionne même avec une connexion faible — l'interface se charge instantanément.</div>
            `)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, padding: '6px 14px', fontSize: 12, color: '#64748b', cursor: 'pointer', fontWeight: 500 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Télécharger la procédure (PDF)
          </button>
        </div>
      </div>
    ),
  },
  {
    id: 'install-android',
    titre: 'Installer aSchool sur Android',
    Icon: IconMobile,
    contenu: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: '#1e40af' }}>
          Fonctionne avec <strong>Chrome</strong> (recommandé) ou Samsung Internet.
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <Step n="1">Ouvrez <strong>aschool.fr</strong> dans Chrome et connectez-vous.</Step>
          <Step n="2">Une bannière <strong>« Ajouter aSchool à l'écran d'accueil »</strong> peut apparaître automatiquement en bas — appuyez dessus.</Step>
          <Step n="3">Sinon : appuyez sur les <strong>3 points ⋮</strong> en haut à droite → <strong>« Ajouter à l'écran d'accueil »</strong>.</Step>
          <Step n="4">Confirmez en appuyant sur <strong>Ajouter</strong>.</Step>
          <Step n="5">L'icône aSchool apparaît sur votre écran d'accueil. L'app se lance en plein écran, sans barre Chrome.</Step>
        </div>
        <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: '8px 12px', fontSize: 12, color: '#166534' }}>
          Sur Android, Chrome détecte automatiquement l'app installable et propose la bannière dès la connexion.
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
          <button
            title="Télécharger la procédure en PDF"
            onClick={() => telechargerProcedure('Installer aSchool sur Android', `
              <div class="info">Fonctionne avec <strong>Chrome</strong> (recommandé) ou Samsung Internet.</div>
              <div class="step"><div class="num">1</div><div>Ouvrez <strong>aschool.fr</strong> dans Chrome et connectez-vous.</div></div>
              <div class="step"><div class="num">2</div><div>Une bannière <strong>« Ajouter aSchool à l'écran d'accueil »</strong> peut apparaître automatiquement en bas — appuyez dessus.</div></div>
              <div class="step"><div class="num">3</div><div>Sinon : appuyez sur les <strong>3 points ⋮</strong> en haut à droite → <strong>« Ajouter à l'écran d'accueil »</strong>.</div></div>
              <div class="step"><div class="num">4</div><div>Confirmez en appuyant sur <strong>Ajouter</strong>.</div></div>
              <div class="step"><div class="num">5</div><div>L'icône aSchool apparaît sur votre écran d'accueil. L'app se lance en plein écran, sans barre Chrome.</div></div>
              <div class="note">Une fois installée, aSchool fonctionne même avec une connexion faible — l'interface se charge instantanément.</div>
            `)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, padding: '6px 14px', fontSize: 12, color: '#64748b', cursor: 'pointer', fontWeight: 500 }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Télécharger la procédure (PDF)
          </button>
        </div>
      </div>
    ),
  },
  {
    id: 'sequence',
    titre: 'Créer une séquence — ce que la fonctionnalité fera',
    Icon: IconSparkle,
    contenu: (
      <div className="flex flex-col gap-5 text-sm text-gray-600">

        <div>
          <p className="font-semibold text-gray-700 mb-2">1. Décrivez votre objectif pédagogique</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>Formulez ce que vos élèves doivent savoir ou savoir-faire à la fin de la séquence</li>
            <li>Précisez le contexte : nombre de séances, durée totale, contraintes éventuelles</li>
            <li>Vous pouvez dicter l'objectif à la voix ou le coller depuis un autre document</li>
          </ul>
        </div>

        <hr className="border-gray-100" />

        <div>
          <p className="font-semibold text-gray-700 mb-2">2. Paramétrez la structure</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li><strong>Nombre de phases ou de séances</strong> — A-SCHOOL répartit les apprentissages</li>
            <li>
              <strong>Types de phases à inclure</strong> :
              <ul className="mt-1 pl-3 flex flex-col gap-0.5" style={{ listStyleType: 'circle' }}>
                <li>Découverte / mise en situation</li>
                <li>Structuration des connaissances</li>
                <li>Entraînement / exercices</li>
                <li>Synthèse / bilan</li>
                <li>Évaluation finale</li>
              </ul>
            </li>
            <li><strong>Avec ou sans corrigé enseignant</strong> pour chaque phase</li>
          </ul>
        </div>

        <hr className="border-gray-100" />

        <div>
          <p className="font-semibold text-gray-700 mb-2">3. A-SCHOOL génère la séquence complète</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>Chaque phase est détaillée : nom, durée, objectif, consignes élèves, matériel</li>
            <li>Progression garantie : pas de rupture conceptuelle, charge cognitive maîtrisée</li>
            <li>Ancrage mémoriel intégré : synthèse, révision et bilan prévus dans la structure</li>
            <li>Séquence exportable et partageable avec des collègues</li>
          </ul>
        </div>

      </div>
    ),
  },
  {
    id: 'optimiseur',
    titre: 'Améliorer une séquence (Optimiseur)',
    Icon: IconTarget,
    contenu: (
      <div className="flex flex-col gap-5 text-sm text-gray-600">

        <div>
          <p className="font-semibold text-gray-700 mb-2">1. Soumettez votre séquence</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>Collez une séquence existante — planning de cours, progression rédigée, fichier de préparation</li>
            <li>Un bouton "Tester sur un exemple" permet de découvrir la fonctionnalité sans séquence sous la main</li>
          </ul>
        </div>

        <hr className="border-gray-100" />

        <div>
          <p className="font-semibold text-gray-700 mb-2">2. A-SCHOOL analyse sur 6 critères</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>Rupture conceptuelle — une phase suppose une notion non encore construite</li>
            <li>Surcharge cognitive — trop de notions nouvelles sur un temps trop court</li>
            <li>Consigne ambiguë — formulation pouvant être mal interprétée</li>
            <li>Activité inefficace — exercice sans lien réel avec l'objectif déclaré</li>
            <li>Progression déséquilibrée — phases trop courtes ou trop longues</li>
            <li>Ancrage mémoriel manquant — pas de consolidation avant l'évaluation</li>
          </ul>
        </div>

        <hr className="border-gray-100" />

        <div>
          <p className="font-semibold text-gray-700 mb-2">3. Récupérez le résultat</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>Un score global : Bon · Moyen · À revoir</li>
            <li>La liste des problèmes détectés avec leur description précise</li>
            <li>La séquence réécrite avec toutes les corrections intégrées</li>
          </ul>
        </div>

      </div>
    ),
  },
  {
    id: 'apprentissage',
    titre: 'A-SCHOOL apprend votre style',
    Icon: IconSparkle,
    contenu: (
      <div className="flex flex-col gap-4 text-sm text-gray-600">
        <p>
          Chaque activité que vous sauvegardez est un exemple que A-SCHOOL retient.
          À partir du <strong>3e exemple du même type</strong>, il reconnaît votre façon
          de travailler et génère un résultat dans votre style.
        </p>
        <p className="text-xs text-gray-400 italic">Rien à configurer — cela se fait automatiquement.</p>

        <div className="rounded-lg overflow-hidden border border-gray-200">
          <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide bg-gray-50">
            Exemple — Questions de compréhension (Français, 4e)
          </div>
          <div className="flex flex-col divide-y divide-gray-100">
            <div className="px-4 py-3">
              <div className="text-xs font-medium text-gray-400 mb-1">Avant — génération standard</div>
              <div className="text-gray-500 italic">
                "À partir du texte proposé, identifiez et expliquez le rôle du personnage principal
                dans la progression narrative, en vous appuyant sur des exemples précis tirés du document."
              </div>
            </div>
            <div className="px-4 py-3" style={{ background: '#eff6ff' }}>
              <div className="text-xs font-medium mb-1" style={{ color: 'var(--bleu)' }}>
                Après — adapté au style de ce professeur
              </div>
              <div className="text-gray-700">
                "1. Quel est le rôle du personnage principal ?<br />
                2. Comment évolue-t-il au fil du texte ?"
              </div>
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-500">
          A-SCHOOL s'affine progressivement à chaque utilisation.
          Plus vous l'utilisez, moins vous corrigez.
        </p>
      </div>
    ),
  },
  {
    id: 'comment',
    titre: 'Créer une activité — tout ce que vous pouvez faire',
    Icon: IconBook,
    contenu: (
      <div className="flex flex-col gap-5 text-sm text-gray-600">

        <div>
          <p className="font-semibold text-gray-700 mb-2">1. Fournissez un texte source — 3 options</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>Collez directement un texte — extrait de manuel, article de presse, document élève</li>
            <li>Dictez à la voix grâce au micro intégré — A-SCHOOL transcrit automatiquement</li>
            <li>Scannez un document papier avec l'OCR — la photo est convertie en texte exploitable</li>
          </ul>
        </div>

        <hr className="border-gray-100" />

        <div>
          <p className="font-semibold text-gray-700 mb-2">2. Configurez les paramètres</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>
              <strong>Type d'activité</strong> — varie selon la matière :
              <ul className="mt-1 pl-3 flex flex-col gap-0.5" style={{ listStyleType: 'circle' }}>
                <li>Questions de compréhension</li>
                <li>Analyse de texte / document</li>
                <li>Résumé / synthèse</li>
                <li>Production d'écrit</li>
                <li>Fiche de révision</li>
                <li>Exercices de vocabulaire</li>
                <li className="text-gray-400 italic">et d'autres selon la matière…</li>
              </ul>
            </li>
            <li><strong>Sous-type</strong> — précise la nature exacte (ex : inférence, lexique, mélange de types)</li>
            <li><strong>Nombre de questions</strong> — disponible selon le type choisi</li>
            <li><strong>Avec correction</strong> — génère le corrigé complet sous l'activité</li>
          </ul>
        </div>

        <hr className="border-gray-100" />

        <div>
          <p className="font-semibold text-gray-700 mb-2">3. Exploitez le résultat</p>
          <ul className="flex flex-col gap-1.5 pl-4" style={{ listStyleType: 'disc' }}>
            <li>Cliquez sur "Générer" — activité prête en quelques secondes</li>
            <li>Régénérez sans hésiter — chaque génération est différente</li>
            <li>Sauvegardez dans "Mes activités" — rechargeable en un clic à tout moment</li>
            <li>Partagez par email avec un collègue depuis le résultat</li>
          </ul>
        </div>

        <hr className="border-gray-100" />

        <p className="text-xs rounded-md px-3 py-2" style={{ background: '#f8fafc', color: '#64748b', borderLeft: '3px solid #cbd5e1' }}>
          A-SCHOOL apprend votre style : à partir de la 3e sauvegarde d'un même type, il adapte automatiquement le ton et la formulation à votre façon d'enseigner — sans rien configurer.
        </p>

      </div>
    ),
  },
  {
    id: 'champs',
    titre: 'Les champs expliqués',
    Icon: IconSliders,
    contenu: (
      <dl className="flex flex-col gap-4 text-sm text-gray-600">
        <div>
          <dt className="font-semibold text-gray-700">Matière</dt>
          <dd className="mt-0.5 flex flex-col gap-2">
            <span>A-SCHOOL propose 12 matières : Français, Histoire-Géographie, Mathématiques, Physique-Chimie, SVT, SES, NSI, Philosophie, Langues vivantes, Technologie, Arts et EPS.</span>
            <span><strong>Votre matière de profil</strong> est définie à l'inscription et modifiable via "Mon profil" — c'est votre identité par défaut, elle persiste d'une connexion à l'autre.</span>
            <span><strong>Le sélecteur de matière dans les paramètres</strong> vous permet de changer de matière pour la session en cours uniquement, sans toucher à votre profil. Utile si vous intervenez ponctuellement dans une autre discipline ou souhaitez tester des activités d'une autre matière.</span>
          </dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Niveau</dt>
          <dd className="mt-0.5">Le niveau scolaire de vos élèves, de la 6e à la Terminale. Influence le vocabulaire et la complexité de l'activité. Votre niveau habituel est mémorisé d'une session à l'autre. Le niveau Supérieur (BTS, prépa) est en cours de développement.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Type d'activité</dt>
          <dd className="mt-0.5">Le genre d'exercice à produire — varie selon la matière (compréhension, vocabulaire, résumé, exercices…). Chaque type génère un format différent.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Nombre de questions</dt>
          <dd className="mt-0.5">Le nombre d'items dans l'activité. Disponible selon le type choisi.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Avec correction</dt>
          <dd className="mt-0.5">Si activé, A-SCHOOL ajoute la correction complète sous l'activité — pratique pour préparer votre cours ou gagner du temps sur la correction.</dd>
        </div>
      </dl>
    ),
  },
  {
    id: 'conseils',
    titre: 'Conseils pour un bon texte source',
    Icon: IconBulb,
    contenu: (
      <ul className="flex flex-col gap-2 text-sm text-gray-600">
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>200 à 1 000 mots</strong> — en dessous le résultat manque de matière, au-dessus il peut perdre en précision.</span></li>
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Texte structuré</strong> — préférez des paragraphes rédigés à des listes ou des tableaux.</span></li>
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Langue française</strong> — A-SCHOOL est optimisé pour les textes en français.</span></li>
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Sujet cohérent</strong> — un extrait avec un thème clair donne de meilleurs résultats qu'un assemblage de fragments.</span></li>
        <li className="flex gap-2"><span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span><span><strong>Régénérez si nécessaire</strong> — le bouton "Régénérer" relance une nouvelle génération avec les mêmes paramètres, sans ressaisir le texte.</span></li>
      </ul>
    ),
  },
  {
    id: 'conseils-utilisation',
    titre: 'Conseils d\'utilisation',
    Icon: IconTarget,
    contenu: (
      <ul className="flex flex-col gap-3 text-sm text-gray-600">
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Choisissez le type d'activité selon votre objectif</strong> — "Questions de compréhension" pour vérifier la lecture, "Production d'écrit" pour entraîner à la rédaction, "Fiche de révision" pour synthétiser un chapitre.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Précisez le sous-type</strong> — plus votre choix est ciblé (ex : "inférence" plutôt que "mélange"), plus le résultat est adapté à ce que vous cherchez.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Sauvegardez les activités qui vous conviennent</strong> — chaque génération sauvegardée est un exemple que A-SCHOOL retient pour apprendre votre style (voir "A-SCHOOL apprend votre style").</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Activez "Avec correction"</strong> pour obtenir le corrigé en même temps que l'activité — gain de temps direct pour la préparation de cours.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Relisez avant de distribuer</strong> — A-SCHOOL produit une base solide, mais un regard professionnel sur le résultat garantit la pertinence pédagogique.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Utilisez l'historique</strong> — retrouvez une ancienne activité dans "Mes activités" et rechargez-la en un clic pour la réutiliser ou la faire évoluer.</span>
        </li>
        <li className="flex gap-2">
          <span className="font-bold shrink-0" style={{ color: 'var(--bleu)' }}>·</span>
          <span><strong>Régénérez sans hésiter</strong> — chaque génération est différente. Si le premier résultat ne correspond pas, une seconde tentative avec le même texte peut donner exactement ce que vous cherchez.</span>
        </li>
      </ul>
    ),
  },
  {
    id: 'espace',
    titre: 'Votre espace & retours',
    Icon: IconUser,
    contenu: (
      <dl className="flex flex-col gap-4 text-sm text-gray-600">
        <div>
          <dt className="font-semibold text-gray-700">Mon profil</dt>
          <dd className="mt-0.5">Modifiez votre prénom, nom, matière et niveau par défaut depuis le menu latéral. Ces données sont enregistrées sur votre compte et persistent d'une session à l'autre.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Mes activités</dt>
          <dd className="mt-0.5">Toutes vos générations sont sauvegardées automatiquement. Cliquez sur une activité pour recharger le texte source, les paramètres et le résultat en un clic.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Notez A-SCHOOL</dt>
          <dd className="mt-0.5">Donnez votre avis en 30 secondes — de 1 à 5 étoiles, avec un commentaire optionnel. Vos retours nous aident directement à améliorer la plateforme.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Envoyer un feedback</dt>
          <dd className="mt-0.5">Signalez un problème, proposez une amélioration ou posez une question. Si un type d'activité vous manque, c'est ici que vous pouvez le suggérer.</dd>
        </div>
      </dl>
    ),
  },
  {
    id: 'problemes',
    titre: 'Trucs et astuces',
    Icon: IconAlert,
    contenu: (
      <dl className="flex flex-col gap-4 text-sm text-gray-600">
        <div>
          <dt className="font-semibold text-gray-700">Le bouton "Générer" ne fait rien</dt>
          <dd className="mt-0.5">Vérifiez que la zone de texte source n'est pas vide. Le bouton est grisé tant que le texte manque.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Le résultat ne correspond pas à mes attentes</dt>
          <dd className="mt-0.5">Essayez un autre type d'activité, ajustez le niveau, ou utilisez un texte source plus clair et mieux structuré. Le bouton "Régénérer" relance une nouvelle génération avec les mêmes paramètres.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Un type d'activité est absent ou incorrect</dt>
          <dd className="mt-0.5">Utilisez "Envoyer un feedback" dans le menu latéral pour le signaler. C'est directement intégré au développement de la plateforme.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Le niveau Supérieur affiche un message de développement</dt>
          <dd className="mt-0.5">Les activités pour le niveau Supérieur (BTS, prépa, licence) sont en cours de développement. Les autres niveaux (6e à Terminale) sont pleinement opérationnels.</dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">La traduction automatique perturbe les activités</dt>
          <dd className="mt-0.5">
            A-SCHOOL génère des activités en français. Si vous laissez votre navigateur traduire la page,
            les paramètres envoyés à la génération sont altérés — les activités produites seront incohérentes
            ou de mauvaise qualité.<br />
            <strong>Solution :</strong> lorsque Chrome ou Edge propose de traduire, cliquez sur{' '}
            <strong>« Plus »</strong> puis <strong>« Ne jamais traduire ce site »</strong>.
          </dd>
        </div>
        <div>
          <dt className="font-semibold text-gray-700">Erreur lors de la génération</dt>
          <dd className="mt-0.5">Vérifiez votre connexion internet. Si le problème persiste, contactez <a href="mailto:contact@aschool.fr" className="underline hover:text-gray-800">contact@aschool.fr</a>.</dd>
        </div>
      </dl>
    ),
  },
  {
    id: 'bibliotheque-exemples',
    titre: 'Les exemples de la Bibliothèque',
    Icon: IconBook,
    contenu: (
      <div className="flex flex-col gap-4 text-sm text-gray-600">
        <p>
          La Bibliothèque contient des <strong>activités d'exemple générées par A-SCHOOL</strong>,
          disponibles dès votre première connexion. Elles sont là pour vous montrer concrètement
          ce que l'outil peut produire dans chaque matière.
        </p>
        <div className="rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide bg-gray-50">
            Ce que contient la bibliothèque d'exemples
          </div>
          <div className="px-4 py-3 flex flex-col gap-2">
            <p><strong>24 activités</strong> — 2 par matière, couvrant les 12 matières de la plateforme.</p>
            <p>Chaque exemple est une activité réelle, générée avec un texte source représentatif du niveau indiqué. Vous pouvez les charger comme point de départ et les adapter.</p>
            <p>Elles sont signées <strong>Équipe A-SCHOOL</strong> et identifiées par un badge <span style={{ fontSize: 10, fontWeight: 600, color: '#7c3aed', background: '#f5f3ff', border: '1px solid #ddd6fe', borderRadius: 99, padding: '1px 7px' }}>Exemple</span> dans la liste.</p>
          </div>
        </div>
        <p className="text-xs text-gray-400 italic">
          Ces exemples peuvent être masqués par l'administrateur si nécessaire — ils restent visibles par défaut pour tous les professeurs connectés.
        </p>
      </div>
    ),
  },
]

export default function Aide() {
  const [open, setOpen] = useState('comment')

  return (
    <div className="flex flex-col gap-3 max-w-2xl">
      <h2 className="text-base font-semibold text-gray-800 mb-1">Aide</h2>
      {sections.map(s => {
        const isOpen = open === s.id
        return (
          <div
            key={s.id}
            className="bg-white rounded-lg border overflow-hidden shadow-sm"
            style={{
              borderColor: isOpen ? 'var(--bleu)' : '#e5e7eb',
              borderLeftWidth: isOpen ? '3px' : '1px',
              transition: 'border-color 0.2s ease',
            }}
          >
            <button
              onClick={() => setOpen(isOpen ? null : s.id)}
              title={isOpen ? 'Réduire cette section' : 'Développer cette section'}
              className="w-full flex items-center gap-3 px-5 py-4 text-sm font-medium hover:bg-gray-50 transition-colors"
              style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', color: isOpen ? 'var(--bleu)' : '#1f2937' }}
            >
              <span style={{ color: isOpen ? 'var(--bleu)' : '#6b7280', transition: 'color 0.2s ease' }}>
                <s.Icon />
              </span>
              <span className="flex-1">{s.titre}</span>
              <span style={{ color: isOpen ? 'var(--bleu)' : '#9ca3af', transition: 'color 0.2s ease' }}>
                <ChevronDown open={isOpen} />
              </span>
            </button>
            <div
              style={{
                display: 'grid',
                gridTemplateRows: isOpen ? '1fr' : '0fr',
                transition: 'grid-template-rows 0.25s ease',
              }}
            >
              <div style={{ overflow: 'hidden' }}>
                <div className="px-5 pb-5 border-t border-gray-100 pt-4">
                  {s.contenu}
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
