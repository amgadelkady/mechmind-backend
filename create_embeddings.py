import os
import json
from openai import OpenAI
from sqlalchemy import text
from main import engine

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("pipe_stress_chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"✅ Loaded {len(chunks)} chunks from pipe_stress_chunks.json")

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipe_stress_chunks (
            id SERIAL PRIMARY KEY,
            content TEXT,
            embedding VECTOR(1536)
        );
    """))
    conn.commit()

for i, chunk in enumerate(chunks):
    print(f"🔹 Embedding chunk {i+1}/{len(chunks)}")
    emb = client.embeddings.create(
        input=chunk,
        model="text-embedding-3-small"
    ).data[0].embedding

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO pipe_stress_chunks (content, embedding) VALUES (:content, :embedding)"),
            {"content": chunk, "embedding": emb}
        )

print("✅ All embeddings for Pipe-Stress-Analysis stored successfully!")
