# -*- coding: utf-8 -*-
"""Moteur d'écritures prédictives (Feature 3).

Transforme un journal de caisse (encaissements / décaissements) en projets
d'écritures comptables équilibrées, prêtes à être VALIDÉES par un humain.

Positionnement produit : les écritures générées sont TOUJOURS proposées en
statut "pending" (jamais appliquées d'office). Un gestionnaire les valide
explicitement avant qu'elles n'aient force d'écriture comptable (source).

Contraintes :
- Pas de scikit-learn : classification par règles (mots-clés) + score de confiance.
- Comptabilité de base : plan comptable simplifié type SYSCOHADA/RDC.
- Chaque écriture est équilibrée (total débit == total crédit).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _next_ref() -> str:
    return f"PRED-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


# Mapping de classification : mots-clés -> (sens, débit, crédit, compte_caisse)
# Compte de caisse par défaut : 530 (Caisse) ; on peut pointer 512 (Banque).
CATEGORY_RULES = {
    "vente": {
        "keywords": ["vente", "client", "encaissement", "reglement client",
                     "chiffre d'affaire", "ca", "facture client"],
        "debit": None,  # déterminé par le type d'opération
        "credit": "70",
        "label": "Ventes / produits",
        "hint": "70",
    },
    "achat": {
        "keywords": ["achat", "fournisseur", "marchandise", "stock",
                     "facture fournisseur", "approvisionnement"],
        "debit": "60",
        "credit": None,
        "label": "Achats / fournisseurs",
        "hint": "60",
    },
    "salaire": {
        "keywords": ["salaire", "paie", "masse salariale", "rémunération",
                     "chargé du personnel"],
        "debit": "64",
        "credit": None,
        "label": "Charges de personnel",
        "hint": "64",
    },
    "loyer": {
        "keywords": ["loyer", "location", "bail"],
        "debit": "61",
        "credit": None,
        "label": "Services extérieurs",
        "hint": "61",
    },
    "frais": {
        "keywords": ["frais", "divers", "transport", "eau", "electricite",
                     "telephone", "communication", "entretien", "carburant"],
        "debit": "61",
        "credit": None,
        "label": "Services extérieurs / frais",
        "hint": "61",
    },
    "impot": {
        "keywords": ["impôt", "impot", "taxe", "tva", "dgi", "dgr"],
        "debit": "44",
        "credit": None,
        "label": "État / impositions",
        "hint": "44",
    },
    "banque": {
        "keywords": ["banque", "virement", "dépôt", "depot", "retrait", "cheque"],
        "debit": None,
        "credit": None,
        "label": "Virement / banque",
        "hint": "512",
    },
}


def classify(description: str) -> tuple[str, str]:
    """Retourne (categorie, compte_de_nature). Catégorie vide si non reconnu."""
    d = (description or "").lower()
    for cat, rule in CATEGORY_RULES.items():
        for kw in rule["keywords"]:
            if kw.lower() in d:
                return cat, rule.get("credit") or rule.get("debit")
    return "", ""


def _caisse_account(direction: str, description: str) -> str:
    """Compte de trésorerie : 530 (caisse) sauf mention banque."""
    d = (description or "").lower()
    if any(k in d for k in ("banque", "virement", "cheque", "retrait", "depot", "dépôt")):
        return "512"
    return "530"


def predict_op(op: dict) -> dict | None:
    """Convertit une opération de caisse en un projet d'écriture équilibrée.

    op attendu : {date, description, amount, direction} (direction in|out).

    Pour un encaissement : Débit 530/512 à la trésorerie -- Crédit au compte de nature.
    Pour un décaissement : Débit au compte de nature -- Crédit 530/512.
    """
    description = op.get("description", "")
    amount = op.get("amount")
    direction = op.get("direction", "in")
    date = op.get("date")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    if amount <= 0:
        return None

    cat, nature_account = classify(description)
    caisse = _caisse_account(direction, description)

    if direction == "in":
        debit, credit = caisse, nature_account if nature_account else "70"
    else:
        debit, credit = nature_account if nature_account else "60", caisse

    # Confiance : plus la description est reconnue, plus haute ; sinon basse.
    if cat:
        confidence = 0.9
        label = CATEGORY_RULES[cat]["label"]
    else:
        confidence = 0.5
        label = "Opération non classée"

    balance_amount = abs(amount)

    lines = [
        {"label": f"{label}", "account": debit, "debit": round(balance_amount, 2),
         "credit": None, "amount": round(balance_amount, 2)},
        {"label": f"{label}", "account": credit, "debit": None,
         "credit": round(balance_amount, 2), "amount": round(balance_amount, 2)},
    ]

    return {
        "entry_ref": _next_ref(),
        "date": date or _utcnow().strftime("%Y-%m-%d"),
        "source": "predicted",
        "confidence": round(confidence, 2),
        "status": "pending",
        "category": cat or "non_classe",
        "description": description,
        "lines": lines,
    }


def predict_cash_book(operations: list[dict]) -> list[dict]:
    """Applique predict_op à la liste d'opérations de caisse."""
    entries = []
    for op in operations:
        en = predict_op(op)
        if en:
            entries.append(en)
    return entries
