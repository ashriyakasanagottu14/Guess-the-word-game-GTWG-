from pydantic import BaseModel
from typing import List


class DailyReport(BaseModel):
    date: str
    user_count: int
    correct_guess_count: int


class UserDailyStat(BaseModel):
    date: str
    words_tried: int
    correct_guesses: int


class UserReport(BaseModel):
    user_id: str
    from_date: str
    to_date: str
    stats: List[UserDailyStat]
