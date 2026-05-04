import os
import time
from google import genai
from dotenv import load_dotenv
from pypdf import PdfReader
from supabase import create_client

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def process_exam_folder(folder_path, category):
    if not os.path.exists(folder_path):
        print(f"⚠️ Folder {folder_path} not found. Skipping.")
        return

    files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    print(f"📂 Found {len(files)} files in {folder_path} ({category})")

    for filename in files:
        # Create the 'Bridge Code' (e.g., w25_23)
        # This removes the 'qp' or 'ms' parts to find the matching pair
        paper_code = filename.lower().replace("_qp_", "_").replace("_ms_", "_").replace("-qp-", "_").replace("-ms-", "_").replace(".pdf", "")
        
        file_path = os.path.join(folder_path, filename)
        reader = PdfReader(file_path)
        print(f"🚀 Ingesting: {filename} | Type: {category}")

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text or text.strip() == "": continue
            
            # 1. Generate Embedding
            result = client.models.embed_content(
                model="gemini-embedding-2",
                contents=text
            )
            
            # 2. Upload with 'Category' and 'Paper Code' metadata
            supabase.table("textbook_sections").insert({
                "content": text,
                "metadata": {
                    "source": filename,
                    "page": i + 1,
                    "category": category,      # 'question' or 'mark_scheme'
                    "paper_code": paper_code   # This links them!
                },
                "embedding": result.embeddings[0].values
            }).execute()

            # Small delay to respect Google's free tier limits
            time.sleep(1.2)

if __name__ == "__main__":
    # Path to your new subfolders
    process_exam_folder("knowledge/Past Papers", "question")
    process_exam_folder("knowledge/Mark Schemes", "mark_scheme")
    print("✅ All Exam Materials have been uploaded separately!")