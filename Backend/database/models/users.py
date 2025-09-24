from pydantic import BaseModel, Field, validator


class UserCreate(BaseModel):
    email: str = Field(..., example="alice@gmail.com")
    password: str = Field(..., min_length=5, example="MyPass1$")
    password_retype: str = Field(..., min_length=5, example="MyPass1$")
    
    @validator('password')
    def password_complexity(cls, v):
        if not any(x.isalpha() for x in v):
            raise ValueError("Password must include letters.")
        if not any(x.isdigit() for x in v):
            raise ValueError("Password must include numbers.")
        if not any(x in "$%@*" for x in v):
            raise ValueError("Password must include one special char: $ % * @")
        return v

    @validator('password_retype')
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match.")
        return v

    @validator('email')
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format.")
        return v

# Schema for returning user info (without password)
class UserOut(BaseModel):
    id: str
    username: str
    email: str