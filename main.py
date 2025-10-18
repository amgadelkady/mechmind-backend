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
import os

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL environment variable is missing")

DATABASE_URL = os.getenv("DATABASE_URL")
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

@app.post("/qa")
def qa_endpoint(q: Question):
    """
    Simple question–answer logic:
    - Looks for clause ID mentioned in the question (e.g. '300.2')
    - Or searches for words that appear in the heading/summary
    """

    question_text = q.question.lower()
    db = SessionLocal()

    # --- Try to find clause by ID mentioned in the question ---
    found_clause = None
    for clause in db.query(Clause).all():
        if clause.clause_id.lower() in question_text:
            found_clause = clause
            break

    # --- If not found, try keyword search in heading/summary ---
    if not found_clause:
        for clause in db.query(Clause).all():
            if any(word in clause.summary.lower() or word in clause.heading.lower()
                   for word in question_text.split()):
                found_clause = clause
                break

    db.close()

    # --- Build response ---
    if found_clause:
        answer_text = (
            f"Clause {found_clause.clause_id} — '{found_clause.heading}' "
            f"({found_clause.edition_year} Edition): {found_clause.summary}"
        )
        citations = [found_clause.clause_id]
    else:
        answer_text = (
            "I couldn’t find a specific clause matching your question. "
            "Try mentioning a clause number or a keyword from the heading."
        )
        citations = []

    return {"answer": answer_text, "citations": citations}


# --- List all stored clauses ---
@app.get("/clauses")
def list_clauses():
    db = SessionLocal()
    results = db.query(Clause).all()
    db.close()
    return results
