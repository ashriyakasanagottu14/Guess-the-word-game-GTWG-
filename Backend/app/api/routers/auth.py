from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId


from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.roles import PLAYER
from app.core.auth import current_user
from app.db.mongodb import get_database
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.utils.validators import validate_username, validate_password

router = APIRouter(prefix="/auth", tags=["auth"])
db = get_database()


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterRequest):
    db = await get_database()
    validate_username(payload.username)
    validate_password(payload.password)
    # Check for existing username or email
    existing = await db.users.find_one({"$or": [
        {"username": payload.username},
        {"email": payload.email}
    ]})
    if existing:
        if existing.get("username") == payload.username:
            raise HTTPException(status_code=409, detail="Username already exists")
        else:
            raise HTTPException(status_code=409, detail="Email already exists")
    now = datetime.now(timezone.utc)
    doc = {
        "username": payload.username,
        "email": payload.email,
        "password_hash": get_password_hash(payload.password),
        "role": PLAYER,
        "created_at": now,
        "last_login_at": None,
    }
    res = await db.users.insert_one(doc)
    return UserOut(id=str(res.inserted_id), username=doc["username"], role=doc["role"],email=doc["email"], created_at=now, last_login_at=None)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    db = await get_database()
    user = await db.users.find_one({"username": payload.username})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": datetime.now(timezone.utc)}})
    token = create_access_token(str(user["_id"]), user["username"], user.get("role", PLAYER))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user=Depends(current_user)):
    db = await get_database()
    return UserOut(
        id=str(user["_id"]),
        username=user["username"],
        role=user.get("role", PLAYER),
        created_at=user["created_at"],
        last_login_at=user.get("last_login_at"),
    )
