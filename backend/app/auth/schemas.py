import re

from pydantic import BaseModel, EmailStr, Field, field_validator


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)

    @field_validator("username")
    @classmethod
    def _check_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise ValueError("用户名只允许字母、数字、下划线，长度 3-20")
        return v

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("密码至少 8 位，且需同时包含字母与数字")
        return v


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str
    nickname: str | None = None
    avatar: str | None = None
    created_at: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: UserOut
