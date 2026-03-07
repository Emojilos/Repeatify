from fastapi import APIRouter

from app.api.deps import CurrentUser

router = APIRouter()


@router.get("/me")
async def get_me(current_user: CurrentUser) -> dict:
    return {"user_id": current_user["user_id"], "email": current_user["email"]}
