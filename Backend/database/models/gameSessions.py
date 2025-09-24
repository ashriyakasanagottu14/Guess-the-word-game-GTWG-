from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from bson import ObjectId

class GameSession(BaseModel):
    id: str = Field(default_factory=str, alias="_id")
    user_id: str
    word: str  
    guesses: List[str] = []
    is_win: bool = False
    date_played: datetime = Field(default_factory=datetime.utcnow)

