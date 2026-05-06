import { Link } from 'react-router-dom'

export default function MentionsLegales() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#f0f4f8' }}>

      <header className="flex items-center px-6 py-4" style={{ backgroundColor: 'var(--bleu)' }}>
        <span className="text-white font-bold text-xl tracking-tight">
          <span style={{ color: 'var(--bordeaux)' }}>A</span>-SCHOOL
        </span>
        <span className="text-white text-base ml-3" style={{ opacity: 0.75 }}>
          | Générateur d'activités pédagogiques
        </span>
      </header>

      <div className="flex-1 flex justify-center p-6">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-2xl">

          <h1 className="text-lg font-semibold text-gray-800 mb-6">Mentions légales</h1>

          <Section titre="Éditeur du site">
            <p>Ce site est édité par <strong>AFIA</strong>.</p>
            <p>Contact : <a href="mailto:contact@aschool.fr" className="underline text-gray-600 hover:text-gray-800">contact@aschool.fr</a></p>
          </Section>

          <Section titre="Hébergement">
            <p>Ce site est hébergé sur un serveur privé virtuel (VPS) exploité par <strong>AFIA</strong>.</p>
            <p>Adresse : <strong>school.afia.fr</strong></p>
          </Section>

          <Section titre="Propriété intellectuelle">
            <p>
              L'ensemble du contenu de ce site (textes, interfaces, logique applicative) est la propriété exclusive d'AFIA.
              Toute reproduction, représentation ou diffusion, totale ou partielle, sans autorisation écrite préalable est interdite.
            </p>
            <p>© 2026 AFIA — Tous droits réservés.</p>
          </Section>

          <Section titre="Données personnelles (RGPD)">
            <p>
              Dans le cadre de l'utilisation de l'application A-SCHOOL, les données suivantes sont collectées :
            </p>
            <ul className="list-disc list-inside mt-2 flex flex-col gap-1">
              <li>Adresse e-mail</li>
              <li>Matière enseignée</li>
              <li>Activités pédagogiques générées</li>
            </ul>
            <p className="mt-2">
              Ces données sont utilisées exclusivement pour le fonctionnement de l'application et ne sont transmises à aucun tiers.
            </p>
            <p>
              Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez d'un droit d'accès,
              de rectification et de suppression de vos données. Pour exercer ce droit, contactez :
              <a href="mailto:contact@aschool.fr" className="underline text-gray-600 hover:text-gray-800 ml-1">contact@aschool.fr</a>
            </p>
            <p>
              Les données sont conservées pendant la durée d'activité du compte. Elles sont supprimées sur demande
              ou après une période d'inactivité prolongée.
            </p>
          </Section>

          <Section titre="Cookies">
            <p>
              Ce site utilise uniquement des cookies techniques nécessaires au fonctionnement de l'authentification
              (tokens de session). Aucun cookie publicitaire ou de traçage n'est utilisé.
            </p>
          </Section>

          <div className="mt-8 pt-4 border-t border-gray-100">
            <Link to="/" className="text-xs text-gray-400 underline hover:text-gray-600">
              ← Retour à l'application
            </Link>
          </div>

        </div>
      </div>

      <footer className="py-3 text-center text-xs text-gray-400">
        A-SCHOOL · contact@aschool.fr
      </footer>
    </div>
  )
}

function Section({ titre, children }) {
  return (
    <div className="mb-6">
      <h2 className="text-sm font-semibold text-gray-700 mb-2">{titre}</h2>
      <div className="text-sm text-gray-500 flex flex-col gap-2">
        {children}
      </div>
    </div>
  )
}
