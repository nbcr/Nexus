import json
import logging
import os
import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings


logger = logging.getLogger("brevo_webhook")

if not logger.handlers:
    logs_dir = "/home/nexus/nexus/logs"
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
async def brevo_webhook(request: Request) -> dict[str, Any]:
    """Receive Brevo webhook events and log them for processing."""

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

    return {"status": "ok", "received": len(events)}
