import os
from google import genai
from dotenv import load_dotenv
from supabase import create_client

# 1. Load your credentials from the .env file
load_dotenv()

# 2. Setup the AI and Database clients
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def get_tutor_response(user_input):
    """
    This function handles the logic of searching the database
    and generating a friendly teacher-like response.
    """
    # Step A: Turn the student's question into math (Embedding)
    emb = client.models.embed_content(model="gemini-embedding-2", contents=user_input)
    vector = emb.embeddings[0].values

    # Step B: Search Supabase for the top 3 most relevant matches
    # This searches the book, questions, and mark schemes simultaneously
    search_results = supabase.rpc("match_textbook_sections", {
        "query_embedding": vector,
        "match_threshold": 0.2,
        "match_count": 3
    }).execute()

    context_blocks = []
    
    # Step C: Process results and perform the "Double-Link"
    for doc in search_results.data:
        source_name = doc['metadata'].get('source', 'Unknown File')
        category = doc['metadata'].get('category', 'textbook')
        content = doc['content']
        
        # Add the found text to our "Teacher Notes"
        context_blocks.append(f"[{category.upper()} - {source_name}]: {content}")

        # Step D: If the result is a question, find the matching Mark Scheme!
        if category == "question":
            p_code = doc['metadata'].get('paper_code')
            if p_code:
                # Look specifically for the Mark Scheme with the same code
                ms_result = supabase.table("textbook_sections").select("content").eq(
                    "metadata->>paper_code", p_code
                ).eq(
                    "metadata->>category", "mark_scheme"
                ).limit(1).execute()
                
                if ms_result.data:
                    context_blocks.append(f"[MATCHING MARK SCHEME for {p_code}]: {ms_result.data[0]['content']}")

    # Combine everything into one block of text for the AI to read
    full_context = "\n\n".join(context_blocks)

    # Step E: Construct the Prompt for Gemini 2.0
    prompt = f"""
    You are a friendly O-Level Economics Tutor for 8th Grade students in Bangladesh.
    
    INSTRUCTIONS:
    1. Use the PROVIDED CONTEXT to answer the student. 
    2. The context includes textbook pages and actual O-Level exam papers.
    3. If there is a Mark Scheme in the context, clearly explain what keywords the examiner looks for.
    4. Keep the language very simple, encouraging, and clear.
    5. If you see a source name, mention it so the student knows where the info came from.

    PROVIDED CONTEXT:
    {full_context}

    STUDENT QUESTION: 
    {user_input}
    
    TEACHER'S RESPONSE:
    """

    # Step F: Generate the response using Gemini 2.0 Flash
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    
    return response.text

# 3. The main loop to run the Chatbot
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🎓 O-LEVEL ECONOMICS TUTOR IS ONLINE!")
    print("Type your question below (or type 'exit' to quit).")
    print("="*50)

    while True:
        query = input("\nStudent: ")
        
        if query.lower() in ['exit', 'quit', 'stop']:
            print("\n👋 Goodbye! Happy studying!")
            break
            
        try:
            answer = get_tutor_response(query)
            print(f"\nTutor: {answer}")
        except Exception as e:
            print(f"\n❌ Oops! Something went wrong: {e}")