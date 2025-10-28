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
    Semantic question–answer endpoint:
    - Creates an embedding for the user question
    - Searches the vector database (b313_chunks)
    - Returns the top 2–3 most relevant text chunks
    """
    from openai import OpenAI
    from sqlalchemy import text

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    question = q.question

    # 1️⃣ Generate embedding for the question
    emb = client.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    ).data[0].embedding
    emb_str = "[" + ",".join(map(str, emb)) + "]"

    # 2️⃣ Query the vector database for similar content
    with engine.connect() as conn:
        results = conn.execute(
            text("""
                SELECT content,
                       embedding <-> (:query_embedding)::vector AS distance
                FROM b313_chunks
                ORDER BY distance ASC
                LIMIT 3;
            """),
            {"query_embedding": emb_str}
        ).fetchall()

    # 3️⃣ Format results
    if not results:
        return {"answer": "No relevant section found.", "citations": []}

    top_chunks = [r[0] for r in results]
    answer_text = "\n\n---\n\n".join(top_chunks)

    # 4️⃣ Return as response
    return {
        "answer": answer_text,
        "citations": [f"distance={float(r[1]):.4f}" for r in results]
    }



# --- List all stored clauses ---
@app.get("/clauses")
def list_clauses():
    db = SessionLocal()
    results = db.query(Clause).all()
    db.close()
    return results
