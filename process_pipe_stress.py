import json
import re
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1️⃣ Read the new PDF
pdf_path = "Pipe-Stress-Analysis.pdf"
reader = PdfReader(pdf_path)

all_text = ""
for i, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""
    # Basic cleanup: remove extra spaces, line breaks, watermark-like patterns
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"Page \d+", "", text)
    all_text += text + "\n"

print(f"✅ Extracted {len(reader.pages)} pages from {pdf_path}")

# 2️⃣ Split text into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,  # adjust for your PDF
    chunk_overlap=100
)
chunks = splitter.split_text(all_text)

# 3️⃣ Save to JSON for embedding
with open("pipe_stress_chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"✅ Created {len(chunks)} chunks and saved to pipe_stress_chunks.json")
