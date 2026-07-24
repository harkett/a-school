"""État de PREMIÈRE MISE EN ROUTE de l'admin — agrégateur LECTURE SEULE (get, zéro copie).

Un seul endpoint qui DÉRIVE en direct les 8 étapes depuis les VRAIES tables : aucune colonne
neuve, aucun drapeau stocké, aucune donnée recopiée. Chaque `fait` = « la donnée existe en base »
au moment de l'appel. Alimente l'écran assistant « Mise en route ».

Règle 16 : la clé API n'est JAMAIS lue ni renvoyée — on ne remonte que sa PRÉSENCE (booléen).
Règle 23 : les messages sont humains (le prof/l'admin comprend et sait quoi faire).
"""
import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models_db import (
    Cycle, Niveau, Matiere, MatiereNiveau, Referentiel, ReferentielChunk,
    ReferentielActiviteType, EmailEnvoi, ActiviteSauvegardee,
)
from backend.systeme.admin import _require_admin, get_ai_provider, get_ai_model

router = APIRouter()

# Nom de la variable d'environnement qui porte la clé TEXTE de chaque fournisseur
# (cf. backend/llm/generator.py : _groq lit GROQ_API_KEY, _anthropic CLAUDE_API_KEY_TEXTE).
# On lit la PRÉSENCE (os.getenv non vide), jamais la valeur.
_CLE_ENV_FOURNISSEUR = {
    "groq": "GROQ_API_KEY",
    "anthropic": "CLAUDE_API_KEY_TEXTE",
}


@router.get("/admin/mise-en-route/etat", dependencies=[Depends(_require_admin)])
def etat_mise_en_route(db: Session = Depends(get_db)):
    """Les 8 étapes de mise en route, chacune dérivée d'un get sur les vraies tables.

    `fait` = la donnée existe en base. `complet` = les 8 sont faites. Zéro copie : rien n'est
    stocké, tout est relu à chaque ouverture. Aucun secret renvoyé (présence de clé seulement)."""

    # 1 — Fournisseur + modèle IA + clé du fournisseur présente (préalable à toute analyse IA).
    provider = (get_ai_provider(db) or "").strip()
    model = (get_ai_model(db) or "").strip()
    env_name = _CLE_ENV_FOURNISSEUR.get(provider)
    cle_presente = bool(env_name and os.getenv(env_name, "").strip())
    ia_ok = bool(provider and model and cle_presente)

    # 2 — Programme (semé) : cycles / niveaux / matières / paires actives.
    prog_ok = (
        db.query(Cycle).count() > 0
        and db.query(Niveau).count() > 0
        and db.query(Matiere).count() > 0
        and db.query(MatiereNiveau).filter(MatiereNiveau.actif == True).count() > 0
    )

    # 3 — Au moins un référentiel déposé (un PDF enregistré sur un couple).
    depot_ok = db.query(Referentiel).filter(Referentiel.fichier.isnot(None)).count() > 0

    # 4 — Au moins un prompt de découpe validé (drapeau sur le couple).
    prompt_ok = (db.query(Referentiel)
                   .filter(Referentiel.prompt_decoupe_valide == True).first() is not None)

    # 5 — Au moins une découpe validée AVEC ses chunks (decoupe_valide posé après ingestion réussie).
    decoupe_ok = (
        db.query(Referentiel).filter(Referentiel.decoupe_valide == True).first() is not None
        and db.query(ReferentielChunk).count() > 0
    )

    # 6 — Au moins un type d'activité coché pour un référentiel (sinon le prof n'a que le défaut).
    types_ok = (db.query(ReferentielActiviteType)
                  .filter(ReferentielActiviteType.actif == True).first() is not None)

    # 7 — Au moins un email envoyé avec succès (le test SMTP).
    email_ok = (db.query(EmailEnvoi)
                  .filter(EmailEnvoi.statut == "envoye").first() is not None)

    # 8 — Au moins une activité générée et sauvegardée (preuve bout-en-bout).
    bout_ok = db.query(ActiviteSauvegardee).count() > 0

    etapes = [
        {"num": 1, "cle": "ia", "fait": ia_ok, "ecran": "/admin/parametres/generation",
         "titre": "Choisir le fournisseur d'IA et son modèle",
         "message": "Choisissez votre fournisseur d'IA, son modèle, et vérifiez que sa clé est en "
                    "place. Sans ça, aucune analyse automatique ne peut fonctionner."},
        {"num": 2, "cle": "programme", "fait": prog_ok, "ecran": "/admin/programmes",
         "titre": "Vérifier le programme officiel",
         "message": "Le programme officiel (cycles, niveaux, matières) est déjà en place. Rien à "
                    "faire, sauf si vous souhaitez le compléter."},
        {"num": 3, "cle": "referentiel", "fait": depot_ok, "ecran": "/admin/referentiels",
         "titre": "Déposer un référentiel (PDF)",
         "message": "Déposez le PDF du référentiel d'un niveau pour commencer à construire les contenus."},
        {"num": 4, "cle": "prompt", "fait": prompt_ok, "ecran": "/admin/referentiels",
         "titre": "Valider le plan de découpe",
         "message": "Relisez puis validez le plan de découpe proposé par l'IA pour ce référentiel."},
        {"num": 5, "cle": "decoupe", "fait": decoupe_ok, "ecran": "/admin/referentiels",
         "titre": "Lancer et valider la découpe",
         "message": "Lancez puis validez la découpe : c'est elle qui rend le référentiel réellement utilisable."},
        {"num": 6, "cle": "types", "fait": types_ok, "ecran": "/admin/referentiels",
         "titre": "Contrôler les types d'activité",
         "message": "Après la découpe, l'IA rattache elle-même les types d'activité lus dans le document. "
                    "Contrôlez-les (retirez, ajoutez) — sinon le prof n'aura que le type générique."},
        {"num": 7, "cle": "email", "fait": email_ok, "ecran": "/admin/parametres/email",
         "titre": "Tester l'envoi d'email",
         "message": "Envoyez un email de test : c'est l'envoi qui permet la vérification d'inscription des profs."},
        {"num": 8, "cle": "bout_en_bout", "fait": bout_ok, "ecran": "",
         "titre": "Test complet côté prof",
         "message": "Créez un compte prof, vérifiez l'email, générez une activité : la preuve que toute "
                    "la chaîne fonctionne."},
    ]
    return {"complet": all(e["fait"] for e in etapes), "etapes": etapes}
