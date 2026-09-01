# -*- coding: utf-8 -*-
"""Rapprochement bancaire automatisé (Feature 2).

Algorithme en deux passes :
  1. Correspondance stricte : montant égal (≤ 0,01 %) ET date à ±3 jours.
  2. Correspondance floue : montant proche (≤ 10 %) + similarité de libellé.

Chaque correspondance produit un score de confiance [0,1] fonction de
l'écart de montant, l'écart de date, la similarité de libellé et l'unicité.

Principe glouton : on traite les paires par confiance décroissante, et chaque
ligne (écriture ou relevé) ne peut être rapprochée qu'une seule fois.
"""
import logging
from difflib import SequenceMatcher
from datetime import datetime, timedelta

import numpy as np

logger = logging.getLogger(__name__)

AMOUNT_EPSILON = 0.0001          # 0,01 % de tolérance pour le strict
DATE_WINDOW_DAYS = 3
FUZZY_AMOUNT_RATIO = 0.10        # 10 % de tolérance pour la passe floue
FUZZY_LABEL_MIN = 0.60           # similarité minimale de libellé (passe floue)


def _norm_label(text) -> str:
    """Normalise un libellé pour la comparaison floue."""
    import re
    s = str(text or "").lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s.strip()


def _parse_date(value):
    """Convertit une date (str ou datetime) en date, None si invalide."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _conf(amount_diff: float, date_diff_days: int, label_ratio: float = 1.0,
          unique: bool = True) -> float:
    """Calcule la confiance d'une correspondance.

    - Écart de montant : 1.0 si 0, dégradé linéairement.
    - Écart de date : 1.0 si 0, -0.15/jour (plancher 0.3).
    - Similarité de libellé (passe floue uniquement).
    - Unicité : pénalise si le pointage n'est pas unique.
    """
    score = 1.0
    # Montant
    if amount_diff > AMOUNT_EPSILON:
        score -= min(0.5, amount_diff * 8)
    # Date
    if date_diff_days is not None:
        penalty = min(0.5, max(0, date_diff_days - 1) * 0.15)
        score -= penalty
    # Libellé (passe floue)
    score *= label_ratio if label_ratio < 1.0 else 1.0
    # Unicité
    if not unique:
        score -= 0.25
    return round(min(1.0, max(0.1, score)), 2)


def reconcile(journal_lines: list, statement_lines: list):
    """Rapproche les écritures avec les lignes de relevé.

    Param.
      journal_lines   : list de dict {date, label, amount} (écritures)
      statement_lines : list de dict {date, description, amount} (relevé)

    Retour.
      liste de dict : {entry_index, statement_index, status, confidence,
                       matched_by}
      - status 'auto' ou 'matched' selon la passe.
      - attrs_amount_diff, date_diff pour l'affichage.
    """
    journal = []
    for i, j in enumerate(journal_lines):
        journal.append({
            "idx": i,
            "amount": float(j.get("amount") or 0.0),
            "date": _parse_date(j.get("date")),
            "label": _norm_label(j.get("label")),
        })

    statements = []
    for i, s in enumerate(statement_lines):
        statements.append({
            "idx": i,
            "amount": float(s.get("amount") or 0.0),
            "date": _parse_date(s.get("date")),
            "label": _norm_label(s.get("description") or s.get("label")),
        })

    if not journal or not statements:
        return _empty_result(journal_lines, statement_lines)

    pairs = []
    used_journal = set()
    used_stmt = set()

    # --- Passe 1 : stricte (montant + fenêtre de date) ---
    for j in journal:
        if j["idx"] in used_journal:
            continue
        best = None
        best_conf = 0.0
        for s in statements:
            if s["idx"] in used_stmt:
                continue
            if j["amount"] == 0 and s["amount"] == 0:
                continue
            amount_diff = abs(j["amount"] - s["amount"]) / max(1.0, abs(j["amount"]))
            if amount_diff > AMOUNT_EPSILON:
                continue
            date_diff = None
            if j["date"] and s["date"]:
                date_diff = abs((j["date"] - s["date"]).days)
                if date_diff > DATE_WINDOW_DAYS:
                    continue
            unique = _count_candidates(j, statements, used_stmt) == 1
            conf = _conf(amount_diff, date_diff if date_diff is not None else 0, unique=unique)
            if conf > best_conf:
                best_conf = conf
                best = s
        if best is not None:
            pairs.append((j, best, "auto", best_conf))
            used_journal.add(j["idx"])
            used_stmt.add(best["idx"])

    # --- Passe 2 : floue (montant proche + similarité de libellé) ---
    candidates = []
    for j in journal:
        if j["idx"] in used_journal:
            continue
        for s in statements:
            if s["idx"] in used_stmt:
                continue
            if j["amount"] == 0 or abs(j["amount"]) < 1:
                continue
            amount_diff = abs(j["amount"] - s["amount"]) / max(1.0, abs(j["amount"]))
            if amount_diff > FUZZY_AMOUNT_RATIO:
                continue
            ratio = SequenceMatcher(None, j["label"], s["label"]).ratio()
            if ratio < FUZZY_LABEL_MIN:
                continue
            date_diff = None
            if j["date"] and s["date"]:
                date_diff = abs((j["date"] - s["date"]).days)
            conf = _conf(amount_diff, date_diff if date_diff is not None else 0,
                         label_ratio=ratio)
            candidates.append((conf, j, s))

    candidates.sort(key=lambda c: c[0], reverse=True)
    for conf, j, s in candidates:
        if j["idx"] in used_journal or s["idx"] in used_stmt:
            continue
        pairs.append((j, s, "matched", conf))
        used_journal.add(j["idx"])
        used_stmt.add(s["idx"])

    # Construction du résultat : chaque ligne a un statut
    result = []
    for j in journal:
        found = next((p for p in pairs if p[0]["idx"] == j["idx"]), None)
        if found:
            result.append({
                "entry_index": j["idx"],
                "statement_index": found[1]["idx"],
                "status": found[2],
                "confidence": found[3],
            })
        else:
            result.append({
                "entry_index": j["idx"],
                "statement_index": None,
                "status": "unmatched",
                "confidence": 0.0,
            })
    # Lignes de relevé non rapprochées
    matched_stmt = {p[1]["idx"] for p in pairs}
    for s in statements:
        if s["idx"] not in matched_stmt:
            result.append({
                "entry_index": None,
                "statement_index": s["idx"],
                "status": "unmatched",
                "confidence": 0.0,
            })
    return _sort_result(result)


def _count_candidates(j, statements, used_stmt) -> int:
    count = 0
    for s in statements:
        if s["idx"] in used_stmt:
            continue
        if abs(j["amount"] - s["amount"]) / max(1.0, abs(j["amount"])) <= AMOUNT_EPSILON:
            count += 1
    return count


def _empty_result(journal_lines, statement_lines):
    result = [
        {"entry_index": i, "statement_index": None, "status": "unmatched", "confidence": 0.0}
        for i in range(len(journal_lines))
    ]
    result += [
        {"entry_index": None, "statement_index": i, "status": "unmatched", "confidence": 0.0}
        for i in range(len(statement_lines))
    ]
    return result


def _sort_result(result):
    # Constante d'ordre : matchés en premier (par confiance), puis non rapprochés
    def order(r):
        if r["status"] != "unmatched":
            return (0, -r["confidence"])
        return (1, 0)
    return sorted(result, key=order)


def automation_rate(result: list) -> float:
    """Taux d'écritures rapprochées automatiquement (critère ≥ 80 %)."""
    if not result:
        return 0.0
    matched = sum(1 for r in result if r["status"] in ("auto", "matched") and r["entry_index"] is not None)
    total_entries = sum(1 for r in result if r["entry_index"] is not None)
    if total_entries == 0:
        return 0.0
    return round(matched / total_entries, 4)
