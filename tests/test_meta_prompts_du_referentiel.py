"""Preuve — un référentiel NEUF arrive avec ses quatre méta-prompts VIDES, et c'est voulu.

CE QUE CE FICHIER GARDE. Le 08/08/2026, le repli sur un méta-prompt COMMUN a été retiré : un
méta regarde CE document pour écrire le prompt qui le lira, et le commun faisait chercher une
grille d'horaires dans un programme de crèche. Le 14/08, en voyant Collège · 4e arriver avec ses
quatre colonnes vides, on a cru à une panne et on a semé quatre GABARITS, recopiés sur le
référentiel à sa validation. Même faute, autre mécanisme : ces gabarits étaient tirés du BTS
CIEL option A, et celui de la découpe parle d'options, de règlement d'examen, de grille horaire
et de codes d'unités — dans un programme de collège. Retiré le jour même (c8f5a3d7e2b9).

UNE COLONNE VIDE N'EST PAS UNE PANNE : c'est l'état normal d'un référentiel qu'on vient de
déposer. Et un texte faux qui a l'air juste est PIRE que rien — vide, l'écran dit ce qu'il faut
charger ; rempli, personne ne va compter les occurrences de « option » pour voir qu'il décrit un
autre diplôme.

Ce que ces tests PROUVENT :
  1. le dépôt réel, déroulé de bout en bout, ne pose AUCUN méta-prompt ;
  2. plus aucun gabarit de méta-prompt au registre ;
  3. plus aucun en base — un `get_prompt` ne peut plus en ressusciter un.

Ni IA, ni réseau : le texte du PDF est mocké.

Lancer : docker compose exec backend python -m pytest tests/test_meta_prompts_du_referentiel.py -q
"""
import asyncio
import json
import uuid

from unittest.mock import patch

import backend.core.database as dbmod
import backend.pedagogie.referentiels_admin as refadm
from backend.core.llm_prompts import PROMPTS


COLONNES = ("prompt_meta_matieres", "prompt_meta_decoupe",
            "prompt_meta_types", "prompt_meta_precisions")

GABARITS = ("gabarit_meta_matieres", "gabarit_meta_decoupe",
            "gabarit_meta_types", "gabarit_meta_precisions")


def _couple():
    """Un cycle et un niveau à nous, jamais partagés avec un autre test."""
    from backend.core.models_db import Cycle, Niveau
    marque = uuid.uuid4().hex[:8]
    with dbmod.SessionLocal() as db:
        c = Cycle(nom=f"MP-Cycle-{marque}", ordre=90)
        db.add(c); db.commit(); db.refresh(c)
        n = Niveau(cycle_id=c.id, nom=f"MP-Niv-{marque}", ordre=90)
        db.add(n); db.commit(); db.refresh(n)
        return c.id, n.id


def _deposer(couple=None):
    """Déroule le VRAI flux de validation. Rend (id du référentiel, cycle_id, niveau_id)."""
    from backend.core.models_db import Referentiel
    cid, nid = couple or _couple()
    token = uuid.uuid4().hex
    (refadm.STAGING_DIR / f"{token}.pdf").write_bytes(b"%PDF-fake")
    body = refadm.ValiderBody(token=token, cycle_id=cid, niveau_id=nid,
                              fichier_origine="ref-officiel.pdf", source="dépôt manuel")
    try:
        with patch("backend.rag.extraction.extraire_texte", return_value="TEXTE ÉPURÉ"), \
             patch("pdfplumber.open") as ouvrir:
            ouvrir.return_value.__enter__.return_value.pages = [object()]
            reponse = refadm.valider_flux(body)

            async def _lire():
                return [json.loads(l) async for l in reponse.body_iterator if l.strip()]

            msgs = asyncio.run(_lire())
    finally:
        (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)

    fin = [m["fin"] for m in msgs if "fin" in m]
    assert len(fin) == 1 and fin[0]["ok"] is True, msgs
    with dbmod.SessionLocal() as db:
        ref = db.query(Referentiel).filter(Referentiel.niveau_id == nid).one()
        return ref.id, cid, nid


def test_un_referentiel_neuf_arrive_avec_ses_quatre_colonnes_vides():
    """LE test du retrait. Si celui-ci tombe, c'est qu'un mécanisme repose un texte tout seul —
    et le premier référentiel d'un type nouveau repartira avec les repères d'un autre diplôme."""
    from backend.core.models_db import Referentiel
    ref_id, _, _ = _deposer()
    with dbmod.SessionLocal() as db:
        ref = db.get(Referentiel, ref_id)
        remplies = {c: getattr(ref, c) for c in COLONNES if (getattr(ref, c) or "").strip()}
    assert not remplies, f"Le dépôt a posé des méta-prompts : {sorted(remplies)}"


def test_un_second_depot_ne_pose_rien_non_plus():
    """La recopie d'hier passait à la création COMME à la mise à jour : redéposer sur le même
    couple rattrapait les colonnes vides. Ce chemin-là doit être mort aussi."""
    from backend.core.models_db import Referentiel
    ref_id, cid, nid = _deposer()

    token = uuid.uuid4().hex
    (refadm.STAGING_DIR / f"{token}.pdf").write_bytes(b"%PDF-fake")
    body = refadm.ValiderBody(token=token, cycle_id=cid, niveau_id=nid,
                              fichier_origine="ref-officiel-v2.pdf", source="dépôt manuel")
    try:
        with patch("backend.rag.extraction.extraire_texte", return_value="TEXTE ÉPURÉ V2"), \
             patch("pdfplumber.open") as ouvrir:
            ouvrir.return_value.__enter__.return_value.pages = [object()]
            reponse = refadm.valider_flux(body)

            async def _lire():
                return [json.loads(l) async for l in reponse.body_iterator if l.strip()]

            asyncio.run(_lire())
    finally:
        (refadm.STAGING_DIR / f"{token}.pdf").unlink(missing_ok=True)

    with dbmod.SessionLocal() as db:
        ref = db.get(Referentiel, ref_id)
        remplies = {c: getattr(ref, c) for c in COLONNES if (getattr(ref, c) or "").strip()}
    assert not remplies, f"Le second dépôt a posé des méta-prompts : {sorted(remplies)}"


def test_aucun_gabarit_de_meta_prompt_au_registre():
    """Les quatre entrées sont sorties avec le mécanisme qui les lisait. Les laisser ferait
    apparaître dans l'écran Prompts quatre textes que plus rien ne consomme."""
    restants = [cle for cle in GABARITS if cle in PROMPTS]
    assert not restants, f"Encore au registre : {restants}"


def test_aucun_gabarit_de_meta_prompt_en_base():
    """L'autre bout : une ligne restée en `settings` serait un texte mort que `get_prompt`
    pourrait encore servir si quelqu'un rebranchait la recopie sans y penser."""
    from backend.core.models_db import Setting
    with dbmod.SessionLocal() as db:
        cles = [s.key for s in db.query(Setting)
                .filter(Setting.key.like("prompt_gabarit_meta%")).all()]
    assert not cles, f"Encore en base : {cles}"
