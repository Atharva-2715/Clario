# Agentic AI Tutor

An AI-powered tutoring system that uses RAG (Retrieval Augmented Generation) to answer questions, generate adaptive quizzes, and track student progress.

## Prerequisites

- Python 3.11 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Setup Instructions

### 1. Set up Environment Variables

Create a `.env` file in the project root directory:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies

**Option A: Using existing virtual environment (if on macOS/Linux)**
```bash
# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option B: Create a new virtual environment (recommended)**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Verify Sample PDF Exists

The sample PDF should already exist at `backend/data/sample_notes.pdf`. If it doesn't, you can generate it:

```bash
python backend/create_sample_pdf.py
```

## Running the Application

### Step 1: Start the Backend Server

From the project root directory:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
# or
# venv\Scripts\activate  # Windows

# Start the FastAPI server
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at `http://127.0.0.1:8000`

You should see output like:
```
RAG system initialized successfully with X chunks.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Open the Frontend

Simply open `frontend/index.html` in your web browser. You can:

- **Double-click** the file to open it in your default browser
- Or use a local server:
  ```bash
  # Using Python's built-in server
  cd frontend
  python3 -m http.server 8080
  # Then open http://localhost:8080 in your browser
  ```

### Step 3: Use the Application

1. Enter a Student ID (or use the default)
2. **Ask Tutor**: Enter a question (e.g., "What is AI?") and click "Ask Tutor"
3. **Generate Quiz**: Enter a topic (e.g., "Probability") and click "Generate Quiz"
4. **Progress Report**: Click "Progress Report" to see your learning progress

## API Endpoints

- `POST /ask_answer` - Get answers to questions using RAG
- `POST /quiz_generate` - Generate adaptive quizzes
- `POST /quiz_submit` - Submit quiz answers and get feedback
- `GET /progress/{student_id}` - Get student progress report

## Troubleshooting

- **"GEMINI_API_KEY not found"**: Make sure you have a `.env` file with your API key
- **"RAG system initialization failed"**: Check that `backend/data/sample_notes.pdf` exists
- **CORS errors**: The backend is configured to allow all origins, but make sure it's running on port 8000
- **Module not found errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`

## Project Structure

```
agentic-ai-tutor/
├── backend/
│   ├── app.py              # FastAPI main application
│   ├── config.py           # Configuration (API keys)
│   ├── rag.py              # RAG system implementation
│   ├── progress_tracker.py # Student progress tracking
│   ├── create_sample_pdf.py # PDF generation utility
│   └── data/
│       └── sample_notes.pdf # Sample study material
├── frontend/
│   ├── index.html          # Main UI
│   ├── script.js           # Frontend logic
│   └── style.css           # Styling
└── requirements.txt        # Python dependencies
```

