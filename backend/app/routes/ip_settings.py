from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
from app.services.ip_settings import get_allowed_ips, update_allowed_ips, verify_ip
from app.utils.auth import verify_token

router = APIRouter(prefix="/api/ip-settings", tags=["IP Settings"])
security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

class IPSettingsRequest(BaseModel):
    allowed_ips: List[str]
    ip_check_enabled: bool = True

class IPVerifyRequest(BaseModel):
    client_ip: str

@router.get("/")
async def get_ip_settings(admin=Depends(get_current_admin)):
    settings = await get_allowed_ips()
    return {"message": "Success", "data": settings}

@router.post("/")
async def save_ip_settings(
    data: IPSettingsRequest,
    admin=Depends(get_current_admin)
):
    settings = await update_allowed_ips(data.allowed_ips, data.ip_check_enabled)
    return {"message": "IP settings saved successfully", "data": settings}

@router.post("/verify")
async def check_ip(request: Request):
    # Real IP fetch karo
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    is_allowed, message = await verify_ip(client_ip)
    return {
        "allowed": is_allowed,
        "client_ip": client_ip,
        "message": message
    }