# -*- coding: utf-8 -*-
"""Tests unitaires du moteur de détection d'anomalies (Feature 4).

Critères d'acceptation vérifiés ici :
  - chaque anomalie porte les champs canoniques
  - rappel : les anomalies réellement présentes sont détectées
  - le score de risque est borné [0, 100] et pondéré par la confiance
"""
import numpy as np
import pandas as pd
import pytest

from engine.rules_engine import RulesEngine

CANONICAL_KEYS = {
    "type", "severity", "confidence", "description", "reference",
    "summary", "reason", "red_flags", "suggested_action",
}


def _df(**overrides):
    base = {
        "vendor": ["A", "A", "B", "C"],
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "amount": [1000.0, 1000.0, 2500.0, 900.0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


# ----------------------------------------------------------------------
# Structure des anomalies
# ----------------------------------------------------------------------
def test_every_anomaly_has_canonical_keys():
    df = _df()
    anomalies = RulesEngine.detect_anomalies(df)
    assert isinstance(anomalies, list)
    for a in anomalies:
        assert CANONICAL_KEYS.issubset(a.keys()), f"clés manquantes: {CANONICAL_KEYS - a.keys()}"


def test_quality_anomaly_when_columns_missing():
    df = pd.DataFrame({"amount": [1, 2, 3]})  # pas de date ni vendor
    anomalies = RulesEngine.detect_anomalies(df)
    types = {a["type"] for a in anomalies}
    assert "Qualité des données" in types


def test_empty_df_returns_empty():
    assert RulesEngine.detect_anomalies(pd.DataFrame()) == []


# ----------------------------------------------------------------------
# Détection effective (rappel)
# ----------------------------------------------------------------------
def test_detects_duplicates():
    df = _df(vendor=["A", "A", "B", "B"], date=["2024-01-01"] * 4,
             amount=[1000.0] * 4)
    anomalies = RulesEngine.detect_anomalies(df)
    assert any(a["type"] == "Trans.En double" for a in anomalies)


def test_detects_negative_transaction():
    df = _df(amount=[-500.0, 1000.0, 2000.0, 3000.0])
    anomalies = RulesEngine.detect_anomalies(df)
    assert any(a["type"] == "Transaction négative" for a in anomalies)


def test_detects_statistical_outlier():
    rng = np.random.default_rng(42)
    vals = rng.normal(1000, 50, 200).tolist()
    vals.append(5000.0)  # valeur aberrante flagrante
    df = pd.DataFrame({
        "vendor": [f"V{i%10}" for i in range(len(vals))],
        "date": [f"2024-01-{(i % 28) + 1:02d}" for i in range(len(vals))],
        "amount": vals,
    })
    anomalies = RulesEngine.detect_anomalies(df)
    assert any(a["type"] == "Écart statistique" for a in anomalies)


def test_detects_monthly_spike():
    months = [f"2024-{m:02d}-15" for m in range(1, 13)]
    df = pd.DataFrame({
        "vendor": ["A"] * 15,
        "date": months + ["2024-03-20", "2024-03-21", "2024-03-22"],
        "amount": [10000.0] * 12 + [100000.0] * 3,
    })
    anomalies = RulesEngine.detect_anomalies(df)
    assert any(a["type"] == "Pic mensuel anormal" for a in anomalies)


# ----------------------------------------------------------------------
# Score de risque
# ----------------------------------------------------------------------
def test_risk_score_bounded_and_non_negative():
    df = _df(amount=[-500.0, 1000.0, 2000.0, 3000.0])
    anomalies = RulesEngine.detect_anomalies(df)
    score = RulesEngine.calculate_risk_score(anomalies, len(df))
    assert 0 <= score <= 100


def test_risk_score_zero_when_no_rows():
    assert RulesEngine.calculate_risk_score([], 0) == 0.0


def test_risk_score_reflects_severity():
    # Des anomalies "critical" doivent donner un score plus élevé que "low" seules
    low = RulesEngine.calculate_risk_score(
        [{"severity": "low", "confidence": 1.0}], 100
    )
    critical = RulesEngine.calculate_risk_score(
        [{"severity": "critical", "confidence": 1.0}], 100
    )
    assert critical > low
