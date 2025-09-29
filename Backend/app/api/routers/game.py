from datetime import datetime, timezone
import random
from fastapi import APIRouter, HTTPException, Depends, status, Request
from bson import ObjectId

from app.core.auth import get_current_user, require_role
from app.core.security import get_token_from_header
from app.db.mongodb import get_database
from app.schemas.game import StartGameResponse, GuessRequest, GameOut, GuessEntry
from app.utils.validators import validate_guess
from app.core.roles import PLAYER

router = APIRouter(prefix="/game", tags=["game"])

@router.post("/logout")
async def logout(request: Request, user=Depends(get_current_user)):
    db = await get_database()
    token = get_token_from_header(request)
    
    # Add token to blacklist
    await db.blacklisted_tokens.insert_one({
        "token": token,
        "user_id": user["_id"],
        "blacklisted_at": datetime.now(timezone.utc)
    })
    
    # Update user's last logout time
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_logout_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Successfully logged out"}


MAX_GUESSES = 5
MAX_GAMES_PER_DAY = 3


def day_range(dt: datetime):
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


@router.post("/start", response_model=StartGameResponse)
async def start_game(user=Depends(require_role(PLAYER))):
    db = await get_database()
    now = datetime.now(timezone.utc)
    day_start, day_end = day_range(now)

    # Check and initialize remaining games
    user_doc = await db.users.find_one({"_id": user["_id"]})
    remaining_games = user_doc.get("remaining_games")
    
    # Reset remaining games at the start of each day
    last_game = await db.games.find_one(
        {"user_id": user["_id"]},
        sort=[("started_at", -1)]
    )
    
    if not last_game or last_game["started_at"].date() < now.date():
        remaining_games = MAX_GAMES_PER_DAY
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"remaining_games": remaining_games}}
        )
    
    if remaining_games is None:
        remaining_games = MAX_GAMES_PER_DAY
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"remaining_games": remaining_games}}
        )
    
    if remaining_games <= 0:
        raise HTTPException(status_code=429, detail="No games remaining for today")
    
    print(f"User {user['username']} has {remaining_games} games remaining today")

    # pick random active word
    words = [w async for w in db.words.aggregate([{"$match": {"active": True}}, {"$sample": {"size": 1}}])]
    if not words:
        raise HTTPException(status_code=503, detail="No words available")
    word = words[0]

    game_doc = {
        "user_id": user["_id"],
        "word_id": word["_id"],
        "started_at": now,
        "completed_at": None,
        "status": "IN_PROGRESS",
        "guesses": [],
    }
    res = await db.games.insert_one(game_doc)
    return StartGameResponse(game_id=str(res.inserted_id), started_at=now, status="IN_PROGRESS", guesses_made=0)


@router.post("/guess", response_model=GameOut)
async def submit_guess(request: Request, payload: GuessRequest, user=Depends(require_role(PLAYER))):
    db = await get_database()
    validate_guess(payload.guess)

    game = await db.games.find_one({"_id": ObjectId(payload.game_id), "user_id": user["_id"]})
    print(game)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="Game already completed")

    # Use secret from payload
    secret = payload.target_word.upper()

    # Evaluate guess (simple algorithm with frequency handling)
    guess = payload.guess.upper()  # <-- Fix: Normalize guess to uppercase
    secret_chars = list(secret)
    res = ["X"] * 5

    # First pass for greens
    used = [False] * 5
    for i, c in enumerate(guess):
        if c == secret_chars[i]:
            res[i] = "G"
            used[i] = True

    # Count remaining letters
    from collections import Counter
    remaining_secret = Counter(secret_chars[i] for i in range(5) if not used[i])

    # Second pass for oranges
    for i, c in enumerate(guess):
        if res[i] == "G":
            continue
        if remaining_secret.get(c, 0) > 0:
            res[i] = "O"
            remaining_secret[c] -= 1

    guesses = game.get("guesses", [])
    if len(guesses) >= MAX_GUESSES:
        raise HTTPException(status_code=400, detail="No guesses remaining")

    guess_entry = {"guess": guess, "result": res, "guessed_at": datetime.now(timezone.utc)}
    guesses.append(guess_entry)

    update = {"$set": {"guesses": guesses}}
    status = game["status"]
    completed_at = None
    game_completed = False

    # Check if current guess is correct
    if guess == secret:
        # Won the game!
        status = "WON"
        completed_at = datetime.now(timezone.utc)
        game_completed = True
        # Create a new document for completed game
        completed_game = {
            "user_id": user["_id"],
            "word_id": game["word_id"],
            "word": secret,
            "status": status,
            "completed_at": completed_at,
            "started_at": game["started_at"],
            "guesses": guesses,
            "won": True
        }
        await db.completed_games.insert_one(completed_game)
        # Delete the in-progress game
        await db.games.delete_one({"_id": game["_id"]})
        
    elif len(guesses) == MAX_GUESSES:
        # Used all 5 guesses and didn't win
        status = "LOST"
        completed_at = datetime.now(timezone.utc)
        game_completed = True
        # Create a new document for completed game
        completed_game = {
            "user_id": user["_id"],
            "word_id": game["word_id"],
            "word": secret,
            "status": status,
            "completed_at": completed_at,
            "started_at": game["started_at"],
            "guesses": guesses,
            "won": False
        }
        await db.completed_games.insert_one(completed_game)
        # Delete the in-progress game
        await db.games.delete_one({"_id": game["_id"]})
    else:
        # Update in-progress game
        await db.games.update_one({"_id": game["_id"]}, update)
    
    # If game is completed, update user's remaining games
    if completed_at:
        # Get user's remaining games
        user_doc = await db.users.find_one({"_id": user["_id"]})
        remaining_games = user_doc.get("remaining_games", MAX_GAMES_PER_DAY)
        
        # Decrement remaining games
        remaining_games = max(0, remaining_games - 1)
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"remaining_games": remaining_games}}
        )
        
        # If no games remain, blacklist the token
        if remaining_games == 0:
            token = get_token_from_header(request)
            await db.blacklisted_tokens.insert_one({
                "token": token,
                "user_id": user["_id"],
                "blacklisted_at": datetime.now(timezone.utc),
                "reason": "daily_limit_reached"
            })

    await db.games.update_one({"_id": game["_id"]}, update)

    remaining = MAX_GUESSES - len(guesses)
    return GameOut(
        id=str(game["_id"]),
        user_id=str(game["user_id"]),
        status=status,
        started_at=game["started_at"],
        completed_at=completed_at or game.get("completed_at"),
        guesses=[GuessEntry(**g) for g in guesses],
        remaining_guesses=remaining,
        won=(status == "WON"),
    )


