from typing import Literal
from pydantic import BaseModel


class StoryRating(BaseModel):
    rating: Literal["adequate", "inadequate"]
