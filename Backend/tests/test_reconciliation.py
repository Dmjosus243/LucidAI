# -*- coding: utf-8 -*-
"""Tests du rapprochement bancaire automatisé (Feature 2).

Critère d'acceptation clé : taux d'automatisation ≥ 80 % sur des données réelles,
faux positifs faibles, pas de double rapprochement.
"""
import pytest

from engine.reconciliation import reconcile, automation_rate


def test_strict_match_same_amount_and_date():
    journal = [{"date": "2024-05-10", "label": "Facture EDF", "amount": 150000.0}]
    stmt = [{"date": "2024-05-10", "description": "VIR EDF", "amount": 150000.0}]
    result = reconcile(journal, stmt)
    matched = [r for r in result if r["entry_index"] is not None and r["status"] != "unmatched"]
    assert len(matched) == 1
    assert matched[0]["status"] in ("auto", "matched")
    assert matched[0]["confidence"] >= 0.7


def test_strict_match_within_date_window():
    # ±3 jours autorisés
    journal = [{"date": "2024-05-10", "label": "A", "amount": 1000.0}]
    stmt = [{"date": "2024-05-12", "description": "B", "amount": 1000.0}]
    result = reconcile(journal, stmt)
    matched = [r for r in result if r["status"] != "unmatched" and r["entry_index"] is not None]
    assert len(matched) == 1


def test_fuzzy_match_by_label():
    # montant différent (5%) mais même libellé → match flou
    journal = [{"date": "2024-05-10", "label": "SOCIETE ELECTRICITE KINSHASA", "amount": 100000.0}]
    stmt = [{"date": "2024-05-11", "description": "Societe Electricite Kinshasa", "amount": 105000.0}]
    result = reconcile(journal, stmt)
    matched = [r for r in result if r["status"] != "unmatched" and r["entry_index"] is not None]
    assert len(matched) == 1
    assert matched[0]["status"] == "matched"


def test_no_match_for_different_amount():
    journal = [{"date": "2024-05-10", "label": "A", "amount": 1000.0}]
    stmt = [{"date": "2024-05-10", "description": "B", "amount": 9999.0}]
    result = reconcile(journal, stmt)
    entry = [r for r in result if r["entry_index"] == 0][0]
    assert entry["status"] == "unmatched"


def test_no_double_matching():
    # 2 écritures, 1 seule ligne de relevé → une seule correspondance
    journal = [
        {"date": "2024-05-10", "label": "A", "amount": 1000.0},
        {"date": "2024-05-10", "label": "Z", "amount": 1000.0},
    ]
    stmt = [{"date": "2024-05-10", "description": "B", "amount": 1000.0}]
    result = reconcile(journal, stmt)
    matched_all = [r for r in result if r["status"] != "unmatched"]
    assert len(matched_all) == 1


def test_automation_rate_high_on_clean_data():
    journal = [
        {"date": "2024-01-05", "label": "Facture 1", "amount": 50000.0},
        {"date": "2024-01-06", "label": "Facture 2", "amount": 80000.0},
        {"date": "2024-01-07", "label": "Facture 3", "amount": 12000.0},
        {"date": "2024-01-08", "label": "Facture 4", "amount": 30000.0},
        {"date": "2024-01-09", "label": "Facture 5", "amount": 90000.0},
    ]
    stmt = [
        {"date": "2024-01-05", "description": "Facture 1 - SEPA", "amount": 50000.0},
        {"date": "2024-01-05", "description": "Facture deux", "amount": 80000.0},
        {"date": "2024-01-08", "description": "FACTURE TROIS", "amount": 11900.0},
        {"date": "2024-01-08", "description": "Facture 4 reglement", "amount": 30000.0},
        {"date": "2024-01-09", "description": "Facture 5", "amount": 90050.0},
    ]
    result = reconcile(journal, stmt)
    rate = automation_rate(result)
    # critère d'acceptation : ≥ 80 %
    assert rate >= 0.8


def test_empty_journal_returns_all_unmatched():
    result = reconcile([], [{"date": "2024-01-01", "description": "X", "amount": 10.0}])
    assert result[0]["status"] == "unmatched"
