# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MechMind AI Backend")

# ✅ Allow frontend (Next.js) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later to your specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
