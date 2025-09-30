# Guess The Word Game (Wordle Clone)

A web-based word guessing game built with FastAPI (Backend) and JavaScript (Frontend).

## Features

- 5-letter word guessing game
- Visual feedback with color coding:
  - **Green**: Letter is correct and in the right position
  - **Orange**: Letter is in the word but in the wrong position
  - **Grey**: Letter is not in the word
- Interactive keyboard with visual feedback
- 5 attempts to guess the word
- Responsive design for mobile and desktop
- Admin dashboard for game statistics

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB
- pip (Python package manager)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file in the backend directory):
   ```
   MONGODB_URL=mongodb://localhost:27017/gtwg
   SECRET_KEY=your-secret-key-here
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

5. Run the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`

## How to Play

1. Open the game in your browser
2. Type a 5-letter word using your keyboard or the on-screen keyboard
3. Press Enter or click Submit to check your guess
4. Use the color feedback to make your next guess:
   - Green tiles show correct letters in correct positions
   - Orange tiles show correct letters in wrong positions
   - Grey tiles show letters not in the word
5. You have 5 attempts to guess the correct word

## Admin Access

To access the admin dashboard:
- **URL**: `/admin` (after starting the frontend)
- **Default Admin Credentials**:
  - **Email**: "admin_game"
  - **Password**: "secretcode"

## Files Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routers/
│   ├── core/
│   ├── db/
│   └── main.py
frontend/
├── public/
├── src/
└── package.json
```

## Contact
Ashriya Kasanagottu - ashriyaksngtt@gmail.com  
Project Link: [https://github.com/ashriyakasanagottu14/Guess-the-word-game-GTWG-](https://github.com/ashriyakasanagottu14/Guess-the-word-game-GTWG-)

## License
MIT License
