from __future__ import annotations
from typing import Optional

ABSOLUTE_PREFIXES = ("http://", "https://")

def ensure_absolute(url: Optional[str], base: str) -> Optional[str]:
    """Devuelve una URL absoluta a partir de `url`.
    Si `url` ya es absoluta o es falsy, se retorna tal cual.
    `base` debe incluir esquema y host (p.ej. request.base_url).
    """
    if not url:
        return url
    if url.startswith(ABSOLUTE_PREFIXES):
        return url
    base = base.rstrip("/")
    return f"{base}/{url.lstrip('/')}"

__all__ = ["ensure_absolute"]
