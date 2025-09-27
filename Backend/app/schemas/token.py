from pydantic import BaseModel

class Token(BaseModel):
    """Token response schema for authentication."""
    access_token: str
    token_type: str
    role:str

class TokenData(BaseModel):
    """Token payload schema."""
    username: str | None = None
    role: str | None = None  # Added missing default value