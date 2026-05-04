import os
from google import genai
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Setup Clients
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def search_textbook(query):
    print(f"🔍 Searching for: '{query}'...")
    
    # 1. Turn your question into a vector
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=query
    )
    query_vector = response.embeddings[0].values

    # 2. Ask Supabase to find the top 3 most relevant pages
    matched_docs = supabase.rpc("match_textbook_sections", {
        "query_embedding": query_vector,
        "match_threshold": 0.3, # Adjust this if results are too loose
        "match_count": 3
    }).execute()

    # 3. Print the results
    if not matched_docs.data:
        print("❌ No matches found. Check your SQL function!")
    else:
        for i, doc in enumerate(matched_docs.data):
            print(f"\n--- Result {i+1} (Page {doc['metadata']['page']}) ---")
            print(f"Content snippet: {doc['content'][:200]}...")

if __name__ == "__main__":
    # Test it with a real Economics question!
    search_textbook("What is the definition of opportunity cost?")