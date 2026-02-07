from fastapi import APIRouter, Depends
from backend.app.db.models import User
from backend.app.dependencies.auth import get_current_active_user

router = APIRouter(prefix="/protected", tags=["Protected"])


@router.get("/test")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Test protected route that requires authentication."""
    return {
        "message": "This is a protected route",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }