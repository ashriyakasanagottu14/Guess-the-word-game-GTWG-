# Guess The Word Game (Wordle Clone)

A web-based word guessing game built with Flask and JavaScript.

## Features

- 5-letter word guessing game
- Visual feedback with color coding:
  - **Green**: Letter is correct and in the right position
  - **Orange**: Letter is in the word but in the wrong position
  - **Grey**: Letter is not in the word
- Interactive keyboard with visual feedback
- 5 attempts to guess the word
- Responsive design for mobile and desktop

## Setup Instructions

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask application:**
   ```bash
   python app.py
   ```

3. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

## How to Play

1. Click "Start Game" or navigate to `/game`
2. Type a 5-letter word using your keyboard or the on-screen keyboard
3. Press Enter or click Submit to check your guess
4. Use the color feedback to make your next guess:
   - Green tiles show correct letters in correct positions
   - Orange tiles show correct letters in wrong positions
   - Grey tiles show letters not in the word
5. You have 5 attempts to guess the correct word

## Game Logic

The game uses the same logic as the original `actual.py` file:
- Random word selection from a predefined list
- Proper feedback calculation for each guess
- Win/lose conditions based on attempts

## Files Structure

- `app.py` - Flask backend with game logic
- `templates/game.html` - Game interface
- `templates/index.html` - Home page
- `actual.py` - Original game logic (reference)
- `requirements.txt` - Python dependencies

Enjoy playing Guess The Word!
