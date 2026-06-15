from pydantic import BaseModel, Field


class FavoriteState(BaseModel):
    landmark_id: str
    favorited: bool
    count: int


class CommentCreateIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class CommentOut(BaseModel):
    id: str
    landmark_id: str
    user_id: str
    username: str
    content: str
    created_at: str
