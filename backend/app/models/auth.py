from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str


class UserProfile(BaseModel):
    id: str
    email: str | None = None
    display_name: str | None = None
    exam_date: str | None = None
    target_score: int | None = None
    current_xp: int = 0
    current_level: int = 1
    current_streak: int = 0
    longest_streak: int = 0
