# -*- coding: utf-8 -*-
"""Routes de rapprochement bancaire automatisé (Feature 2)."""
import io
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from database import get_db, Profile, Organization, JournalEntry, BankStatement, ReconciliationItem, BankAccount
from api.dependencies import get_current_user, is_manager_or_above
from api.audit import log_action
from engine.reconciliation import reconcile, automation_rate

router = APIRouter(tags=["recon"])

ALLOWED_EXT = (".csv", ".xlsx", ".xls", ".json")


def _require_org(user: Profile, db: Session) -> Organization:
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    return org


def _parse_statement(ext: str, content: bytes, account_id: str | None) -> list:
    """Retourne la liste de lignes {date, description, amount}."""
    try:
        if ext == ".json":
            import json
            data = json.loads(content.decode("utf-8"))
            rows = data.get("lines") or data.get("rows") or (data if isinstance(data, list) else [])
        elif ext == ".csv":
            import pandas as pd
            df = pd.read_csv(io.BytesIO(content))
            rows = df.to_dict(orient="records")
        else:
            import pandas as pd
            df = pd.read_excel(io.BytesIO(content))
            rows = df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(400, f"Impossible de lire le relevé : {e}")

    lines = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        lower = {str(k).strip().lower(): v for k, v in r.items()}
        amount = None
        for k, v in lower.items():
            if any(s in k for s in ("montant", "amount", "debit", "credit", "value", "mouvement")):
                try:
                    amount = float(v) if not isinstance(v, str) else float(v.replace(" ", "").replace(",", "."))
                    break
                except (TypeError, ValueError):
                    continue
        date = None
        for k, v in lower.items():
            if any(s in k for s in ("date", "jour", "operation")):
                date = str(v) if not isinstance(v, str) else v
                break
        label = None
        for k, v in lower.items():
            if any(s in k for s in ("libellé", "libelle", "description", "motif", "label", "tiers")):
                label = str(v)
                break
        if amount is not None:
            lines.append({"date": date, "description": label or "", "amount": amount})
    if not lines:
        raise HTTPException(400, "Aucune ligne exploitable dans le relevé (cherchez les colonnes montant/date/libellé)")
    return lines


def _journal_lines(db: Session, org_id) -> list:
    entries = db.query(JournalEntry).filter(JournalEntry.organization_id == org_id).all()
    lines = []
    for e in entries:
        first = (e.lines or [{}])[0] if e.lines else {}
        lines.append({
            "date": e.date,
            "label": first.get("label"),
            "amount": first.get("amount"),
            "ref": e.entry_ref,
            "entry_id": e.id,
        })
    return lines


def _statement_line_for(st: BankStatement, idx: int) -> dict:
    raw = st.raw or []
    return raw[idx] if idx < len(raw) else {}


@router.post("/recon/import")
async def import_statement(
    file: UploadFile = File(...),
    account_id: str | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if not is_manager_or_above(user):
        raise HTTPException(403, "Réservé au manager ou au-dessus")
    org = _require_org(user, db)
    filename = file.filename or "releve"
    ext = "." + (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Format non supporté : {ALLOWED_EXT}")

    content = await file.read()
    lines = _parse_statement(ext, content, account_id)
    account = None
    if account_id:
        account = db.query(BankAccount).filter(BankAccount.id == account_id).first()
    if not account and user.organization_id:
        account = db.query(BankAccount).filter(BankAccount.organization_id == org.id).first()
    if not account:
        account = BankAccount(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            label=filename,
            currency="CDF",
            provider="generic",
        )
        db.add(account)
        db.flush()

    statement = BankStatement(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        account_id=account.id,
        date_range=None,
        source="upload",
        raw=lines,
        imported_by=user.id,
    )
    db.add(statement)
    db.flush()

    # Rapprochement
    journal = _journal_lines(db, org.id)
    results = reconcile(journal, lines)

    items = []
    for r in results:
        entry_idx = r["entry_index"]
        entry_ref = None
        entry_id = None
        if entry_idx is not None and entry_idx < len(journal):
            entry_ref = journal[entry_idx].get("ref")
            entry_id = journal[entry_idx].get("entry_id")
        item = ReconciliationItem(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            statement_id=statement.id,
            statement_line=(lines[r["statement_index"]] if r["statement_index"] is not None else {}),
            entry_id=(entry_id if entry_id else None),
            status=r["status"],
            confidence=r["confidence"],
        )
        db.add(item)
        items.append({"entry_ref": entry_ref, **r})

    db.commit()

    auto_rate = automation_rate(results)
    log_action(
        db, str(user.id), "recon.import",
        {"filename": filename, "lines": len(lines), "automation_rate": auto_rate},
        request.client.host if request.client else None,
    )
    return {
        "statement_id": str(statement.id),
        "account_id": str(account.id),
        "lines_count": len(lines),
        "automation_rate": auto_rate,
        "results": _serialize_results(results, lines),
    }


def _serialize_results(results: list, lines: list) -> list:
    return [
        {
            "status": r["status"],
            "confidence": r["confidence"],
            "entry_index": r["entry_index"],
            "statement_index": r["statement_index"],
            "statement_line": (lines[r["statement_index"]] if r["statement_index"] is not None else None),
        }
        for r in results
    ]


@router.get("/recon/statements")
async def list_statements(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if not user.organization_id:
        return []
    statements = (
        db.query(BankStatement)
        .filter(BankStatement.organization_id == user.organization_id)
        .order_by(BankStatement.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": str(s.id),
            "account_id": str(s.account_id) if s.account_id else None,
            "date_range": s.date_range,
            "source": s.source,
            "lines_count": len(s.raw or []),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in statements
    ]
