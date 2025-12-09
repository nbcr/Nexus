import json
import logging
import os
import secrets
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status, BackgroundTasks

from app.core.config import settings
from app.models.user import BrevoEmailEvent


logger = logging.getLogger("brevo_webhook")

if not logger.handlers:
    # Use relative path for cross-platform compatibility
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    logs_dir = str(PROJECT_ROOT / "logs")
    os.makedirs(logs_dir, exist_ok=True)
    handler = logging.FileHandler(os.path.join(logs_dir, "brevo_webhook.log"))
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


router = APIRouter()


def _get_token_from_request(request: Request) -> str | None:
    """Extract webhook token from Authorization bearer header or custom headers."""
    # Brevo sends token in Authorization header as "bearer <token>"
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]  # Strip "bearer " prefix
    
    # Fallback to custom headers for other webhook sources
    return (
        request.headers.get("X-Brevo-Signature")
        or request.headers.get("X-Brevo-Webhook-Token")
        or request.headers.get("X-Webhook-Token")
        or request.query_params.get("token")
    )


def _require_valid_token(token: str | None, request: Request) -> None:
    expected = settings.BREVO_WEBHOOK_TOKEN
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Brevo webhook token not configured",
        )

    if not token or not secrets.compare_digest(token, expected):
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(
            "Brevo webhook invalid token from %s headers=%s", client_ip, {
                k: v
                for k, v in request.headers.items()
                if k.lower() in {"x-brevo-signature", "x-brevo-webhook-token", "x-webhook-token"}
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token",
        )


@router.post("/brevo", status_code=status.HTTP_200_OK)
async def brevo_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Receive Brevo webhook events and store them for registration validation."""

    token = _get_token_from_request(request)
    _require_valid_token(token, request)

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")

    events = payload if isinstance(payload, list) else [payload]
    try:
        sample = json.dumps(events[:1], default=str)[:2000]
    except Exception:
        sample = "<unserializable payload>"

    logger.info("Brevo webhook received events=%d sample=%s", len(events), sample)
    
    # Store events in background
    background_tasks.add_task(_store_brevo_events, events)

    return {"status": "ok", "received": len(events)}


async def _store_brevo_events(events):
    """Store email events in database asynchronously."""
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            for event in events:
                email = event.get("email")
                event_type = event.get("event")
                
                # Only track events that indicate email problems
                if email and event_type in ("invalid_email", "bounce", "complaint", "unsubscribe", "hard_bounce"):
                    event_str = json.dumps(event, default=str)
                    brevo_event = BrevoEmailEvent(
                        email=email,
                        event_type=event_type,
                        event_data=event_str[:1000]  # Truncate to 1000 chars
                    )
                    db.add(brevo_event)
                    logger.info("Stored email event: %s for %s", event_type, email)
            
            await db.commit()
        except Exception as e:
            logger.error("Failed to store brevo events: %s", e)
            await db.rollback()
