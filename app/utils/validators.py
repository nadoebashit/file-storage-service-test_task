from fastapi import HTTPException, status
from typing import Literal

ROLE_LIMITS = {
    "USER":    {"max_mb": 10,  "types": {"pdf"},              "can_visibility": {"PRIVATE"}},
    "MANAGER": {"max_mb": 50,  "types": {"pdf","doc","docx"}, "can_visibility": {"PRIVATE","DEPARTMENT","PUBLIC"}},
    "ADMIN":   {"max_mb": 100, "types": {"pdf","doc","docx"}, "can_visibility": {"PRIVATE","DEPARTMENT","PUBLIC"}},
}

def ensure_upload_allowed(role: str, ext: str, size_bytes: int, requested_visibility: str) -> str:
    ext = ext.lower().lstrip(".")
    limits = ROLE_LIMITS[role]
    max_bytes = limits["max_mb"] * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Max size {limits['max_mb']}MB for role {role}")
    if ext not in limits["types"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Extension .{ext} not allowed for role {role}")
    # USER всегда PRIVATE
    if role == "USER":
        return "PRIVATE"
    # иначе проверить requested_visibility
    if requested_visibility.upper() not in limits["can_visibility"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Visibility not allowed")
    return requested_visibility.upper()
