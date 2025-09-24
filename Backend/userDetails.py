from fastapi import HTTPException
from database.config import db
from database.models.users import UserCreate, UserOut
from passlib.hash import bcrypt
from bson import ObjectId

async def create_user(user:UserCreate)->UserOut:
    exsisting_user=await db.database.users.find_one({"email":user.email})
    if exsisting_user:
        raise HTTPException(status_code=400,detail="User already exists")
    
    hashed_password=bcrypt.hash(user.password)
    user_dict=user.dict()
    user_dict["password"]=hashed_password
    result = await db.database.users.insert_one(user_dict)

    username = user.email.split("@")[0]

    return UserOut(id=str(result.inserted_id), username=username, email=user.email)

