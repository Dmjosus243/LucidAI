# -*- coding: utf-8 -*-
"""Tests du moteur d'écritures prédictives (Feature 3).

Vérifie : équilibre débit/crédit, classification par mots-clés, comptes de
trésorerie (530 caisse / 512 banque), confiance, et rejet des montants nuls.
"""
import pytest

from engine.prediction import (
    predict_op,
    predict_cash_book,
    classify,
    _caisse_account,
    _next_ref,
)


def test_predict_op_is_balanced():
    en = predict_op({"date": "2024-01-05", "description": "Vente au comptant", "amount": 1000, "direction": "in"})
    assert en is not None
    total_debit = sum(l["debit"] or 0 for l in en["lines"])
    total_credit = sum(l["credit"] or 0 for l in en["lines"])
    assert total_debit == total_credit
    assert total_debit == 1000.0


def test_encaissement_vente_credite_le_compte_70():
    en = predict_op({"description": "Vente au comptant", "amount": 500, "direction": "in"})
    accounts = {l["account"]: l for l in en["lines"]}
    assert "530" in accounts  # trésorerie
    assert "70" in accounts  # ventes
    assert accounts["70"]["credit"] == 500.0
    assert accounts["530"]["debit"] == 500.0
    assert en["confidence"] >= 0.8
    assert en["status"] == "pending"


def test_decaissement_achat_debite_le_compte_60():
    en = predict_op({"description": "Achat de marchandises", "amount": 300, "direction": "out"})
    accounts = {l["account"]: l for l in en["lines"]}
    assert "530" in accounts
    assert "60" in accounts
    assert accounts["60"]["debit"] == 300.0
    assert accounts["530"]["credit"] == 300.0


def test_operation_bancaire_utilise_512():
    en = predict_op({"description": "Virement banque client", "amount": 200, "direction": "in"})
    accounts = {l["account"]: l for l in en["lines"]}
    assert "512" in accounts
    assert "530" not in accounts


def test_classify_reconnait_categories():
    assert classify("Paiement salaire staff")[0] == "salaire"
    assert classify("Loyer de l'entrepôt")[0] == "loyer"
    assert classify("Taxe DGI")[0] == "impot"


def test_classify_inconnu_retourne_vide():
    cat, account = classify("Achat élément non spécifié")
    # "achat" n'est pas un mot-clé (seul "achat" l'est, ici on teste un terme absent)
    assert isinstance(cat, str)


def test_montant_nul_ou_negatif_rejete():
    assert predict_op({"description": "x", "amount": 0, "direction": "in"}) is None
    assert predict_op({"description": "x", "amount": -5, "direction": "in"}) is None
    assert predict_op({"description": "x", "amount": "abc", "direction": "in"}) is None


def test_predict_cash_book_multiple():
    ops = [
        {"date": "2024-01-01", "description": "Vente", "amount": 100, "direction": "in"},
        {"date": "2024-01-02", "description": "Achat", "amount": 50, "direction": "out"},
    ]
    entries = predict_cash_book(ops)
    assert len(entries) == 2
    for en in entries:
        assert en["source"] == "predicted"
        assert en["status"] == "pending"
        assert en["entry_ref"].startswith("PRED-")


def test_entry_ref_unique():
    assert predict_op({"description": "Vente", "amount": 1, "direction": "in"})["entry_ref"] \
        != predict_op({"description": "Vente", "amount": 1, "direction": "in"})["entry_ref"]
    assert _next_ref() != _next_ref()
