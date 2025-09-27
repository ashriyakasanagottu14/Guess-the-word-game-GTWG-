import re
from fastapi import HTTPException

USERNAME_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])[A-Za-z]{5,}$")
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[$%*@]).{5,}$")
GUESS_RE = re.compile(r"^[A-Z]{5}$")


def validate_username(username: str):
    if not USERNAME_RE.match(username or ""):
        raise HTTPException(status_code=422, detail="Username must be letters only, at least 5 chars, with both upper and lower case")


def validate_password(password: str):
    if not PASSWORD_RE.match(password or ""):
        raise HTTPException(status_code=422, detail="Password must be >=5 chars, include letter, digit, and one of $, %, *, @")


def validate_guess(guess: str):
    if not GUESS_RE.match(guess or ""):
        raise HTTPException(status_code=422, detail="Guess must be exactly 5 uppercase letters")
