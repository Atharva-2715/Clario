from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import json
import shutil
import google.generativeai as genai

# ----------------------------
# Import RAG and Tracker components
# ----------------------------
from backend.rag import (
    get_embedding_model,
    ingest,
    retrieve_context
)
from backend.config import GEMINI_API_KEY
from backend.progress_tracker import get_student_profile, update_student_profile

# ----------------------------
# Gemini API setup
# ----------------------------
genai.configure(api_key=GEMINI_API_KEY)
model_generation = genai.GenerativeModel("gemini-2.5-flash")


# ----------------------------
# Initialize RAG system
# ----------------------------
DATA_DIR = Path(__file__).parent / "data"
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

# Global variables for vector store
embedding_model = get_embedding_model()
index = None
texts = []

def rebuild_vector_store():
    """Rebuild the vector store from all PDFs in data directory."""
    global index, texts
    try:
        index, texts, chunk_count = ingest(str(DATA_DIR), embedding_model)
        print(f"RAG system initialized successfully with {chunk_count} chunks from {len(list(DATA_DIR.glob('*.pdf')))} PDF(s).")
        return True
    except Exception as e:
        print(f"ERROR initializing RAG. Error: {e}")
        return False

# Initialize on startup
rebuild_vector_store()


# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="Simplified AI Tutor Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"],
)

# ----------------------------
# Pydantic Models (Simplified for direct calls)
# ----------------------------
class TutorRequest(BaseModel):
    input_text: str # Used for either question or topic
    student_id: str = "default_student" 

class AnswerResponse(BaseModel):
    natural_language_response: str
    
class QuizQuestion(BaseModel):
    q: str
    options: List[str]
    correct_answer: str

class QuizGenerateResponse(BaseModel):
    topic: str
    questions: List[QuizQuestion]

class QuizSubmission(BaseModel):
    student_id: str = "default_student"
    topic: str
    submission: List[dict] # [{"question_id": 1, "student_answer": "A", "correct_answer": "B"}, ...]

class AgentResponse(BaseModel): # Used for quiz submission and progress
    plan_executed: str
    natural_language_response: str
    
class ProgressResponse(BaseModel):
    student_id: str
    progress: dict
    agent_recommendation: str
    natural_language_summary: str

class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    chunk_count: int

# ----------------------------
# 0. Upload PDF Endpoint
# ----------------------------
@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file and rebuild the vector store."""
    if not file.filename.endswith('.pdf'):
        return UploadResponse(
            success=False,
            message="Only PDF files are supported.",
            filename=file.filename,
            chunk_count=0
        )
    
    try:
        # Save uploaded file
        file_path = DATA_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Rebuild vector store with all PDFs
        success = rebuild_vector_store()
        
        if success:
            chunk_count = len(texts)
            return UploadResponse(
                success=True,
                message=f"PDF '{file.filename}' uploaded successfully. Vector store rebuilt with {chunk_count} chunks.",
                filename=file.filename,
                chunk_count=chunk_count
            )
        else:
            return UploadResponse(
                success=False,
                message="PDF uploaded but failed to rebuild vector store.",
                filename=file.filename,
                chunk_count=0
            )
    except Exception as e:
        print(f"Upload error: {e}")
        return UploadResponse(
            success=False,
            message=f"Error uploading file: {str(e)}",
            filename=file.filename,
            chunk_count=0
        )

# ----------------------------
# 1. Answer Endpoint (Direct RAG Retrieval)
# ----------------------------
@app.post("/ask_answer", response_model=AnswerResponse)
def ask_answer(payload: TutorRequest):
    question = payload.input_text
    
    if index is None or len(texts) == 0:
        return AnswerResponse(
            natural_language_response="No PDF documents are available. Please upload PDF files first using the upload feature."
        )
    
    context = retrieve_context(question, embedding_model, index, texts)
    
    tutor_prompt = f"""
    You are a friendly and **concise** AI Tutor. Your answer must be **direct and brief**.
    Use ONLY the CONTEXT below to answer the student's QUESTION.
    Do NOT include the raw context in your final answer.

    QUESTION: {question}
    CONTEXT: {context}
    
    Provide a clear, brief, and friendly explanation as a tutor.
    """
    
    response = model_generation.generate_content(tutor_prompt)
    
    return AnswerResponse(natural_language_response=response.text)


# ----------------------------
# 2. Quiz Generation Endpoint (Direct LLM Call)
# ----------------------------
@app.post("/quiz_generate", response_model=QuizGenerateResponse)
def quiz_generate(payload: TutorRequest):
    topic = payload.input_text
    student_id = payload.student_id

    # Get student profile to determine adaptive difficulty (still useful!)
    profile = get_student_profile(student_id)
    current_strength = profile["topics"].get(topic, {}).get("strength", "unknown")
    difficulty = "medium"
    if current_strength == "strong": difficulty = "hard"
    if current_strength == "weak": difficulty = "easy"
    
    if index is None or len(texts) == 0:
        return QuizGenerateResponse(
            topic=topic,
            questions=[QuizQuestion(
                q="No PDF documents are available. Please upload PDF files first.",
                options=["Upload PDFs to continue"],
                correct_answer=""
            )]
        )
    
    context = retrieve_context(topic, embedding_model, index, texts)

    quiz_prompt = f"""
    Create EXACTLY 3 {difficulty} MCQs about the topic '{topic}' based ONLY on the context.
    The questions MUST be challenging but directly answerable from the context.
    CONTEXT: {context}
    
    Output JSON ONLY:
    {{
        "questions":[
            {{
                "q":"question text",
                "options":["A","B","C","D"],
                "correct_answer":"A"
            }}
        ]
    }}
    """
    
    # --- FINAL FIX: NO CONFIG ARGUMENT ---
    quiz_resp = model_generation.generate_content(quiz_prompt)
    # --- END FINAL FIX ---

    try:
        # Rely on manual string cleaning to extract JSON (needed when no config is passed)
        cleaned = quiz_resp.text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "")
        elif cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "")
            
        quiz_json = json.loads(cleaned)
        questions = [QuizQuestion(**q) for q in quiz_json.get("questions", [])]
        return QuizGenerateResponse(topic=topic, questions=questions)
        
    except Exception as e:
        print(f"Quiz generation failed: {e}")
        # Log the raw response text for debugging
        print(f"Raw LLM Response: {quiz_resp.text}")
        return QuizGenerateResponse(
            topic=topic,
            questions=[QuizQuestion(q=f"Quiz failed: LLM output error. Details: {e}", options=["Try another topic"], correct_answer="")]
        )


# ----------------------------
# 3. Quiz Submission Endpoint (Tracking/Feedback)
# ----------------------------
@app.post("/quiz_submit", response_model=AgentResponse)
def submit_quiz(payload: QuizSubmission):
    
    correct_count = 0
    total_count = len(payload.submission)
    
    for q_data in payload.submission:
        if str(q_data.get("student_answer")).upper() == str(q_data.get("correct_answer")).upper():
            correct_count += 1
            
    # 1. Update Progress Tracker
    update_student_profile(
        student_id=payload.student_id, 
        topic=payload.topic, 
        correct_count=correct_count, 
        total_count=total_count
    )
    
    score_percent = round((correct_count / total_count) * 100)
    
    # 2. Feedback Agent - Provide natural language response
    feedback_msg = (
        f"Great job! You scored {correct_count} out of {total_count} "
        f"({score_percent}%) on the **{payload.topic}** quiz. Your progress profile has been updated."
    )
    
    return AgentResponse(
        plan_executed=f"Quiz graded: {correct_count}/{total_count}. Profile updated.",
        natural_language_response=feedback_msg
    )


# ----------------------------
# 4. Progress Report Endpoint
# ----------------------------
@app.get("/progress/{student_id}", response_model=ProgressResponse)
def get_progress(student_id: str = "default_student"):
    profile = get_student_profile(student_id)
    
    # Use LLM to generate natural language recommendation
    recommendation_prompt = f"""
    Analyze the student's progress: {json.dumps(profile["topics"])}. Recommend the single best next topic.
    Recommendation Goal: Focus on the weakest area.
    
    Output JSON ONLY:
    {{ "recommendation": "Topic name", "summary": "A friendly, one-sentence summary." }}
    """
    
    try:
        rec_resp = model_generation.generate_content(recommendation_prompt) # No config
        
        rec_data_clean = rec_resp.text.strip()
        if rec_data_clean.startswith("```json"):
            rec_data_clean = rec_data_clean.replace("```json", "").replace("```", "")
        elif rec_data_clean.startswith("```"):
            rec_data_clean = rec_data_clean.replace("```", "")

        rec_data = json.loads(rec_data_clean)
        recommendation = rec_data.get("recommendation", "Reviewing fundamental concepts.")
        summary = rec_data.get("summary", "Keep up the good work!")
        
    except Exception:
        recommendation = "Reviewing fundamental concepts."
        summary = "Could not generate personalized recommendation."

    return ProgressResponse(
        student_id=student_id,
        progress=profile["topics"],
        agent_recommendation=recommendation,
        natural_language_summary=summary
    )