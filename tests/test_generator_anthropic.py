r"""Preuve — lecture de la réponse Anthropic dans `_anthropic` (src/generator.py).

Bug corrigé : la réponse Anthropic est une LISTE de blocs ; avec le raisonnement (thinking),
le 1er bloc est un ThinkingBlock (pas de `.text`). L'ancien `message.content[0].text` plantait
(« 'ThinkingBlock' object has no attribute 'text' »).

Ce que ces tests PROUVENT :
  1. Une réponse [thinking, text] -> le TEXTE est lu correctement (le bloc thinking est ignoré).
  2. Une réponse SANS bloc de texte -> erreur CLAIRE levée (jamais une chaîne vide en douce).

Lancer : .\.venv\Scripts\python.exe -m pytest test_generator_anthropic.py -q
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(ROOT))   # racine projet -> `src` importable

import pytest
from unittest.mock import MagicMock, patch

import src.generator as gen


class _Bloc:
    """Bloc de contenu Anthropic simulé. Un bloc 'thinking' n'a PAS d'attribut `.text`
    (comme le vrai ThinkingBlock) — accéder à `.text` dessus lèverait, ce qui reproduit
    exactement le bug d'origine."""
    def __init__(self, type_, **attrs):
        self.type = type_
        for k, v in attrs.items():
            setattr(self, k, v)


class _Msg:
    def __init__(self, content):
        self.content = content


def _client(content):
    c = MagicMock()
    c.messages.create.return_value = _Msg(content)
    return c


def test_anthropic_thinking_puis_text_lit_le_texte():
    # [ThinkingBlock, TextBlock] : le bloc thinking (sans .text) est ignoré, le texte est lu.
    contenu = [_Bloc("thinking", thinking="je réfléchis"), _Bloc("text", text="LE TEXTE")]
    with patch.object(gen, "CLAUDE_API_KEY_TEXTE", "cle-test"), \
         patch("anthropic.Anthropic", return_value=_client(contenu)):
        out = gen._anthropic("prompt")
    assert out == "LE TEXTE"


def test_anthropic_plusieurs_blocs_text_concatenes():
    # Deux blocs de texte -> concaténés dans l'ordre (jamais seulement le premier).
    contenu = [_Bloc("text", text="AB"), _Bloc("text", text="CD")]
    with patch.object(gen, "CLAUDE_API_KEY_TEXTE", "cle-test"), \
         patch("anthropic.Anthropic", return_value=_client(contenu)):
        out = gen._anthropic("prompt")
    assert out == "ABCD"


def test_anthropic_sans_bloc_text_leve_erreur_claire():
    # Réponse composée UNIQUEMENT d'un bloc thinking : aucun texte -> erreur explicite,
    # jamais une chaîne vide rendue en silence.
    contenu = [_Bloc("thinking", thinking="je réfléchis")]
    with patch.object(gen, "CLAUDE_API_KEY_TEXTE", "cle-test"), \
         patch("anthropic.Anthropic", return_value=_client(contenu)):
        with pytest.raises(RuntimeError, match="sans bloc de texte"):
            gen._anthropic("prompt")
