# -*- coding: utf-8 -*-
"""Routes OCR + validation humaine (Feature 1)."""
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, Profile, Organization, OCRDocument, JournalEntry
from api.dependencies import get_current_user, is_manager_or_above
from api.audit import log_action
from engine.ocr_pipeline import extract_document, build_entries

router = APIRouter(tags=["ocr"])

ALLOWED_EXT = (".csv", ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".xls", ".json")


class ValidateRequest(BaseModel):
    lines: list  # liste de dicts {label, date, amount, tax_rate}


def _require_org(user: Profile, db: Session) -> Organization:
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    return org


def _scope_doc(db: Session, user: Profile, doc_id: str) -> OCRDocument:
    doc = db.query(OCRDocument).filter(OCRDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document introuvable")
    if user.role != "super_admin" and doc.organization_id != user.organization_id:
        raise HTTPException(403, "Document non autorisé")
    return doc


@router.post("/ocr/upload")
async def ocr_upload(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    org = _require_org(user, db)
    filename = file.filename or "document"
    ext = "." + (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Format non supporté. Formats autorisés : {', '.join(ALLOWED_EXT)}")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Fichier vide")

    # Les fichiers structurés sont parsés directement (grande précision)
    structured_rows = None
    if ext in (".csv", ".xlsx", ".xls", ".json"):
        try:
            if ext == ".csv":
                import pandas as pd
                df = pd.read_csv(io.BytesIO(content))
                structured_rows = df.to_dict(orient="records")
            elif ext in (".xlsx", ".xls"):
                import pandas as pd
                df = pd.read_excel(io.BytesIO(content))
                structured_rows = df.to_dict(orient="records")
            elif ext == ".json":
                import json
                structured_rows = json.loads(content.decode("utf-8"))
                if isinstance(structured_rows, dict):
                    structured_rows = structured_rows.get("rows") or structured_rows.get("data") or []
        except Exception as e:
            raise HTTPException(400, f"Impossible de lire le fichier structuré : {e}")

    result = extract_document(filename, content, structured_rows=structured_rows)
    lines = result["lines"]

    doc = OCRDocument(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        user_id=user.id,
        filename=filename,
        status="pending",
        engine=result["engine"],
        extracted_json=lines,
        confidence=result["confidence"],
    )
    db.add(doc)
    db.commit()

    log_action(
        db, str(user.id), "ocr.upload",
        {"filename": filename, "engine": result["engine"],
         "lines": len(lines), "confidence": result["confidence"]},
        request.client.host if request.client else None,
    )
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "status": doc.status,
        "engine": doc.engine,
        "confidence": doc.confidence,
        "lines": lines,
        "raw_text": result.get("raw_text", ""),
    }


@router.get("/ocr/documents")
async def list_ocr_documents(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if user.role == "super_admin":
        docs = db.query(OCRDocument).order_by(OCRDocument.created_at.desc()).limit(100).all()
    else:
        if not user.organization_id:
            return []
        docs = (
            db.query(OCRDocument)
            .filter(OCRDocument.organization_id == user.organization_id)
            .order_by(OCRDocument.created_at.desc())
            .limit(100)
            .all()
        )
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "status": d.status,
            "engine": d.engine,
            "confidence": d.confidence,
            "lines": d.extracted_json or [],
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.post("/ocr/documents/{doc_id}/validate")
async def validate_ocr_document(
    doc_id: str,
    req: ValidateRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if not is_manager_or_above(user):
        raise HTTPException(403, "Réservé au manager ou au-dessus")
    doc = _scope_doc(db, user, doc_id)
    if doc.status == "validated":
        raise HTTPException(400, "Document déjà validé")

    org = _require_org(user, db)
    if not req.lines:
        raise HTTPException(400, "Aucune ligne à valider")

    normalized = []
    for line in req.lines:
        amount = line.get("amount")
        if amount is None:
            raise HTTPException(400, "Montant manquant sur une ligne")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise HTTPException(400, f"Montant invalide : {amount}")
        date = line.get("date")
        normalized.append({
            "label": line.get("label", ""),
            "date": str(date) if date else None,
            "amount": amount,
            "tax_rate": line.get("tax_rate"),
            "confidence": line.get("confidence", 1.0),
        })

    entries = build_entries(normalized, source="ocr")
    created_refs = []
    for en in entries:
        entry = JournalEntry(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            user_id=user.id,
            entry_ref=en["entry_ref"],
            date=en["date"],
            source="ocr",
            confidence=float(en["confidence"]),
            lines=[{
                "label": en["label"],
                "amount": en["amount"],
                "tax_rate": en["tax_rate"],
            }],
            status="validated",
            validated_by=user.id,
        )
        db.add(entry)
        created_refs.append(en["entry_ref"])

    doc.status = "validated"
    doc.validated_json = normalized
    doc.validated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    doc.validated_by = user.id
    db.commit()

    log_action(
        db, str(user.id), "ocr.validate",
        {"filename": doc.filename, "entries": created_refs, "count": len(created_refs)},
        request.client.host if request.client else None,
    )
    return {"ok": True, "doc_id": str(doc.id), "entries": created_refs}


@router.post("/ocr/documents/{doc_id}/reject")
async def reject_ocr_document(
    doc_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    if not is_manager_or_above(user):
        raise HTTPException(403, "Réservé au manager ou au-dessus")
    doc = _scope_doc(db, user, doc_id)
    if doc.status == "validated":
        raise HTTPException(400, "Document déjà validé")
    doc.status = "rejected"
    db.commit()
    log_action(
        db, str(user.id), "ocr.reject", {"filename": doc.filename},
        request.client.host if request.client else None,
    )
    return {"ok": True, "doc_id": str(doc.id)}


@router.get("/ocr/entries")
async def list_journal_entries(
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
    limit: int = 200,
):
    """Liste les écritures comptables de l'organisation (issues OCR/recon/prédit)."""
    if not user.organization_id:
        return []
    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.organization_id == user.organization_id)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(e.id),
            "entry_ref": e.entry_ref,
            "date": e.date,
            "source": e.source,
            "confidence": e.confidence,
            "status": e.status,
            "lines": e.lines or [],
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
