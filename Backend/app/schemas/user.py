from datetime import datetime
from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    email: str
    created_at: datetime
    last_login_at: datetime | None = None
