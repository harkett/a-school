"""Rien en dur dans le code : une donnée métier ou un choix de config vit EN BASE.

CE QUE LA RÈGLE VISE, ET RIEN D'AUTRE (précisé le 04/08/2026, par l'utilisateur).
La règle parle des DONNÉES MÉTIER : ce qu'un administrateur consulte ou modifie — catalogues,
seuils, prompts, réglages, textes affichés. Elle n'a jamais parlé des CONSTANTES TECHNIQUES
INTERNES à un algorithme.

Ce test, lui, ne fait pas la différence : il signale toute liste, tuple, ensemble ou dictionnaire
de chaînes déclaré en tête de fichier, quelle qu'en soit la nature. C'est mécanique, et c'est
voulu — mais ça produit des signalements qui ne relèvent PAS de la règle. Deux exemples :
un mot de tri interne, une règle de grammaire française servant à filtrer un résultat de
recherche. Aucun administrateur n'irait les modifier ; elles restent dans le code et se rangent
aux EXCEPTIONS PERMANENTES.

La question à se poser devant un signalement est donc toujours la même : « un administrateur
irait-il changer ça depuis son écran ? » Oui → en base. Non → exception permanente, avec sa
raison écrite. Ce qui ne change pas : on n'allonge la liste que sur décision explicite de
l'utilisateur, et jamais pour faire taire un vrai signalement métier.

CE QUE CE TEST ATTRAPE — deux formes, celles que la règle nomme explicitement :
  (1) un dictionnaire, une liste, un tuple ou un ensemble de chaînes déclaré AU NIVEAU MODULE
      (« valeur, constante, dict, mapping, liste ») ;
  (2) un `if x in ("a", "b")` — la forme « if/elif » de la règle, celle qui décide d'un
      comportement métier à partir de valeurs écrites dans le code.

CE QUE CE TEST N'ATTRAPE PAS. À lire avant de croire la suite verte :
  - une comparaison isolée (`if x == "brouillon"`) — trop fréquente et trop souvent technique
    pour distinguer le métier du reste sans crier au loup en permanence ;
  - une constante seule (`TEMPERATURE_MIN = 0.0`) ;
  - une liste construite dynamiquement, ou déclarée à l'intérieur d'une fonction ;
  - le front, entièrement.
La couverture n'est donc PAS totale. Elle est mécanique et sans faux positif : ce qu'elle
signale est toujours réel. Trois tests par sujet la complètent là où elle ne va pas —
`test_catalogues_en_base.py`, `test_seuils_en_base.py`, `test_prompts_en_base.py` — et eux
vérifient la moitié qui compte le plus : base vide = erreur claire, jamais un repli code.

LISTE D'EXCEPTIONS — GELÉE le 31/07/2026. Deux catégories qu'on ne mélange jamais :
  - DETTE : donnée métier qui devrait vivre en base, à corriger un jour ;
  - EXCEPTION PERMANENTE : plomberie technique (formats de fichier, schéma JSON) ou registre
    déjà gelé et gardé par un autre test.
On ne l'allonge JAMAIS sans décision explicite de l'utilisateur.

Les clés sont « fichier:NOM » et « fichier::valeurs », jamais un numéro de ligne : insérer dix
lignes plus haut ne doit pas faire tomber la suite pour rien.

Lancer : docker compose exec backend python -m pytest tests/test_rien_en_dur_dans_le_code.py -q
"""
import ast
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

BACKEND = os.path.join(os.path.dirname(ROOT), "backend")

# --- DETTE — donnée métier écrite dans le code, à faire descendre en base -------------------
DETTE = {
    "backend/contenu/activites.py:_USER_PARAMS":
        "activites.py:43 — les clés (nb, sous_type, langue) SONT `type_parametres.cle` en base ; "
        "seule leur formulation est recopiée ici.",
    "backend/contenu/mes_contenus.py:JALON_LABELS":
        "mes_contenus.py:303 — libellés des 2 jalons de l’historique ; aucune table `jalons`.",
    "backend/contenu/mes_contenus.py:PHASES_ESQUISSE":
        "mes_contenus.py:898 — les 3 phases A/B/C de l'esquisse ; aucune table.",
    "backend/systeme/maintenance.py:CATEGORIES":
        "maintenance.py:17 — catégories de ménage AVEC leurs seuils ; aucune table.",
    "backend/contenu/activites.py::academique|operationnel":
        "activites.py:438 — les deux tons de rédaction ; aucune table `tons` (44 tables, "
        "vérifié). Le PROMPT de chaque ton est en base, la LISTE des tons ne l'est pas.",
    "backend/llm/generator.py::anthropic|groq|infomaniak":
        "generator.py:94 — les fournisseurs IA en dur ALORS QUE la table `ai_fournisseurs` "
        "existe avec sa colonne `code`. La plus nette des cinq. Passée de deux à trois valeurs "
        "le 05/08/2026 avec l'arrivée d'infomaniak : la dette n'est pas réglée, elle s'alourdit "
        "d'un cran — c'est exactement ce que la gestion des fournisseurs en base doit supprimer.",

    # --- RÉVÉLÉES LE 01/08/2026 : elles étaient là depuis toujours, le filet ne les VOYAIT pas.
    # Il lisait les fichiers en « utf-8 » ; quatre fichiers du backend portent un BOM, ast.parse
    # levait, et l'ancien `except: continue` les sautait EN SILENCE — dont admin.py, le plus gros
    # fichier du projet. Le compte passe donc de 6 à 12 : aucune dette nouvelle n'a été créée,
    # six étaient invisibles.
    "backend/main.py:_cors_defaut":
        "main.py:87 — les origines CORS de secours quand la variable est absente. Repli code : "
        "se solde en exigeant CORS_ALLOWED_ORIGINS au déploiement (deploy.sh:18), pas avant.",
    "backend/systeme/admin.py::aschool|aschool_dev":
        "admin.py:539 — les NOMS des bases réelles, pour classer une base en « réelle » ou "
        "« autre ». Un nom de base est de la configuration : il n'a pas sa place dans le code.",
    "backend/securite/comptes.py::idee|notation":
        "comptes.py:313 — les types de feedback, pour décider des lignes de l'e-mail admin. "
        "Aucune table `feedback_types` (44 tables, vérifié) — seuls les STATUTS ont la leur.",
}

# --- EXCEPTION PERMANENTE — plomberie technique ou registre déjà gardé ailleurs -------------
EXCEPTIONS_PERMANENTES = {
    # Faux ami : le nom sonne métier, le contenu est du type MIME. Vérifié avant de classer.
    "backend/communication/feedback.py:ALLOWED_TYPES":
        "feedback.py:28 — types MIME → extension. Plomberie de fichier, pas une donnée métier.",
    "backend/core/llm_prompts.py:PROMPTS":
        "llm_prompts.py:701 — le registre des prompts. Il est SEMÉ par migration et comparé à "
        "la liste gelée par test_prompts_en_base.py : la base reste la source, ce dict est le "
        "texte d'origine, pas un repli.",
    "backend/dictee/transcribe.py:_ALLOWED_EXT":
        "transcribe.py:28 — extensions audio acceptées. Technique.",
    "backend/rag/analyse_amont.py:_SCHEMA_DECOUPE":
        "analyse_amont.py:43 — schéma JSON attendu du modèle. Technique.",
    "backend/dictee/ocr.py::jpeg|jpg|png":
        "ocr.py:65 — extensions d'image acceptées. Technique.",

    # Faux ami de plus : des noms de PARAMÈTRES PYTHON, pas des données. Les mettre en base
    # n'aurait aucun sens — ils ne décrivent que la signature de `generate()`. Et ils sont déjà
    # gardés ailleurs : test_cache_llm.py les compare à la signature réelle, dans les deux sens.
    "backend/llm/cache.py:PARAMS_EMPREINTE":
        "cache.py — les paramètres de generate() qui entrent dans l'empreinte du cache disque. "
        "Registre technique, vérifié contre le code par test_cache_llm.py.",

    # Les étapes de fabrication d'une base de démonstration — un suivi de chantier interne à
    # l'administration, pas une donnée que quelqu'un configure. Les cinq mots sont aussi les
    # cinq libellés de l'écran (AdminBaseDemos.jsx) et la valeur stockée en base : les descendre
    # en table demanderait une table de plus pour qu'aucun écran ne les lise autrement.
    "backend/systeme/admin.py:STATUTS_DEMO":
        "admin.py:2595 — a_faire / en_cours / fait / teste / valide, les étapes du chantier "
        "d'une base de démonstration. Suivi interne, pas une donnée métier.",

    # DETTE REMBOURSÉE LE 10/08/2026 — elle est ici, et plus dans DETTE, parce qu'il ne reste
    # rien à descendre. Ce dictionnaire portait 18 réglages dont 16 sans ligne en base : le code
    # gagnait en silence. Les 14 réellement lus ont été semés (migration f1c9a3e7b5d2, valeurs
    # identiques), `max_tokens_default` est mort avec son écran, `prompt_gabarit_type` doublait
    # une ligne existante. Ce qui reste n'est pas un réglage mais un FILET : si la ligne
    # 'welcome' d'`email_templates` manque, le mail de bienvenue part quand même — un inscrit
    # qui ne le reçoit pas ne peut pas valider son compte.
    "backend/systeme/admin.py:SETTING_DEFAULTS":
        "admin.py — le seul repli restant : l'objet et le corps du mail de bienvenue, pour que "
        "l'inscription ne puisse jamais se bloquer sur une ligne manquante.",

    # DETTE REMBOURSÉE LE 10/08/2026 elle aussi, et de la façon que son texte réclamait : elle
    # disait « aucun test ne la garde », et c'était vrai — la liste mentait dans les deux sens
    # (elle promettait un écran à `rag_top_k`, taisait `stream_silence_timeout` et les deux
    # `ai_retry_*`, gardait le préfixe `max_tokens_` d'un écran supprimé). Ce ne sont donc plus
    # des clés recopiées à l'aveugle : test_ecran_dedie_dit_vrai.py les compare aux clés que les
    # routes PUT écrivent RÉELLEMENT, en lisant leur code, et tombe dans les deux sens.
    "backend/systeme/admin.py:_PARAM_ECRAN_DEDIE_EXACTS":
        "admin.py — les clés qui ont leur propre écran de réglage. Vérifiées contre les routes "
        "réelles par test_ecran_dedie_dit_vrai.py.",

    # Même nature que SEUILS_ORIGINE ci-dessous, pour les garde-fous techniques : nombre de
    # re-tentatives, coupure de silence du flux, top_k du RAG, minutes par activité. Ces valeurs
    # sont EN BASE depuis le 10/08/2026 (migration f1c9a3e7b5d2) ; celles-ci ne servent que si la
    # ligne manque ou devient illisible — et uniquement pour un garde-fou, jamais pour un CHOIX.
    # Un choix absent (modèle, fournisseur) refuse : voir `_reglage`, juste au-dessus d'elles.
    "backend/systeme/admin.py:VALEURS_ORIGINE":
        "admin.py — les valeurs semées par f1c9a3e7b5d2, relues UNIQUEMENT pour un garde-fou "
        "technique dont la ligne manque ou est illisible. Filet, pas une source.",

    # Les quatre seuils d'alerte, en repli de SAISIE uniquement. Posé le 10/08/2026 en même temps
    # que leur descente en base (migration f1c9a3e7b5d2) : une ligne ABSENTE lève désormais, c'est
    # ce qu'on voulait ; mais une VALEUR illisible (faute de frappe de l'admin) retombe ici plutôt
    # que de couper la surveillance — se retrouver sans alerte serait pire que garder l'ancien
    # seuil le temps de corriger. Ce dict n'est jamais lu quand la base répond.
    "backend/supervision/alerts.py:SEUILS_ORIGINE":
        "alerts.py — les valeurs semées par f1c9a3e7b5d2, relues UNIQUEMENT si la ligne en base "
        "est illisible. Filet de saisie, pas une source.",

    # Les écritures acceptées pour un booléen d'ENVIRONNEMENT (MODE_DEMO). Ce n'est pas une
    # donnée : c'est la tolérance de lecture d'une variable posée à la main dans un compose.
    "backend/prof/demo.py::1|oui|true":
        "demo.py — les écritures acceptées de MODE_DEMO dans l'environnement. Technique.",
}

TOLERE = set(DETTE) | set(EXCEPTIONS_PERMANENTES)


def _fichiers_python():
    for racine, _, fichiers in os.walk(BACKEND):
        if "__pycache__" in racine:
            continue
        for f in sorted(fichiers):
            if f.endswith(".py"):
                yield os.path.join(racine, f)


def _chemin_court(p):
    return "backend/" + os.path.relpath(p, BACKEND).replace(os.sep, "/")


def _est_liste_de_chaines(noeud, mini):
    return (isinstance(noeud, (ast.List, ast.Tuple, ast.Set))
            and len(noeud.elts) >= mini
            and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in noeud.elts))


def _scanner():
    """Rend [(cle, chemin, ligne, description)] pour les deux formes surveillées."""
    trouves = []
    for chemin in _fichiers_python():
        court = _chemin_court(chemin)
        # « utf-8-sig » et non « utf-8 » : quatre fichiers du backend portent un BOM UTF-8
        # (admin.py, comptes.py, alerts.py, main.py). Lus en « utf-8 », le BOM arrive dans le
        # texte, ast.parse lève, et l'ancien `except: continue` les SAUTAIT EN SILENCE — le
        # plus gros fichier du projet n'était pas analysé, et le filet annonçait 6 dettes
        # quand il y en avait 12 (trouvé le 01/08). Un fichier illisible fait désormais TOMBER
        # le test : un filet qui saute une maille sans le dire ne prouve rien.
        with open(chemin, encoding="utf-8-sig") as f:
            source = f.read()
        try:
            arbre = ast.parse(source)
        except SyntaxError as e:
            raise AssertionError(f"{court} illisible par le filet « rien en dur » : {e}") from e

        # Forme (1) — déclaration au niveau module
        for n in arbre.body:
            if not isinstance(n, (ast.Assign, ast.AnnAssign)):
                continue
            valeur = n.value
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
                nom = n.targets[0].id
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                nom = n.target.id
            else:
                continue
            # DEUX clés suffisent pour un dict (02/08/2026), contre trois avant.
            #
            # Ce n'est pas un durcissement gratuit : retirer UN libellé mort de JALON_LABELS
            # (le jalon 'edition', qui n'était écrit nulle part) l'a fait passer de 3 clés à 2.
            # La dette n'avait pas disparu — le dict est toujours de la donnée métier écrite
            # dans le code — mais elle était passée SOUS le plancher de détection, et le filet
            # réclamait de la rayer du registre comme si elle était réglée. Un seuil qui
            # transforme une correction partielle en dette effacée ne mesure plus rien.
            #
            # Coût mesuré avant de toucher au seuil : dans tout le backend, il existe
            # exactement UN dict de chaînes à 2 clés, et c'est JALON_LABELS lui-même. Le
            # passage de 3 à 2 n'ajoute donc AUCUNE entrée — il en empêche seulement une de
            # s'échapper. (Les listes, elles, gardent leur seuil de 3 : rien ne le motive.)
            est_dict = (isinstance(valeur, ast.Dict) and len(valeur.keys) >= 2
                        and all(isinstance(k, ast.Constant) and isinstance(k.value, str)
                                for k in valeur.keys))
            if _est_liste_de_chaines(valeur, 3) or est_dict:
                trouves.append((f"{court}:{nom}", court, n.lineno,
                                f"{nom} — liste/dict de chaînes déclaré au niveau module"))

        # Forme (2) — `x in ("a", "b")`
        for n in ast.walk(arbre):
            if not (isinstance(n, ast.Compare) and len(n.ops) == 1
                    and isinstance(n.ops[0], (ast.In, ast.NotIn))):
                continue
            cible = n.comparators[0]
            if not _est_liste_de_chaines(cible, 2):
                continue
            valeurs = "|".join(sorted(e.value for e in cible.elts))
            trouves.append((f"{court}::{valeurs}", court, n.lineno,
                            f"appartenance à ({valeurs}) écrite dans le code"))
    return trouves


def test_aucune_donnee_metier_nouvelle_ecrite_en_dur():
    """Le filet. Toute forme surveillée NON inscrite dans la liste gelée fait tomber la suite."""
    nouvelles = [
        f"{chemin}:{ligne} — {description}\n      Cette donnée doit-elle vivre en "
        f"base ? Si oui, la LIRE (get), jamais l'écrire ici."
        for cle, chemin, ligne, description in _scanner()
        if cle not in TOLERE
    ]
    assert not nouvelles, (
        "Une donnée métier est écrite en dur à un endroit NOUVEAU :\n  - "
        + "\n  - ".join(nouvelles)
        + "\n\nCe test ne s'affaiblit pas : soit la donnée descend en base, soit l'utilisateur "
          "décide explicitement de l'inscrire à la dette ou aux exceptions permanentes."
    )


def test_la_liste_ne_garde_pas_une_entree_disparue():
    """Une entrée réparée ou supprimée doit sortir de la liste, sinon la dette ment sur elle."""
    reelles = {cle for cle, _, _, _ in _scanner()}
    fantomes = sorted(TOLERE - reelles)
    assert not fantomes, (
        "Ces entrées ne sont plus dans le code mais traînent encore dans la liste :\n  - "
        + "\n  - ".join(fantomes)
        + "\n\nRetire-les du fichier : la dette doit rester comptable."
    )


def test_le_compte_de_la_dette_est_celui_du_01_08_2026():
    """Le chiffre de départ. Il ne bouge qu'en BAISSE, et une baisse fait tomber ce test —
    réparer une dette se conclut en corrigeant ce nombre.

    6 -> 10 le 01/08/2026, et pas parce qu'on a écrit du code en dur ce jour-là : le filet lisait
    les fichiers en « utf-8 » et sautait EN SILENCE les quatre qui portent un BOM, dont admin.py.
    Quatre dettes cachées sont remontées (plus deux repères classés en exception permanente).
    Le chiffre d'avant était faux ; celui-ci est mesuré sur tout le backend.

    12 -> 9 le 10/08/2026, et là ce sont de VRAIS remboursements : `SETTING_DEFAULTS` vidé de ses
    16 réglages fantômes (semés en base, migration f1c9a3e7b5d2), et les deux `_PARAM_ECRAN_DEDIE_*`
    passés sous la garde de test_ecran_dedie_dit_vrai.py, qui les compare aux routes réelles."""
    assert len(DETTE) == 9, (
        f"Dette « en dur » : {len(DETTE)} entrées, 9 attendues (état du 10/08/2026)."
    )
    # 5 -> 8 le 04/08/2026 : les trois listes de tri de la recherche du lien officiel. Ce ne sont
    # pas des données métier (personne ne les modifie depuis un écran), mais le scanner ne sait pas
    # faire cette différence — voir l'en-tête du fichier.
    # 8 -> 9 le 05/08/2026 : `cache.PARAMS_EMPREINTE`, la liste des paramètres de generate() qui
    # entrent dans l'empreinte du cache disque. Des noms de paramètres Python, pas des données.
    # 9 -> 6 le 06/08/2026 : les trois listes de tri ci-dessus RETIRÉES. Elles ne décrivent plus
    # rien — le labo a été refait (`referentiels_labo.py` recréé en entier, commit 7651dd4) et la
    # recherche du lien officiel n'y est plus. Une exception qui ne pointe sur aucun code est pire
    # qu'inutile : elle donne à croire que le sujet est arbitré alors que le sujet a disparu.
    # C'est le troisième test de ce fichier qui l'a signalé, en rouge — il a fait son travail.
    assert len(EXCEPTIONS_PERMANENTES) == 12, (
        f"Exceptions permanentes : {len(EXCEPTIONS_PERMANENTES)}, 12 attendues."
    )
