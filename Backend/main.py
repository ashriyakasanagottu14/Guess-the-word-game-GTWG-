from fastapi import FastAPI
from database.config import connect_to_mongo, close_mongo_connection, db
from userDetails import create_user
from database.models.users import UserCreate
from database.models.users import UserOut
from fastapi import Depends
from your_auth_module import get_current_user
from fastapi import FastAPI
from app.api import game
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

router = APIRouter()

app = FastAPI()

app.include_router(game.router, prefix="/game", tags=["game"])

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Hello FastAPI + MongoDB!"}

@app.post("/register", response_model=UserOut)
async def register(user:UserCreate):
    return await create_user(user)

from typing import List

@router.get("/history", response_model=List[GameSession])
async def get_game_history(current_user=Depends(get_current_user)):
    sessions = await db.database.game_sessions.find({"user_id": current_user.id}).to_list(100)
    return sessions

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

router = APIRouter()

@router.post("/guess")
async def make_guess(payload: GuessRequest, current_user=Depends(get_current_user)):
    game = await db.database.game_sessions.find_one({
        "_id": ObjectId(payload.game_id),
        "user_id": current_user.id
    })
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game['is_win']:
        return {"message": "You already won this game!"}

    if len(game.get('guesses', [])) >= 5:
        return {"message": "Maximum number of guesses reached."}

    guess = payload.guess.upper()
    

    guesses = game.get('guesses', [])
    guesses.append(guess)

    is_win = guess == game['word']

    await db.database.game_sessions.update_one(
        {"_id": game["_id"]},
        {"$set": {"guesses": guesses, "is_win": is_win}}
    )

    return {
        "is_win": is_win,
        "guesses": guesses,
        "message": "Correct!" if is_win else "Try again."
    }



