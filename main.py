# main.py

import os
from dotenv import load_dotenv
load_dotenv()  # 👈 loads values from .env file

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is missing")

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- Database setup (add below imports) ---
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="MechMind AI Backend")

# ✅ Allow frontend (Next.js) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later to your specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ASME B31.3 Clause Model ---
class Clause(Base):
    __tablename__ = "clauses"
    id = Column(Integer, primary_key=True, index=True)
    clause_id = Column(String, unique=True, index=True)
    heading = Column(String)
    summary = Column(Text)
    edition_year = Column(String)


class Question(BaseModel):
    question: str


# --- Create table on startup ---
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "Backend running successfully"}


# --- Improved /qa Endpoint ---
@app.post("/qa")
def qa_endpoint(q: Question):
    """
    Smarter question–answer logic:
    - Looks for clause ID in the question
    - If none found, scores all clauses by keyword overlap
    """

    question_text = q.question.lower()
    db = SessionLocal()
    clauses = db.query(Clause).all()
    db.close()

    # --- 1. Try exact clause ID match ---
    for clause in clauses:
        if clause.clause_id.lower() in question_text:
            return {
                "answer": f"Clause {clause.clause_id} — '{clause.heading}' "
                          f"({clause.edition_year} Edition): {clause.summary}",
                "citations": [clause.clause_id],
            }

    # --- 2. Keyword search with scoring ---
    stopwords = {
        "the", "is", "in", "at", "of", "and", "a", "to",
        "for", "on", "what", "are", "does", "define", "tell", "me", "about"
    }
    words = [w for w in question_text.split() if w not in stopwords]

    best_match = None
    best_score = 0
    for clause in clauses:
        text = (clause.heading + " " + clause.summary).lower()
        score = sum(word in text for word in words)
        if score > best_score:
            best_score = score
            best_match = clause

    # --- 3. Return best match or fallback ---
    if best_match and best_score > 0:
        return {
            "answer": f"Clause {best_match.clause_id} — '{best_match.heading}' "
                      f"({best_match.edition_year} Edition): {best_match.summary}",
            "citations": [best_match.clause_id],
        }

    return {
        "answer": "I couldn’t find a specific clause matching your question. "
                  "Try mentioning a clause number or a keyword from the heading.",
        "citations": [],
    }


# --- List all stored clauses ---
@app.get("/clauses")
def list_clauses():
    db = SessionLocal()
    results = db.query(Clause).all()
    db.close()
    return results
