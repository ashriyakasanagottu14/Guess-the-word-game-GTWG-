# Standard library imports
from datetime import datetime, timezone, timedelta
from typing import List, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from bson import ObjectId

# Local application imports
from app.core.roles import ADMIN
from app.core.security import verify_password, create_access_token
from app.db.mongodb import get_database
from app.schemas.token import Token
from app.core.config import settings
from app.schemas.report import DailyReport, UserReport, UserDailyStat
from app.schemas.user import UserOut
from app.core.auth import require_role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserOut], dependencies=[Depends(require_role(ADMIN))])
async def get_users_list():
    """
    Get a list of all users.
    """
    db = await get_database()
    users = await db.users.find({"role": "PLAYER"}).to_list(length=None)   
    print('users',users)
    return [UserOut(
        id=str(user["_id"]),
        username=user["username"],
        email=user.get("email"),
        role=user.get("role"),
        created_at=user.get("created_at"),
        last_login_at=user.get("last_login_at")
    ) for user in users]


@router.post("/login", response_model=Token)
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Admin login endpoint.
    
    Authenticates an admin user and returns an access token.
    """
    db = await get_database()
    admin = await db.users.find_one({
        "username": form_data.username,
        "role": ADMIN
    })
    
    if not admin or not verify_password(form_data.password, admin.get("hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await db.users.update_one(
        {"_id": admin["_id"]},
        {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )
    
    # Create access token
    access_token = create_access_token(
        subject=str(admin["_id"]),
        username=admin["username"],
        role=admin["role"],
        expires_minutes=settings.JWT_EXPIRES_MINUTES
    )
    
    return {"access_token": access_token, "token_type": "bearer","role": admin["role"]}





@router.get("/report/daily", response_model=DailyReport, dependencies=[Depends(require_role(ADMIN))])
async def daily_report(date: str):
    db = await get_database()
    day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

    user_ids = await db.games.distinct("user_id", {"started_at": {"$gte": start, "$lte": end}})
    won_count = await db.games.count_documents({"started_at": {"$gte": start, "$lte": end}, "status": "WON"})

    return DailyReport(date=date, user_count=len(user_ids), correct_guess_count=won_count)


@router.get("/report/user/{user_id}", response_model=UserReport, dependencies=[Depends(require_role(ADMIN))])
async def user_report(user_id: str, from_date: str, to_date: str):
    db = await get_database()

    from_day = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
    to_day = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc)

    stats: List[UserDailyStat] = []
    day = from_day
    while day <= to_day:
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        tried = await db.games.count_documents({"user_id": ObjectId(user_id), "started_at": {"$gte": start, "$lte": end}})
        correct = await db.games.count_documents({"user_id": ObjectId(user_id), "started_at": {"$gte": start, "$lte": end}, "status": "WON"})
        stats.append(UserDailyStat(date=day.date().isoformat(), words_tried=tried, correct_guesses=correct))
        day = day + timedelta(days=1)

    return UserReport(user_id=user_id, from_date=from_date, to_date=to_date, stats=stats)



class WordCreate(BaseModel):
    text: str
    active: Optional[bool] = True

@router.post("/words", response_model=dict)
async def add_word(
    word_data: WordCreate,
    _: dict = Depends(require_role(ADMIN))
):
    db = await get_database()
    text = word_data.text.strip().upper()
    
    if len(text) != 5 or not text.isalpha():
        raise HTTPException(
            status_code=422, 
            detail="Word must be 5 letters (A-Z)"
        )
        
    exists = await db.words.find_one({"text": text})
    if exists:
        raise HTTPException(
            status_code=409, 
            detail="Word already exists"
        )
        
    res = await db.words.insert_one({
        "text": text, 
        "active": word_data.active,
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "id": str(res.inserted_id), 
        "text": text, 
        "active": word_data.active
    }

@router.get("/words")
async def list_words(active: bool | None = None, _: dict = Depends(require_role(ADMIN))):
    db = await get_database()
    query = {}
    if active is not None:
        query["active"] = active
    words = [
        {"id": str(w["_id"]), "text": w["text"], "active": w.get("active", True)}
        async for w in db.words.find(query)
    ]
    return words

@router.patch("/words/{word_id}")
async def update_word(word_id: str, active: bool | None = None, _: dict = Depends(require_role(ADMIN))):
    db = await get_database()
    update = {}
    if active is not None:
        update["active"] = active
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.words.update_one({"_id": ObjectId(word_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Word not found")
    w = await db.words.find_one({"_id": ObjectId(word_id)})
    return {"id": word_id, "text": w["text"], "active": w.get("active", True)}
