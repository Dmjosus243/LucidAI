from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import logging

from config import config
from database import get_db, Profile, Organization
from api.dependencies import get_current_user, require_org_admin
from api.audit import log_action

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])

# Devise : Franc Congolais
CURRENCY = "CDF"

# Plans proposés (montant en CDF, correspond au montant facturé au client)
PLANS = {
    "pro": {"label": "Pro", "amount": 55000, "tier": "pro"},
    "enterprise": {"label": "Enterprise", "amount": 142000, "tier": "enterprise"},
}

MAISHAPAY_CHECKOUT_URL = "https://marchand.maishapay.online/payment/vers1.0/merchant/checkout"


class CheckoutRequest(BaseModel):
    plan: str
    # Optional: phone for Mobile Money push if we later support direct billing.
    phone: str | None = None


def _get_org(db: Session, user: Profile) -> Organization:
    if not user.organization_id:
        raise HTTPException(400, "Vous n'avez pas d'organisation")
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        raise HTTPException(404, "Organisation non trouvée")
    return org


@router.post("/billing/checkout")
async def create_checkout(
    req: CheckoutRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: Profile = Depends(get_current_user),
):
    """
    Initialise un paiement MaishaPay (Checkout) et renvoie une URL vers une
    page qui redirige le client vers le comptoir de paiement hébergé par MaishaPay.
    """
    require_org_admin(user)

    if not config.MAISHAPAY_PUBLIC_KEY or not config.MAISHAPAY_SECRET_KEY:
        raise HTTPException(500, "MaishaPay non configuré. Ajoutez MAISHAPAY_PUBLIC_KEY et MAISHAPAY_SECRET_KEY dans le .env")

    plan = PLANS.get(req.plan)
    if not plan:
        raise HTTPException(400, f"Plan invalide. Choisissez parmi : {', '.join(PLANS.keys())}")

    org = _get_org(db, user)
    plan_char = "P" if plan == "pro" else "E"
    # Format du ref: LUCID + plan(P/E) + 6 premiers hex de l'org + aléatoire
    transaction_ref = f"LUCID{plan_char}{org.id.hex[:6]}{uuid.uuid4().hex[:6]}".upper()

    # L'URL de checkout redirige vers une page backend qui soumet le form MaishaPay
    checkout_url = f"{config.BACKEND_URL}/api/v1/billing/pay/{req.plan}?tx={transaction_ref}"

    log_action(
        db, str(user.id), "billing.checkout_started",
        {"plan": req.plan, "transaction_ref": transaction_ref, "amount_cdf": plan["amount"]},
        request.client.host if request.client else None,
    )

    return {"checkout_url": checkout_url, "transaction_ref": transaction_ref}


@router.get("/billing/pay/{plan}")
async def payment_page(
    plan: str,
    tx: str = "",
    request: Request = None,
):
    """
    Page intermédiaire (backend) qui rend un formulaire auto-soumis vers le
    comptoir MaishaPay. Nécessaire car le checkout MaishaPay se fait via un form POST.
    """
    plan_data = PLANS.get(plan)
    if not plan_data:
        raise HTTPException(400, "Plan invalide")

    if not config.MAISHAPAY_PUBLIC_KEY or not config.MAISHAPAY_SECRET_KEY:
        raise HTTPException(500, "MaishaPay non configuré")

    gateway_mode = config.MAISHAPAY_GATEWAY_MODE  # 0 sandbox, 1 live

    callback_url = f"{config.BACKEND_URL}/api/v1/billing/callback"
    return_url = f"{config.FRONTEND_URL}/organisation?paiement=resultat&ref={tx}"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Redirection vers le paiement sécurisé</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#0a0f1a;color:#fff;display:flex;
        align-items:center;justify-content:center;height:100vh;margin:0;}}
  .box{{text-align:center;}}
  .spinner{{width:40px;height:40px;border:4px solid #1e293b;border-top-color:#22d3ee;
           border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 16px;}}
  @keyframes spin{{to{{transform:rotate(360deg)}}}}
</style>
</head>
<body>
  <div class="box">
    <div class="spinner"></div>
    <p>Redirection vers le paiement sécurisé...</p>
  </div>
  <form action="{MAISHAPAY_CHECKOUT_URL}" method="POST" id="payform">
    <input type="hidden" name="gatewayMode" value="{gateway_mode}">
    <input type="hidden" name="publicApiKey" value="{config.MAISHAPAY_PUBLIC_KEY}">
    <input type="hidden" name="secretApiKey" value="{config.MAISHAPAY_SECRET_KEY}">
    <input type="hidden" name="montant" value="{plan_data['amount']}">
    <input type="hidden" name="devise" value="{CURRENCY}">
    <input type="hidden" name="transactionReference" value="{tx}">
    <input type="hidden" name="callbackUrl" value="{callback_url}">
  </form>
  <script>document.getElementById('payform').submit();</script>
</body>
</html>"""
    return Response(content=html, media_type="text/html")


@router.get("/billing/callback")
async def billing_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    URL de retour MaishaPay. MaishaPay redirige le client ici avec le statut dans
    l'URL (GET) : ?status , description, transactionRefId, operatorRefId
    C'est ici qu'on traite le résultat du paiement et qu'on met à jour l'organisation.
    """
    q = request.query_params
    status = q.get("status", "")
    ref = q.get("transactionRefId", "") or q.get("ref", "")
    description = q.get("description", "")

    logger.info("MaishaPay callback: status=%s ref=%s desc=%s", status, ref, description)

    if status == "202":
        # ACCEPTED -> on cherche l'organisation via le ref de transaction
        # format du ref: "LUCID" + "P"/"E" + 6 hex org + aléatoire
        org_db_id = None
        tier = "pro"
        if ref.startswith("LUCID") and len(ref) >= 5 + 1 + 6:
            if ref[5] == "E":
                tier = "enterprise"
            hex6 = ref[6:12]
            # On retrouve par correspondance partielle du UUID
            orgs = db.query(Organization).all()
            for o in orgs:
                if o.id.hex.startswith(hex6):
                    org_db_id = o.id
                    break
        if org_db_id:
            org = db.query(Organization).filter(Organization.id == org_db_id).first()
            if org:
                org.subscription_tier = tier
                org.subscription_status = "active"
                db.commit()
                log_action(db, None, "billing.payment_success", {
                    "transaction_ref": ref, "organization_id": str(org.id), "tier": tier,
                })

    # On redirige le client vers le frontend avec un indicateur de résultat
    result = "succes" if status == "202" else "echec"
    return RedirectResponse(url=f"{config.FRONTEND_URL}/organisation?paiement={result}&ref={ref}")


@router.get("/billing/status/{transaction_ref}")
async def billing_status(transaction_ref: str, db: Session = Depends(get_db)):
    """Endpoint de contrôle/debug."""
    return {"transaction_ref": transaction_ref}
