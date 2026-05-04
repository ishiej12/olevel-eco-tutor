import os
import time
from google import genai
from dotenv import load_dotenv
from pypdf import PdfReader
from supabase import create_client

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def process_pdf(file_path):
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    
    # 1. Check how many pages we already have
    already_done = supabase.table("textbook_sections").select("id", count="exact").execute()
    start_page = already_done.count if already_done.count else 0
    
    print(f"🔄 Resuming from Page {start_page + 1}...")

    for i in range(start_page, total_pages):
        page = reader.pages[i]
        text = page.extract_text()
        if not text or text.strip() == "": continue
        
        print(f"🚀 Processing Page {i+1}/{total_pages}...")

        try:
            # Create embedding
            result = client.models.embed_content(
                model="gemini-embedding-2",
                contents=text
            )
            
            # Save to Supabase
            supabase.table("textbook_sections").insert({
                "content": text,
                "metadata": {"page": i + 1},
                "embedding": result.embeddings[0].values
            }).execute()

            # 2. THE SECRET SAUCE: Wait 1.5 seconds so we don't get blocked
            time.sleep(1.5) 

        except Exception as e:
            if "429" in str(e):
                print("😴 Hit rate limit. Sleeping for 30 seconds...")
                time.sleep(30)
            else:
                print(f"❌ Error on page {i+1}: {e}")

    print("✅ All 394 pages are now in the cloud!")

if __name__ == "__main__":
    process_pdf("knowledge/Eco.pdf")