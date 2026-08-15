# -*- coding: utf-8 -*-
"""LA VEILLE DES TARIFS — un relevé par jour, et un courriel quand un prix a bougé.

CE QU'ELLE ÉVITE. Le 31 août 2026, `claude-sonnet-5` quitte son tarif d'introduction : 2 / 10
dollars deviennent 3 / 15. Rien ne nous préviendra. Sans veille, notre base annoncerait pendant des
mois un coût inférieur de moitié à la réalité — et c'est ce chiffre-là qui sert à comparer les
fournisseurs et à décider lequel appelle en premier.

CE QU'ELLE FAIT TOUTE SEULE : écrire les nouveaux tarifs. Un prix est un FAIT du fournisseur, pas
une proposition ; le garder pour validation reviendrait à conserver un chiffre qu'on sait faux.

CE QU'ELLE FAIT ENSUITE : reclasser l'ordre d'appel sur le tarif. Le gratuit reste en tête, puis
les payants du moins cher au plus cher. Ce reclassement a d'abord été mis derrière un bouton
« Appliquer » que l'administrateur devait trouver, comprendre et actionner — pour confirmer ce que
les chiffres disaient déjà. Un fournisseur devenu moins cher passe maintenant devant tout seul, et
le courriel annonce le nouvel ordre. Personne n'a rien à valider.

CE QUE ÇA COÛTE : rien. Une page web est lue et analysée par une expression régulière ; aucun
modèle de langage n'est appelé, aucun euro n'est dépensé, aucune clé n'est utilisée.

PÉRIODICITÉ : une fois par jour. Les tarifs des fournisseurs d'IA changent quelques fois par an,
toujours à l'occasion d'un événement (nouveau modèle, fin de promotion) : un relevé quotidien est
déjà généreux, et un relevé horaire ne trouverait jamais rien de plus.
"""
import logging
import os

from backend.core.database import session_pour, SCHEMA_REEL
from backend.core.models_db import AiFournisseur, AiModele
from backend.supervision.alerts import create_alert
from backend.systeme.releve_tarifs import lire_page, relever

log = logging.getLogger(__name__)

# Le titre est STABLE : c'est la clé anti-flood de `create_alert`. Le détail voyage dans le sujet.
TITRE = "Un tarif d'IA a changé chez un fournisseur"


def _ligne_du_changement(c: dict) -> str:
    """Une ligne lisible par changement, avec l'ancien prix ET le nouveau.

    Les deux, parce qu'un prix seul ne dit pas s'il monte ou s'il descend — et c'est la seule
    chose qui intéresse celui qui lit le message."""
    def bout(quoi, avant, apres):
        return f"{quoi} {avant if avant is not None else '—'} → {apres}"
    return (f"  - {c['fournisseur']} — {c['modele']} : "
            + bout("entrée", c["avant_entree"], c["apres_entree"]) + " ; "
            + bout("sortie", c["avant_sortie"], c["apres_sortie"])
            + f" {c['devise']} par million.")


def _message(changements: list[dict], sources: set[str], ordre: list[str]) -> str:
    """Le courriel. Écrit pour quelqu'un qui a oublié ce qu'est cet écran — dans un an, ce sera le
    cas. D'où le chemin complet, le nom exact du bouton, et ce qui se passe si on ne fait rien."""
    app = os.getenv("APP_URL", "https://aschool.fr").rstrip("/")
    return (
        "Le relevé quotidien des tarifs a trouvé un prix différent de celui enregistré.\n"
        "LES NOUVEAUX TARIFS ONT DÉJÀ ÉTÉ ÉCRITS EN BASE — un prix est un fait du fournisseur, "
        "il n'y a rien à valider.\n\n"
        "Ce qui a changé :\n"
        + "\n".join(_ligne_du_changement(c) for c in changements)
        + "\n\nRelevé sur : " + ", ".join(sorted(sources)) + "\n\n"
        "L'ORDRE D'APPEL A SUIVI. L'application essaie les fournisseurs l'un après l'autre et "
        "s'arrête au premier qui répond ; ce classement se règle sur le tarif, le gratuit "
        "toujours en tête. Vous n'avez rien à valider.\n\n"
        "Nouvel ordre d'appel :\n"
        + "\n".join(f"  {i}. {nom}" for i, nom in enumerate(ordre, start=1))
        + f"\n\nPour le voir : {app}/admin/ia/fournisseurs"
    )


def _reclasser(db, fournisseurs) -> list[str]:
    """Range les fournisseurs : le gratuit d'abord, puis les payants du moins cher au plus cher.

    LE GRATUIT PASSE TOUJOURS EN PREMIER, quel que soit le tarif des autres : essayer un service
    qui facture avant un service gratuit, c'est dépenser pour ce qu'on avait pour rien.

    LE PRIX D'UN FOURNISSEUR est celui du modèle qu'on appelle vraiment chez lui — son recommandé
    actif — entrée plus sortie, ramenées en euros. Comparer des francs suisses à des dollars sans
    les convertir se tromperait de 15 %. Un fournisseur dont le tarif n'est pas relevé passe en fin
    de liste : on ne le déclare ni cher ni bon marché, on ne sait pas.

    Rend l'ordre final, pour que le courriel puisse le dire."""
    from backend.core.devises import en_euros
    from backend.core.models_db import AiModele

    def cout(code):
        modeles = [m for m in db.query(AiModele).filter(AiModele.fournisseur == code).all() if m.actif]
        modeles.sort(key=lambda m: (not m.recommande, m.ordre))
        if not modeles:
            return None
        m = modeles[0]
        e, so = en_euros(m.cout_entree_million, m.devise), en_euros(m.cout_sortie_million, m.devise)
        return None if e is None or so is None else e + so

    gratuits = [f for f in fournisseurs if f.tarification == "gratuit"]
    payants = [f for f in fournisseurs if f.tarification != "gratuit"]
    # Tarif inconnu : `inf`, donc en fin de liste, sans casser la comparaison.
    payants.sort(key=lambda f: (cout(f.code) if cout(f.code) is not None else float("inf")))

    for rang, f in enumerate(gratuits + payants, start=1):
        f.ordre = rang
    return [f.label for f in gratuits + payants]


def veiller(destinataire: str | None = None) -> list[dict]:
    """Relève les tarifs de tous les fournisseurs qui ont une adresse, écrit, et alerte.

    `destinataire` : à qui écrire, quand l'administrateur l'a précisé sur la fiche de la tâche.
    Vide = l'adresse d'administration du serveur.

    Rend la liste des changements — vide quand rien n'a bougé, ce qui est le cas ordinaire."""
    db = session_pour(SCHEMA_REEL)
    changements, sources, ordre = [], set(), []
    try:
        fournisseurs = db.query(AiFournisseur).filter(AiFournisseur.actif.is_(True)).all()
        for f in fournisseurs:
            if not (f.lien_tarifs or "").strip():
                continue
            try:
                page = lire_page(f.lien_tarifs)
            except ValueError as e:
                # Une page injoignable n'est pas un incident de tarif : on le note et on continue
                # avec les autres fournisseurs. Alerter là-dessus tous les jours noierait le
                # message qui compte vraiment.
                log.warning("Veille des tarifs — %s injoignable : %s", f.code, e)
                continue

            modeles = db.query(AiModele).filter(AiModele.fournisseur == f.code).all()
            cherches = {m.modele: (m.nom_fournisseur or m.modele) for m in modeles}
            releves = relever(page, list(set(cherches.values())))

            for m in modeles:
                trouve = releves.get(cherches[m.modele])
                if not trouve:
                    continue
                avant_e = float(m.cout_entree_million) if m.cout_entree_million is not None else None
                avant_s = float(m.cout_sortie_million) if m.cout_sortie_million is not None else None
                devise = trouve["devise"] or m.devise
                if (avant_e, avant_s, m.devise) == (trouve["entree"], trouve["sortie"], devise):
                    continue
                m.cout_entree_million = trouve["entree"]
                m.cout_sortie_million = trouve["sortie"]
                m.devise = devise
                changements.append({
                    "fournisseur": f.label, "modele": m.modele, "devise": devise,
                    "avant_entree": avant_e, "avant_sortie": avant_s,
                    "apres_entree": trouve["entree"], "apres_sortie": trouve["sortie"],
                })
                sources.add(f.lien_tarifs)
        # Le reclassement ne se fait QUE si un prix a bougé : sans changement il n'y a rien à
        # reclasser, et réécrire `ordre` chaque nuit brouillerait la lecture de ce qui a
        # réellement changé.
        if changements:
            ordre = _reclasser(db, fournisseurs)
        db.commit()
    except Exception:
        db.rollback()
        log.exception("Veille des tarifs interrompue")
        return []
    finally:
        db.close()

    if changements:
        # « info » et non « warning » : rien n'est cassé, il n'y a pas d'urgence. C'est une
        # nouvelle à lire, pas une panne à réparer.
        create_alert("info", TITRE, _message(changements, sources, ordre),
                     sujet_detail=", ".join(sorted({c["fournisseur"] for c in changements})),
                     destinataire=destinataire)
        log.info("Veille des tarifs : %s changement(s) écrit(s)", len(changements))
    return changements
