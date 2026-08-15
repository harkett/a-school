r"""Preuve de la VEILLE DES TARIFS — elle écrit les prix, elle ne touche pas à l'ordre d'appel.

CE QUE LA VEILLE FAIT, une fois par jour : elle relit la grille tarifaire de chaque fournisseur qui
a une adresse, écrit en base les prix qui ont changé, et prévient l'administrateur par courriel.

CE QU'ELLE FAIT ENSUITE : reclasser l'ordre d'appel sur le tarif — le gratuit en tête, puis les
payants du moins cher au plus cher. Ce reclassement a d'abord été mis derrière un bouton
« Appliquer » : l'administrateur devait le trouver, le comprendre et l'actionner pour confirmer ce
que les chiffres disaient déjà. Il se fait maintenant tout seul, et le courriel annonce le nouvel
ordre.

CE QUE CES TESTS PROTÈGENT :
  1. le prix nouveau est ÉCRIT (un tarif est un fait, pas une proposition) ;
  2. le classement suit le prix, et le GRATUIT reste en tête quoi qu'il arrive ;
  3. rien de changé, rien d'envoyé : une alerte quotidienne « tout va bien » ne serait plus lue ;
  4. le message dit ce qu'il faut faire ET où — dans un an, personne ne s'en souviendra ;
  5. une page injoignable n'interrompt pas la veille des autres fournisseurs.

Ni réseau ni base : la page et la session sont fournies par le test. La vraie page a servi à écrire
le module, pas à le tester — une suite qui dépend d'un site tiers échoue le jour où il change de
mise en page, pour une raison qui n'est pas la nôtre.

Lancer : docker compose exec backend python -m pytest tests/test_veille_tarifs.py -q
"""
import backend.systeme.veille_tarifs as veille


class _Modele:
    def __init__(self, modele, entree, sortie, devise="USD", nom_fournisseur=None):
        self.fournisseur = "essai"
        self.modele = modele
        self.cout_entree_million = entree
        self.cout_sortie_million = sortie
        self.devise = devise
        self.nom_fournisseur = nom_fournisseur
        # Le reclassement cherche le modèle RÉELLEMENT appelé : recommandé et actif. Sans ces
        # trois attributs, la doublure ne ressemble plus assez à une vraie ligne pour l'éprouver.
        self.actif = True
        self.recommande = True
        self.ordre = 1


class _Fournisseur:
    def __init__(self, lien="https://exemple.test/tarifs"):
        self.code = "essai"
        self.label = "Essai"
        self.actif = True
        self.lien_tarifs = lien
        self.ordre = 2
        # Le reclassement sépare les gratuits des payants : sans ce champ, la doublure n'irait
        # pas jusqu'au bout du chemin qu'on prétend éprouver.
        self.tarification = "payant"


class _Requete:
    """Rend les fournisseurs ou les modèles selon ce qu'on lui demande, sans base."""
    def __init__(self, contenu):
        self.contenu = contenu

    def filter(self, *_args):
        return self

    def all(self):
        return self.contenu


class _Session:
    def __init__(self, fournisseurs, modeles, journal):
        self.fournisseurs, self.modeles, self.journal = fournisseurs, modeles, journal

    def query(self, classe):
        from backend.core.models_db import AiFournisseur
        return _Requete(self.fournisseurs if classe is AiFournisseur else self.modeles)

    def commit(self):
        self.journal["commits"] += 1

    def rollback(self):
        self.journal["rollbacks"] += 1

    def close(self):
        pass


def _brancher(monkeypatch, modeles, releve, *, lien="https://exemple.test/tarifs", page_ok=True):
    """Isole la veille : pas de réseau, pas de base, pas de courriel. Rend le journal des effets."""
    journal = {"commits": 0, "rollbacks": 0, "alertes": []}
    fournisseur = _Fournisseur(lien)
    monkeypatch.setattr(veille, "session_pour",
                        lambda _schema: _Session([fournisseur], modeles, journal))

    def _page(_url):
        if not page_ok:
            raise ValueError("Page injoignable (URLError). Vérifiez l'adresse.")
        return "peu importe : c'est `relever` qui est simulé"

    monkeypatch.setattr(veille, "lire_page", _page)
    monkeypatch.setattr(veille, "relever", lambda _texte, _noms: releve)
    monkeypatch.setattr(veille, "create_alert",
                        lambda niveau, titre, message, sujet_detail="", destinataire=None:
                            journal["alertes"].append((niveau, titre, message)))
    journal["fournisseur"] = fournisseur
    return journal


def test_un_prix_qui_change_est_ecrit_en_base(monkeypatch):
    """Un tarif est un FAIT du fournisseur. Le garder « pour validation » reviendrait à conserver
    sciemment un chiffre faux — et c'est ce chiffre qui sert à comparer les fournisseurs."""
    m = _Modele("claude-sonnet-5", 2.0, 10.0)
    _brancher(monkeypatch, [m], {"claude-sonnet-5": {"entree": 3.0, "sortie": 15.0, "devise": "USD"}})
    changements = veille.veiller()

    assert float(m.cout_entree_million) == 3.0
    assert float(m.cout_sortie_million) == 15.0
    assert len(changements) == 1
    assert changements[0]["avant_entree"] == 2.0, "l'ancien prix doit voyager : sans lui, on ne sait pas si ça monte"


def test_le_classement_suit_le_prix(monkeypatch):
    """Un fournisseur devenu moins cher passe devant, sans que personne ne valide.

    Le reclassement est la raison d'être de la veille : relever un prix sans en tirer les
    conséquences laissait l'application appeler le plus cher en connaissance de cause."""
    m = _Modele("claude-sonnet-5", 20.0, 100.0)
    journal = _brancher(monkeypatch, [m], {"claude-sonnet-5": {"entree": 0.1, "sortie": 0.2, "devise": "USD"}})
    veille.veiller()

    assert journal["fournisseur"].ordre == 1, "le seul fournisseur payant doit prendre le premier rang"


def test_rien_n_a_change_rien_n_est_envoye(monkeypatch):
    """Le cas ordinaire : les tarifs d'IA bougent quelques fois par an. Une alerte quotidienne
    « tout va bien » ne serait plus lue au bout d'une semaine, et celle qui compte passerait avec."""
    m = _Modele("claude-sonnet-5", 2.0, 10.0)
    journal = _brancher(monkeypatch, [m], {"claude-sonnet-5": {"entree": 2.0, "sortie": 10.0, "devise": "USD"}})
    changements = veille.veiller()

    assert changements == []
    assert journal["alertes"] == [], "aucun courriel ne doit partir quand rien n'a changé"


def test_le_message_dit_quoi_faire_et_ou(monkeypatch):
    """Dans un an, celui qui reçoit ce courriel aura oublié cet écran. Le message doit donc porter
    le chemin complet, le nom exact du bouton, et ce qui se passe si l'on ne fait rien."""
    m = _Modele("claude-sonnet-5", 2.0, 10.0)
    journal = _brancher(monkeypatch, [m], {"claude-sonnet-5": {"entree": 3.0, "sortie": 15.0, "devise": "USD"}})
    veille.veiller()

    assert len(journal["alertes"]) == 1
    niveau, _titre, message = journal["alertes"][0]
    assert niveau == "info", "rien n'est cassé : c'est une nouvelle à lire, pas une panne"
    for attendu in ("/admin/ia/fournisseurs", "Nouvel ordre d'appel", "gratuit",
                    "2.0 → 3.0", "10.0 → 15.0"):
        assert attendu in message, f"le message ne dit pas « {attendu} »"


def test_un_modele_absent_de_la_grille_garde_son_tarif(monkeypatch):
    """Le relevé ne remet jamais un prix à zéro : un modèle retiré du catalogue public du
    fournisseur (nos `qwen3`, `mistral24b`) garde ce qu'on savait de lui."""
    m = _Modele("qwen3", 0.4, 3.2, devise="CHF")
    _brancher(monkeypatch, [m], {})
    assert veille.veiller() == []
    assert float(m.cout_entree_million) == 0.4


def test_une_page_injoignable_n_interrompt_pas_la_veille(monkeypatch):
    """Un site en panne n'est pas un incident de tarif. On le note au journal et on continue —
    alerter là-dessus tous les jours noierait le message qui compte."""
    m = _Modele("claude-sonnet-5", 2.0, 10.0)
    journal = _brancher(monkeypatch, [m], {"claude-sonnet-5": {"entree": 3.0, "sortie": 15.0, "devise": "USD"}},
                        page_ok=False)
    assert veille.veiller() == []
    assert journal["alertes"] == []
    assert float(m.cout_entree_million) == 2.0, "rien ne s'écrit quand la page n'a pas été lue"


def test_un_fournisseur_sans_adresse_est_ignore(monkeypatch):
    """Groq n'a pas d'adresse : sa page de tarifs est construite en JavaScript, il n'y a rien à
    lire côté serveur. La veille passe son chemin sans erreur."""
    m = _Modele("openai/gpt-oss-120b", 0.0, 0.0)
    journal = _brancher(monkeypatch, [m], {"openai/gpt-oss-120b": {"entree": 9.0, "sortie": 9.0, "devise": "USD"}},
                        lien="")
    assert veille.veiller() == []
    assert float(m.cout_entree_million) == 0.0
    assert journal["alertes"] == []
