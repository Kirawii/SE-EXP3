from pydantic import BaseModel, EmailStr, Field


class ProfileUpdateIn(BaseModel):
    nickname: str | None = Field(default=None, max_length=30)
    avatar: str | None = Field(default=None, max_length=300)


class UserPublicOut(BaseModel):
    id: str
    username: str
    email: EmailStr | None = None
    role: str
    nickname: str | None = None
    avatar: str | None = None
    disabled: bool = False
    created_at: str
