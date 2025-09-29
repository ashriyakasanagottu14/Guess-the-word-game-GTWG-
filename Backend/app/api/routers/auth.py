from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
import random
import string


from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.roles import PLAYER
from app.core.auth import current_user
from app.db.mongodb import get_database
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.user import UserOut
from app.utils.validators import validate_username, validate_password
from app.utils.email import email_service

router = APIRouter(prefix="/auth", tags=["auth"])
db = get_database()


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Initiate password reset process.
    """
    db = await get_database()
    user = await db.users.find_one({"email": payload.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist.",
        )

    # Generate a 6-digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    otp_hash = get_password_hash(otp)
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)  # OTP valid for 10 minutes

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"reset_otp_hash": otp_hash, "reset_otp_expiry": otp_expiry}},
    )

    # Send OTP via email
    email_sent = await email_service.send_otp_email(
        to_email=payload.email,
        otp=otp,
        username=user.get("username")
    )

    if not email_sent:
        # If email fails, still log the OTP for development/testing
        print(f"Email failed - Generated OTP for {payload.email}: {otp}")
        return {
            "message": "An OTP has been generated, but email delivery failed. Please check server logs.",
            "otp_for_testing": otp,  # For development/testing purposes when email fails
        }

    return {
        "message": "An OTP has been sent to your email address.",
    }


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    """
    Reset user's password using OTP.
    """
    db = await get_database()
    user = await db.users.find_one({"email": payload.email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    reset_otp_hash = user.get("reset_otp_hash")
    reset_otp_expiry = user.get("reset_otp_expiry")

    if not reset_otp_hash or not reset_otp_expiry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset was not requested.",
        )

    if datetime.now(timezone.utc) > reset_otp_expiry.replace(tzinfo=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired.",
        )

    if not verify_password(payload.otp, reset_otp_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP.",
        )

    validate_password(payload.new_password)
    new_password_hash = get_password_hash(payload.new_password)

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password_hash": new_password_hash},
            "$unset": {"reset_otp_hash": "", "reset_otp_expiry": ""},
        },
    )

    return {"message": "Password has been reset successfully."}


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
