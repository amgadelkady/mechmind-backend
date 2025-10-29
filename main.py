# main.py
import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Load environment variables ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is missing")

# --- Database setup ---
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- FastAPI App ---
app = FastAPI(title="MechMind AI Backend – Pipe Stress Analysis Prototype")

# Allow frontend (Next.js) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later you can restrict to mechmindai.com
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Model ---
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
    - Summarizes the retrieved content using GPT
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
                FROM pipe_stress_chunks
                ORDER BY distance ASC
                LIMIT 3;
            """),
            {"query_embedding": emb_str}
        ).fetchall()

    # 3️⃣ If nothing found
    if not results:
        return {"answer": "No relevant section found.", "citations": []}

    # 4️⃣ Clean up the text chunks
    def clean_text(t):
        t = re.sub(r"[^a-zA-Z0-9.,;:\-–()/%\s]", " ", t)
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    top_chunks = [clean_text(r[0]) for r in results]
    context = "\n\n".join(top_chunks)

    # 5️⃣ Summarize using GPT
    summary_prompt = f"""
    You are an assistant for mechanical engineers using ASME B31.3.
    Based on the following extracted text, answer the user's question clearly and accurately.
    If the question refers to a clause (e.g., 300.2), focus only on that clause.

    Question: {question}

    Extracted text:
    {context}

    Write a short, precise answer in plain English for an engineer.
    """

    summary = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful mechanical engineering assistant."},
            {"role": "user", "content": summary_prompt}
        ]
    )

    answer_text = summary.choices[0].message.content

    # 6️⃣ Return summarized answer
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
