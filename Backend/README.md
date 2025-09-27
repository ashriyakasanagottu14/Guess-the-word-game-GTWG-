# Word Guess Backend (FastAPI + MongoDB)

## Overview
Backend for a 5-letter word guessing game with Admin and Player roles.

## Features
- User registration/login (JWT)
- Game play with constraints (max 3 games/day, 5 guesses/game)
- Stores words and guesses
- Admin reports: daily and per-user

## Run (Docker)
```bash
docker compose up --build
```
App: http://localhost:8000
Docs: http://localhost:8000/docs

## Env
Copy `.env.example` to `.env` and adjust as needed.

## Local (no Docker)
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
