import streamlit as st
from google import genai
from dotenv import load_dotenv
from supabase import create_client
import os

# 1. Page Setup
st.set_page_config(page_title="O-Level Eco Tutor", page_icon="🎓")
st.title("🎓 O-Level Economics AI Tutor")
st.markdown("---")

# 2. Load Backend
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

# 3. Chat History (so the website "remembers" the conversation)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. User Input
if prompt := st.chat_input("Ask about Opportunity Cost, Demand, or Supply..."):
    # Add student message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 5. The "Brain" Logic
    with st.chat_message("assistant"):
        try:
            # A. Search Database
            emb = client.models.embed_content(model="gemini-embedding-2", contents=prompt)
            vector = emb.embeddings[0].values
            
            search = supabase.rpc("match_textbook_sections", {
                "query_embedding": vector, "match_threshold": 0.2, "match_count": 2
            }).execute()

            # B. Build Context
            context = ""
            for doc in search.data:
                context += f"\nSource: {doc['metadata'].get('source')} Content: {doc['content']}"
                if doc['metadata'].get('category') == 'question':
                    p_code = doc['metadata'].get('paper_code')
                    ms = supabase.table("textbook_sections").select("content").eq("metadata->>paper_code", p_code).eq("metadata->>category", "mark_scheme").limit(1).execute()
                    if ms.data:
                        context += f"\nMark Scheme Logic: {ms.data[0]['content']}"

            # C. Generate Response
            ai_prompt = f"You are an O-Level Eco Tutor for 8th graders. Use context: {context}\nStudent Question: {prompt}"
            response = client.models.generate_content(model="gemini-2.0-flash", contents=ai_prompt)
            
            full_response = response.text
            st.markdown(full_response)
            
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error: {e}")