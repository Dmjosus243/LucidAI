# -*- coding: utf-8 -*-
"""Pipeline OCR intelligent basé sur Gemini Vision.

Conception :
  - Détection et extraction via Gemini 1.5 Flash (Images PNG/JPG/WEBP et PDF).
  - Traitement direct des entrées structurées (CSV, XLSX, JSON).
  - Extraction structurée au format JSON natif.
  - Tolérance aux pannes : renvoie toujours une structure valide en cas d'erreur.
"""
import os
import re
import json
import logging
import datetime
import numpy as np
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Initialisation du SDK Google Generative AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def detect_engine() -> str:
    """Retourne le moteur actif ('gemini-vision' ou 'transparent')."""
    if GEMINI_API_KEY:
        return "gemini-vision"
    return "transparent"


def _parse_amount(text):
    """Extrait un montant numérique d'une valeur ou chaîne."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    t = re.sub(r"\s", "", str(text))
    m = re.search(r"[-+]?\d[\d.,]*", t)
    if not m:
        return None
    raw = m.group(0).replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _extract_structured(rows: list) -> tuple:
    """Parsing d'entrées structurées (listes de dictionnaires issue de CSV/XLSX)."""
    lines = []
    confidences = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        lower = {str(k).strip().lower(): v for k, v in raw.items()}
        
        # Résolution du montant
        amount = None
        for k, v in lower.items():
            if any(s in k for s in ("montant", "amount", "total", "prix", "value")):
                amount = _parse_amount(v)
                if amount is not None:
                    break

        # Résolution de la date
        date = None
        for k, v in lower.items():
            if any(s in k for s in ("date", "échéance", "echeance")):
                date = str(v) if v else None
                break

        # Résolution du libellé / tiers
        label = None
        for k, v in lower.items():
            if any(s in k for s in ("fournisseur", "vendor", "libellé", "libelle", "designation", "tiers")):
                label = str(v)
                break
        if not label:
            label = str(raw.get("label") or raw.get("description") or "")

        # Résolution de la TVA
        tax = None
        for k, v in lower.items():
            if "tax" in k or "tva" in k:
                tax = _parse_amount(v)
                break

        conf = 0.95 if amount is not None else 0.0
        confidences.append(conf)

        lines.append({
            "label": label or "",
            "date": date,
            "amount": amount,
            "tax_rate": tax,
            "confidence": conf,
            "raw": raw,
        })
    
    overall = float(np.mean(confidences)) if confidences else 0.0
    return lines, round(overall, 2)


def _extract_with_gemini(content: bytes, mime_type: str) -> dict:
    """Analyse un document ou une image via Gemini 1.5 Flash."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY non configurée. Passage en mode transparent.")
        return {"engine": "transparent", "lines": [], "confidence": 0.1, "raw_text": ""}

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        
        prompt = """
        Tu es un expert comptable spécialisé dans l'analyse de pièces justificatives (factures, reçus, tickets).
        Analyse ce document et extrait toutes les lignes d'écritures sous forme d'un objet JSON strict.

        Format JSON attendu :
        {
          "lines": [
            {
              "label": "Nom du fournisseur, tiers ou description du bien/service",
              "date": "YYYY-MM-DD",
              "amount": 150.00,
              "tax_rate": 16.0,
              "confidence": 0.95
            }
          ],
          "overall_confidence": 0.95,
          "raw_text": "Texte intégral extrait du document"
        }

        Règles :
        1. 'amount' doit être un nombre (float ou int), jamais une chaîne de caractères.
        2. 'tax_rate' doit représenter le taux de TVA en pourcentage (ex: 16.0) ou null si non mentionné.
        3. 'date' doit respecter le format ISO YYYY-MM-DD si possible, sinon conserve la date brute ou null.
        4. Réponds UNIQUEMENT avec le bloc JSON valide, sans texte d'introduction ni explications.
        """

        image_part = {"mime_type": mime_type, "data": content}
        response = model.generate_content([prompt, image_part])
        
        response_text = response.text.strip()
        
        # Nettoyage des balises Markdown de code si présente
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        data = json.loads(response_text.strip())
        
        lines = data.get("lines", [])
        overall_confidence = float(data.get("overall_confidence", 0.9))
        raw_text = data.get("raw_text", "")

        return {
            "engine": "gemini-vision",
            "lines": lines,
            "confidence": round(overall_confidence, 2),
            "raw_text": raw_text,
        }

    except Exception as e:
        logger.error("Erreur lors de l'extraction Gemini Vision : %s", str(e))
        return {"engine": "gemini-error", "lines": [], "confidence": 0.0, "raw_text": ""}


def extract_document(filename: str, content: bytes, structured_rows=None) -> dict:
    """Point d'entrée principal de l'extraction OCR / Document.

    - structured_rows: Données pré-traduites depuis CSV/XLSX/JSON.
    - filename/content: Fichier brut (PNG, JPG, WEBP, PDF).
    """
    name = (filename or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""

    # Cas 1 : Données structurées (Excel / CSV)
    if structured_rows:
        lines, confidence = _extract_structured(structured_rows)
        return {
            "engine": "structured",
            "lines": lines,
            "confidence": confidence,
            "raw_text": "",
        }

    # Cas 2 : Images et PDF via Gemini Vision
    mime_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "pdf": "application/pdf"
    }

    if ext in mime_types:
        return _extract_with_gemini(content, mime_types[ext])

    # Cas 3 : Fichiers texte brut / CSV non parsés
    if ext in ("csv", "txt"):
        text = content.decode("utf-8", errors="ignore")[:200000]
        return {
            "engine": "text-plain",
            "lines": [],
            "confidence": 0.3,
            "raw_text": text,
        }

    return {"engine": "transparent", "lines": [], "confidence": 0.1, "raw_text": ""}


def build_entries(lines: list, source: str = "ocr") -> list:
    """Construit des écritures comptables prêtes à valider à partir des lignes extrates."""
    ref = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    entries = []
    for i, line in enumerate(lines):
        entries.append({
            "entry_ref": f"{source.upper()}-{ref}-{i + 1}",
            "date": line.get("date"),
            "label": line.get("label", ""),
            "amount": line.get("amount"),
            "tax_rate": line.get("tax_rate"),
            "confidence": line.get("confidence", 0.0),
            "source": source,
        })
    return entries