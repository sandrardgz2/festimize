"""
A shared-secret gate for the planning routes.

The service has no user sessions — it is called only by the web app. When
`api_key` is configured, every planning request must present it in the
`X-Analytics-Key` header; a missing or wrong key is 401. When it is blank the
gate is open, which is acceptable only because local development binds the
service to localhost. The Docker deployment sets the key on both services.

/health is deliberately not gated: a health probe must work without secrets.

Targets Python 3.9 syntax.
"""
from fastapi import Header, HTTPException
from typing import Optional

from app.config import get_settings


def require_key(x_analytics_key: Optional[str] = Header(default=None)) -> None:
    expected = get_settings().api_key
    if not expected:
        return
    if x_analytics_key != expected:
        raise HTTPException(status_code=401, detail="bad or missing analytics key")
