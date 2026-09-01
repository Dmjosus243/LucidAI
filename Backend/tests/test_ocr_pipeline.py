# -*- coding: utf-8 -*-
"""Tests unitaires du pipeline OCR + parsing (Feature 1).

Vérifie le parsing des montants/dates, l'extraction structurée,
l'extraction depuis texte, et la génération d'écritures.
"""
import pytest

from engine.ocr_pipeline import (
    detect_engine,
    extract_document,
    build_entries,
    _parse_amount,
    _parse_date,
)


# ----------------------------------------------------------------------
# Parsing des montants (formats francophones / internationaux)
# ----------------------------------------------------------------------
@pytest.mark.parametrize("chaine,attendu", [
    ("1 234,56", 1234.56),
    ("150 000,00", 150000.00),
    ("150,000.00", 150000.00),
    ("150000", 150000.0),
    ("12 500 CDF", 12500.0),
    ("34 500 CDF", 34500.0),
    ("-500", -500.0),
    ("2 000", 2000.0),
])
def test_parse_amount_variants(chaine, attendu):
    assert _parse_amount(chaine) == pytest.approx(attendu)


def test_parse_amount_returns_none_when_no_number():
    assert _parse_amount("Rien ici") is None
    assert _parse_amount("") is None


# ----------------------------------------------------------------------
# Parsing de dates
# ----------------------------------------------------------------------
def test_parse_date_iso():
    assert _parse_date("2024-05-12") == "2024-05-12"


def test_parse_date_slash():
    assert _parse_date("12/05/2024") == "12/05/2024"


def test_parse_date_none():
    assert _parse_date("aucune date") is None


# ----------------------------------------------------------------------
# Extractions structurées (CSV / XLSX / JSON de factures)
# ----------------------------------------------------------------------
def test_structured_extraction_knows_fields():
    rows = [
        {"fournisseur": "Soc. Electrique", "date": "2024-05-12",
         "montant": "150 000,00 CDF", "tva": 16},
        {"fournisseur": "Btp Congo", "date": "2024-05-14",
         "montant": "12 500 CDF", "tva": 0},
    ]
    result = extract_document("factures.xlsx", b"", structured_rows=rows)
    assert len(result["lines"]) == 2
    first = result["lines"][0]
    assert first["amount"] == pytest.approx(150000.0)
    assert first["tax_rate"] == pytest.approx(16.0)
    assert first["date"] == "2024-05-12"
    # La confiance doit être élevée sur les entrées structurées
    assert result["confidence"] >= 0.9


def test_structured_amount_uses_raw_number():
    rows = [{"montant": 150000.0, "date": "2024-01-01"}]
    result = extract_document("f.json", b"", structured_rows=rows)
    assert result["lines"][0]["amount"] == pytest.approx(150000.0)


# ----------------------------------------------------------------------
# Extraction depuis texte
# ----------------------------------------------------------------------
def test_text_extraction_extracts_amounts():
    txt = "2024-06-01 Societe EDF 34 500 CDF TVA 16%\n2024-06-02 2 000 CDF transport"
    result = extract_document("scan.txt", txt.encode("utf-8"))
    amounts = [l["amount"] for l in result["lines"]]
    assert 34500.0 in amounts
    assert 2000.0 in amounts


def test_detect_engine_returns_known_value():
    assert detect_engine() in ("paddle", "tesseract", "transparent")


# ----------------------------------------------------------------------
# Génération d'écritures
# ----------------------------------------------------------------------
def test_build_entries_generates_references():
    lines = [
        {"label": "A", "date": "2024-01-01", "amount": 100.0, "tax_rate": 16, "confidence": 0.95},
    ]
    entries = build_entries(lines, source="ocr")
    assert len(entries) == 1
    assert entries[0]["entry_ref"].startswith("OCR-")
    assert entries[0]["source"] == "ocr"
    assert entries[0]["amount"] == 100.0
