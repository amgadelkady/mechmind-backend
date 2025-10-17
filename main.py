# main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MechMind AI Backend")

class Question(BaseModel):
    question: str

@app.get("/")
def home():
    return {"message": "Backend running successfully"}

@app.post("/qa")
def qa_endpoint(q: Question):
    # For now, we return a hardcoded answer
    return {
        "answer": f"Received your question: '{q.question}'. In the next step, I’ll connect to ASME B31.3 data.",
        "citations": []
    }