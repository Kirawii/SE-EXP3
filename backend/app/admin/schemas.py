from typing import Literal

from pydantic import BaseModel


class ReviewIn(BaseModel):
    action: Literal["approve", "reject"]
