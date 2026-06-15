from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.services.settings import get_office_settings, update_office_settings, verify_location
from app.utils.auth import verify_token

router = APIRouter(prefix="/api/settings", tags=["Settings"])
security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

class OfficeSettingsRequest(BaseModel):
    latitude: float
    longitude: float
    radius: float
    office_name: str = "Main Office"

class LocationVerifyRequest(BaseModel):
    latitude: float
    longitude: float

@router.get("/office")
async def get_settings(admin=Depends(get_current_admin)):
    settings = await get_office_settings()
    if not settings:
        return {"message": "No settings configured", "data": None}
    return {"message": "Success", "data": settings}

@router.post("/office")
async def save_settings(
    data: OfficeSettingsRequest,
    admin=Depends(get_current_admin)
):
    settings = await update_office_settings(
        data.latitude, data.longitude, data.radius, data.office_name
    )
    return {"message": "Office settings saved successfully", "data": settings}

@router.post("/verify-location")
async def check_location(data: LocationVerifyRequest):
    is_inside, distance = await verify_location(data.latitude, data.longitude)
    if is_inside:
        return {
            "allowed": True,
            "distance": distance,
            "message": "Location verified. You are inside the office area."
        }
    else:
        return {
            "allowed": False,
            "distance": distance,
            "message": "You are outside the office attendance area. Please move closer to the office location."
        }