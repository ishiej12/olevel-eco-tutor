import os
from groq import Groq
from google import genai
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

chat_memory = []

def get_tutor_response(user_input, layer="easy"):
    global chat_memory
    
    emb = genai_client.models.embed_content(model="gemini-embedding-2", contents=user_input)
    vector = emb.embeddings[0].values
    search_results = supabase.rpc("match_textbook_sections", {
        "query_embedding": vector, "match_threshold": 0.2, "match_count": 3
    }).execute()

    context_text = ""
    for doc in search_results.data:
        context_text += f"\n[{doc['metadata'].get('category')}]: {doc['content']}"

    model_id = "qwen/qwen3-32b" if layer == "easy" else "llama-3.3-70b-versatile"
    
    # --- UPDATE 1: Strict instructions in the System Message ---
    messages = [
        {
            "role": "system", 
            "content": (
                f"You are a friendly O-Level Economics tutor. Use this context if relevant: {context_text}. "
                "IMPORTANT: Provide ONLY the final answer to the student. Do not include <think> tags "
                "or internal monologue in your response."
            )
        }
    ]
    
    messages.extend(chat_memory)
    messages.append({"role": "user", "content": user_input})

    completion = groq_client.chat.completions.create(
        model=model_id,
        messages=messages
    )
    
    response_text = completion.choices[0].message.content

    chat_memory.append({"role": "user", "content": user_input})
    chat_memory.append({"role": "assistant", "content": response_text})

    if len(chat_memory) > 6:
        chat_memory = chat_memory[-6:]

    return response_text

if __name__ == "__main__":
    print("\n🎓 TUTOR WITH MEMORY: ACTIVE")
    while True:
        query = input("\nStudent: ")
        if query.lower() in ['exit', 'quit']: break
        
        # --- UPDATE 2: Cleaning the output before printing ---
        answer = get_tutor_response(query)
        
        # This split ensures that even if the AI 'thinks', the student only sees the answer
        clean_answer = answer.split("</think>")[-1].strip()
        
        print(f"\nTutor: {clean_answer}")