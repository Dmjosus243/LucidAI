"""
Moteur comptable LucidAI
Lit les écritures de journal_entries (lignes en JSON) et génère :
- Grand livre (par compte)
- Balance générale
- Journal chronologique
- Compte de résultat (simplifié)
- Bilan (simplifié)
"""

import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import JournalEntry, ChartOfAccount


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def parse_date(date_str) -> Optional[datetime]:
    """Parse une date stockée en varchar (plusieurs formats possibles)."""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str
    
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except (ValueError, TypeError):
            continue
    return None


def extract_lines(entry: JournalEntry) -> list:
    """Extrait les lignes d'une écriture (stockées en JSON)."""
    lines = entry.lines
    if isinstance(lines, str):
        try:
            lines = json.loads(lines)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(lines, list):
        return []
    
    # Normaliser chaque ligne
    normalized = []
    for line in lines:
        if not isinstance(line, dict):
            continue
        normalized.append({
            "account_number": str(line.get("account_number", line.get("compte", ""))).strip(),
            "account_name": line.get("account_name", line.get("libelle_compte", "")),
            "debit": float(line.get("debit", 0) or 0),
            "credit": float(line.get("credit", 0) or 0),
            "label": line.get("label", line.get("libelle", "")),
        })
    return normalized


# ============================================================
# 1. GRAND LIVRE (Ledger)
# ============================================================

def get_ledger(
    db: Session,
    organization_id: str,
    account_number: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    only_validated: bool = False
) -> dict:
    """
    Retourne le grand livre : toutes les écritures classées par compte.
    """
    query = db.query(JournalEntry).filter(
        JournalEntry.organization_id == organization_id
    )
    
    if only_validated:
        query = query.filter(JournalEntry.status == "validated")
    
    entries = query.all()
    
    # Filtrer par date si nécessaire
    if date_from or date_to:
        filtered = []
        for e in entries:
            d = parse_date(e.date)
            if not d:
                continue
            if date_from and d < parse_date(date_from):
                continue
            if date_to and d > parse_date(date_to):
                continue
            filtered.append(e)
        entries = filtered
    
    # Regrouper par compte
    accounts = {}
    for entry in entries:
        d = parse_date(entry.date)
        for line in extract_lines(entry):
            acc = line["account_number"]
            if not acc:
                continue
            if account_number and acc != account_number:
                continue
            
            if acc not in accounts:
                accounts[acc] = {
                    "account_number": acc,
                    "account_name": line["account_name"],
                    "entries": [],
                    "total_debit": 0.0,
                    "total_credit": 0.0,
                    "balance": 0.0,
                }
            
            accounts[acc]["entries"].append({
                "date": d.strftime("%Y-%m-%d") if d else entry.date,
                "entry_ref": entry.entry_ref,
                "label": line["label"],
                "debit": line["debit"],
                "credit": line["credit"],
            })
            accounts[acc]["total_debit"] += line["debit"]
            accounts[acc]["total_credit"] += line["credit"]
    
    # Calculer le solde de chaque compte
    for acc in accounts.values():
        acc["balance"] = round(acc["total_debit"] - acc["total_credit"], 2)
        acc["total_debit"] = round(acc["total_debit"], 2)
        acc["total_credit"] = round(acc["total_credit"], 2)
        # Trier les entrées par date
        acc["entries"].sort(key=lambda x: x["date"] or "")
    
    return {
        "organization_id": organization_id,
        "accounts": list(accounts.values()),
        "total_accounts": len(accounts),
    }


# ============================================================
# 2. BALANCE GÉNÉRALE (Trial Balance)
# ============================================================

def get_trial_balance(
    db: Session,
    organization_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> dict:
    """
    Retourne la balance générale : total débit / crédit / solde par compte.
    """
    ledger = get_ledger(db, organization_id, date_from=date_from, date_to=date_to)
    
    balance = []
    total_debit = 0.0
    total_credit = 0.0
    total_solde_debiteur = 0.0
    total_solde_crediteur = 0.0
    
    for acc in ledger["accounts"]:
        solde = acc["balance"]
        balance.append({
            "account_number": acc["account_number"],
            "account_name": acc["account_name"],
            "total_debit": acc["total_debit"],
            "total_credit": acc["total_credit"],
            "solde_debiteur": round(solde, 2) if solde > 0 else 0.0,
            "solde_crediteur": round(-solde, 2) if solde < 0 else 0.0,
        })
        total_debit += acc["total_debit"]
        total_credit += acc["total_credit"]
        if solde > 0:
            total_solde_debiteur += solde
        else:
            total_solde_crediteur += -solde
    
    # Vérification de l'équilibre (débit = crédit)
    is_balanced = abs(total_debit - total_credit) < 0.01
    
    return {
        "organization_id": organization_id,
        "period": {"from": date_from, "to": date_to},
        "accounts": balance,
        "totals": {
            "total_debit": round(total_debit, 2),
            "total_credit": round(total_credit, 2),
            "total_solde_debiteur": round(total_solde_debiteur, 2),
            "total_solde_crediteur": round(total_solde_crediteur, 2),
        },
        "is_balanced": is_balanced,
        "difference": round(total_debit - total_credit, 2),
    }


# ============================================================
# 3. JOURNAL CHRONOLOGIQUE
# ============================================================

def get_journal(
    db: Session,
    organization_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> dict:
    """Retourne toutes les écritures classées par date."""
    query = db.query(JournalEntry).filter(
        JournalEntry.organization_id == organization_id
    )
    entries = query.all()
    
    journal = []
    for entry in entries:
        d = parse_date(entry.date)
        if date_from or date_to:
            if not d:
                continue
            if date_from and d < parse_date(date_from):
                continue
            if date_to and d > parse_date(date_to):
                continue
        
        journal.append({
            "id": str(entry.id),
            "entry_ref": entry.entry_ref,
            "date": d.strftime("%Y-%m-%d") if d else entry.date,
            "source": entry.source,
            "status": entry.status,
            "confidence": entry.confidence,
            "lines": extract_lines(entry),
        })
    
    journal.sort(key=lambda x: x["date"] or "", reverse=True)
    
    return {
        "organization_id": organization_id,
        "entries": journal,
        "total_entries": len(journal),
    }


# ============================================================
# 4. COMPTE DE RÉSULTAT (simplifié)
# ============================================================

def get_income_statement(
    db: Session,
    organization_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> dict:
    """
    Génère un compte de résultat simplifié (SYSCOHADA).
    Charges (classe 6) vs Produits (classe 7).
    """
    balance = get_trial_balance(db, organization_id, date_from, date_to)
    
    charges = []
    produits = []
    total_charges = 0.0
    total_produits = 0.0
    
    for acc in balance["accounts"]:
        num = acc["account_number"]
        if num.startswith("6"):
            montant = acc["total_debit"] - acc["total_credit"]
            charges.append({
                "account_number": num,
                "account_name": acc["account_name"],
                "montant": round(montant, 2),
            })
            total_charges += montant
        elif num.startswith("7"):
            montant = acc["total_credit"] - acc["total_debit"]
            produits.append({
                "account_number": num,
                "account_name": acc["account_name"],
                "montant": round(montant, 2),
            })
            total_produits += montant
    
    resultat = total_produits - total_charges
    
    return {
        "organization_id": organization_id,
        "period": {"from": date_from, "to": date_to},
        "charges": charges,
        "produits": produits,
        "total_charges": round(total_charges, 2),
        "total_produits": round(total_produits, 2),
        "resultat_net": round(resultat, 2),
        "type": "benefice" if resultat > 0 else "perte" if resultat < 0 else "equilibre",
    }


# ============================================================
# 5. BILAN (simplifié)
# ============================================================

def get_balance_sheet(
    db: Session,
    organization_id: str,
    date_to: Optional[str] = None
) -> dict:
    """
    Génère un bilan simplifié (SYSCOHADA).
    Actif (classes 2,3,4,5 débiteurs) vs Passif (classes 1,4 créditeurs).
    """
    balance = get_trial_balance(db, organization_id, date_to=date_to)
    
    actif = []
    passif = []
    total_actif = 0.0
    total_passif = 0.0
    
    for acc in balance["accounts"]:
        num = acc["account_number"]
        
        # ACTIF : classes 2, 3, 5 + 4 débiteur
        if num.startswith(("2", "3", "5")) or (num.startswith("4") and acc["solde_debiteur"] > 0):
            montant = acc["solde_debiteur"]
            if montant > 0:
                actif.append({
                    "account_number": num,
                    "account_name": acc["account_name"],
                    "montant": montant,
                })
                total_actif += montant
        
        # PASSIF : classe 1 + 4 créditeur
        elif num.startswith("1") or (num.startswith("4") and acc["solde_crediteur"] > 0):
            montant = acc["solde_crediteur"]
            if montant > 0:
                passif.append({
                    "account_number": num,
                    "account_name": acc["account_name"],
                    "montant": montant,
                })
                total_passif += montant
    
    return {
        "organization_id": organization_id,
        "date_to": date_to,
        "actif": actif,
        "passif": passif,
        "total_actif": round(total_actif, 2),
        "total_passif": round(total_passif, 2),
        "is_balanced": abs(total_actif - total_passif) < 0.01,
    }