from datetime import date

from pydantic import BaseModel, EmailStr, Field, model_validator


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


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    exam_date: date | None = None
    target_score: int | None = Field(None, ge=27, le=100)

    @model_validator(mode="after")
    def check_exam_date_not_in_past(self):
        if self.exam_date is not None and self.exam_date < date.today():
            msg = "exam_date must not be in the past"
            raise ValueError(msg)
        return self


class UserStats(BaseModel):
    current_xp: int = 0
    current_level: int = 1
    current_streak: int = 0
    longest_streak: int = 0
    total_problems_solved: int = 0
