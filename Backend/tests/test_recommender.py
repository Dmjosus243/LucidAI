# -*- coding: utf-8 -*-
"""Tests de l'assistant conversationnel (Feature 5).

Vérifie la réponse locale (repli dégradé) de façon déterministe :
on vide GEMINI_API_KEY pour forcer le chemin local et éviter tout appel réseau.
"""
import pytest

import config as config_module
from engine import recommender


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    # Force le repli local (aucun appel réseau), indépendamment du .env.
    monkeypatch.setattr(config_module.config, "GEMINI_API_KEY", "")
    yield


def _answer(q):
    return recommender.answer(q, ORG)


ORG = {
    "org_name": "PME Test",
    "entries": [
        {"source": "ocr", "lines": [{"label": "Facture A", "amount": 1000.0}], "date": "2024-01-01"},
        {"source": "manuel", "lines": [{"label": "Facture B", "amount": 500.0}], "date": "2024-01-02"},
        {"source": "ocr", "lines": [{"label": "Facture C", "amount": 300.0}], "date": "2024-02-01"},
    ],
    "analyses": [{"risk_score": 42.0, "status": "done"}],
    "anomalies": [{"type": "Duplicata"}, {"type": "Fraude potentielle"}, {"type": "Duplicata"}],
}


def test_answer_returns_text_and_mode():
    result = _answer("combien d'écritures ai-je ?")
    assert isinstance(result, dict)
    assert "text" in result
    assert "mode" in result
    assert result["mode"] in ("llm", "local")
    assert result["text"]


def test_local_answer_counts_entries():
    result = _answer("combien d'écritures ai-je ?")
    assert "3" in result["text"]


def test_local_answer_risk():
    result = _answer("quel est mon niveau de risque ?")
    assert "42" in result["text"]


def test_local_answer_anomalies():
    result = _answer("quelles anomalies ?")
    assert "Duplicata" in result["text"]


def test_local_answer_greeting():
    result = _answer("bonjour")
    assert "Bonjour" in result["text"]


def test_build_context_contains_summary():
    ctx = recommender.build_context(ORG)
    assert "PME Test" in ctx
    assert "3 écritures" in ctx
    assert "42" in ctx


def test_source_counts():
    counts = recommender._source_counts(ORG["entries"])
    assert counts == {"ocr": 2, "manuel": 1}


def test_answer_never_crashes_on_empty():
    result = _answer("salut")
    assert result["text"]
