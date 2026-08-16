"""Le tableau de bord annonce des fonctionnalités — ce test vérifie qu'elles existent encore.

LA PANNE QU'IL EMPÊCHE. La table `fonctionnalites` porte les lignes « fait », « en cours » et
« à venir » que l'écran d'état affiche telles quelles. Rien ne les reliait au code. Le 10/08/2026
la ligne « Labo » annonçait encore `fait` alors que l'écran, ses treize routes et sa suite de
tests avaient été supprimés le matin même. Un écran d'état qui se trompe ne lève aucune erreur :
il se contente de mentir, et personne ne l'apprend avant de cliquer.

CE QU'IL PROUVE, et comment. Il ne lit pas la base — la table est déclarative, elle se sème par
migration, et c'est donc les MIGRATIONS qu'il lit :

  - chaque fichier cité par `c3a7e9b1d854.COMPOSANTS` existe sur le disque ; supprimez un écran
    sans toucher sa ligne, et ce test tombe ;
  - aucune migration n'insère une ligne `fait` ou `en_cours` sans dire quel fichier la rend ;
    sans ce second sens, la prochaine fonctionnalité livrée redeviendrait invérifiable.

CE QU'IL NE PROUVE PAS : que la fonctionnalité MARCHE. Ça, ce sont les suites métier. Ici on tient
la seule chose qu'une table déclarative puisse garantir — qu'elle ne parle pas d'un écran disparu.

Lancer : docker compose exec backend python -m pytest tests/test_tableau_de_bord_dit_vrai.py -q
"""
import importlib.util
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
FRONTEND = RACINE / "frontend"
VERSIONS = RACINE / "alembic" / "versions"
MIGRATION_COMPOSANTS = "c3a7e9b1d854_chaque_fonctionnalite_dit_son_ecran.py"


def _charger(chemin: Path):
    spec = importlib.util.spec_from_file_location(f"_mig_{chemin.stem}", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _retirees() -> set:
    """Les lignes qu'une migration POSTÉRIEURE a supprimées.

    La table de correspondance est figée dans `c3a7e9b1d854` — on ne réécrit pas une migration
    déjà passée. Quand un écran est supprimé, sa migration retire la ligne de la base ET le
    déclare ici, par un `FONCTIONNALITES_RETIREES = {(écran, nom), ...}` en tête de fichier.
    Premier cas : `c9f5a3e8d1b6`, l'écran « Consulter un référentiel » (16/08/2026).

    Le garde-fou ne s'affaiblit pas : une ligne encore en base qui cite un fichier disparu fait
    toujours tomber le test. Seule une suppression ASSUMÉE, écrite dans une migration, sort du
    compte — et c'est exactement ce que le message d'erreur demande de faire.
    """
    retirees = set()
    for f in sorted(VERSIONS.glob("*.py")):
        if "FONCTIONNALITES_RETIREES" not in f.read_text(encoding="utf-8", errors="replace"):
            continue
        retirees |= set(getattr(_charger(f), "FONCTIONNALITES_RETIREES", ()))
    return retirees


def _composants() -> dict:
    """La table de correspondance, lue dans la migration qui la sème, moins les lignes
    supprimées depuis."""
    composants = _charger(VERSIONS / MIGRATION_COMPOSANTS).COMPOSANTS
    retirees = _retirees()
    return {cle: chemin for cle, chemin in composants.items() if cle not in retirees}


def test_la_table_de_correspondance_est_lisible():
    """Garde-fou du test lui-même : si la migration était renommée, les deux suivants
    passeraient en annonçant une cohérence qu'ils n'auraient rien vérifiée."""
    c = _composants()
    assert len(c) >= 40, (
        f"La correspondance ligne -> écran ne compte que {len(c)} entrées. La migration "
        f"« {MIGRATION_COMPOSANTS} » a dû être renommée ou vidée — remettez ce test sur sa piste."
    )


def test_aucun_ecran_annonce_nexiste_plus():
    """Le sens qui s'installe tout seul : l'écran est supprimé, la ligne reste."""
    disparus = [f"{ecran} / {nom} -> {chemin}"
                for (ecran, nom), chemin in sorted(_composants().items())
                if not (FRONTEND / chemin).is_file()]
    assert not disparus, (
        "Ces fonctionnalités désignent un fichier qui n'existe plus :\n  "
        + "\n  ".join(disparus)
        + "\nL'écran a disparu — retirez la ligne par migration (c'est ce qu'a fait "
          "`b8f2d6c4a917` pour le Labo), ou corrigez le chemin s'il a seulement déménagé."
    )


def test_aucune_migration_ne_livre_une_ligne_muette():
    """L'autre sens : une ligne « fait » qui ne dit pas quel fichier la rend est invérifiable.
    C'était l'état de TOUTES les lignes avant le 10/08/2026, et c'est ce qui a laissé le Labo
    s'annoncer livré pendant des heures."""
    fautives = []
    for f in sorted(VERSIONS.glob("*.py")):
        src = f.read_text(encoding="utf-8", errors="replace")
        if "INSERT INTO fonctionnalites" not in src:
            continue
        # SEULEMENT `upgrade()`. Un `downgrade()` remet l'état d'avant, écran compris : lui
        # réclamer un composant reviendrait à exiger qu'il cite un fichier qu'il vient de
        # supprimer — c'est le cas de `b8f2d6c4a917`, qui restaure la ligne du Labo.
        aller = src.split("def downgrade(")[0]
        if "INSERT INTO fonctionnalites" not in aller:
            continue
        for insert in re.findall(r"INSERT INTO fonctionnalites\s*\(([^)]*)\)", aller):
            colonnes = {c.strip() for c in insert.split(",")}
            if "composant" in colonnes:
                continue
            # une migration qui ne pose que des lignes « à venir » n'a rien à citer
            if re.search(r"'(fait|en_cours)'", aller):
                fautives.append(f"{f.name} : INSERT sans colonne `composant`")
    assert not fautives, (
        "Ces migrations livrent une fonctionnalité sans dire quel fichier la rend :\n  "
        + "\n  ".join(fautives)
        + "\nAjoutez `composant` (chemin depuis `frontend/`) à l'INSERT — sans lui, la ligne "
          "s'annonce faite et rien ne peut la contredire."
    )
