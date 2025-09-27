from datetime import datetime
from pydantic import BaseModel
from typing import List


class StartGameResponse(BaseModel):
    game_id: str
    started_at: datetime
    status: str
    max_guesses: int = 5
    guesses_made: int


class GuessRequest(BaseModel):
    game_id: str
    guess: str


class GuessEntry(BaseModel):
    guess: str
    result: list[str]
    guessed_at: datetime


class GameOut(BaseModel):
    id: str
    user_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    guesses: List[GuessEntry] = []
    remaining_guesses: int
    won: bool
