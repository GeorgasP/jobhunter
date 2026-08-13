"""
/api/stripe — payments + webhooks.
"""
import logging

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import CurrentUser
from app.config import settings
from app.db.session import get_db
from app.schemas import BillingPortalResponse, CheckoutSessionRequest, CheckoutSessionResponse

router = APIRouter()
log = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


PRICE_BY_TIER = {
    "pro": settings.STRIPE_PRICE_PRO,
    "premium": settings.STRIPE_PRICE_PREMIUM,
}


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout(
    req: CheckoutSessionRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe Checkout session for tier upgrade."""
    price = PRICE_BY_TIER.get(req.tier)
    if not price:
        raise HTTPException(status_code=400, detail=f"Unknown tier: {req.tier}")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=user.email,
            line_items=[{"price": price, "quantity": 1}],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            metadata={"user_id": str(user.id), "tier": req.tier},
            allow_promotion_codes=True,
            billing_address_collection="required",
            automatic_tax={"enabled": True},
        )
    except stripe.error.StripeError as e:
        log.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    return CheckoutSessionResponse(url=session.url, session_id=session.id)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhook events.
    Events of interest:
      - checkout.session.completed → upgrade user tier
      - customer.subscription.deleted → downgrade to free
      - invoice.payment_failed → flag user
    """
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature failed: {e}")

    event_type = event["type"]
    log.info(f"Stripe webhook: {event_type}")

    # TODO: Implement actual upgrade/downgrade logic with Subscription model
    if event_type == "checkout.session.completed":
        # session = event["data"]["object"]
        # user_id = session["metadata"]["user_id"]
        # tier = session["metadata"]["tier"]
        # Update user.tier, create Subscription record
        pass

    elif event_type == "customer.subscription.deleted":
        # Downgrade user to free
        pass

    elif event_type == "invoice.payment_failed":
        # Email user, mark account
        pass

    return {"received": True}


@router.get("/portal", response_model=BillingPortalResponse)
async def billing_portal(user: CurrentUser):
    """Generate Stripe Customer Portal URL για user to manage subscription."""
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription")

    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=settings.FRONTEND_URL + "/dashboard",
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return BillingPortalResponse(url=session.url)
