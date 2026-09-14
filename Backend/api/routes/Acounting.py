from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from engine.accounting import (
    get_ledger,
    get_trial_balance,
    get_journal,
    get_income_statement,
    get_balance_sheet,
)

router = APIRouter(prefix="/accounting", tags=["Comptabilité"])


@router.get("/ledger/{organization_id}")
async def ledger(
    organization_id: str,
    account_number: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    only_validated: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Grand livre : toutes les écritures par compte."""
    return get_ledger(db, organization_id, account_number, date_from, date_to, only_validated)


@router.get("/balance/{organization_id}")
async def trial_balance(
    organization_id: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Balance générale : débit / crédit / solde par compte."""
    return get_trial_balance(db, organization_id, date_from, date_to)


@router.get("/journal/{organization_id}")
async def journal(
    organization_id: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Journal chronologique de toutes les écritures."""
    return get_journal(db, organization_id, date_from, date_to)


@router.get("/income-statement/{organization_id}")
async def income_statement(
    organization_id: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Compte de résultat simplifié (Charges vs Produits)."""
    return get_income_statement(db, organization_id, date_from, date_to)


@router.get("/balance-sheet/{organization_id}")
async def balance_sheet(
    organization_id: str,
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Bilan simplifié (Actif vs Passif)."""
    return get_balance_sheet(db, organization_id, date_to)