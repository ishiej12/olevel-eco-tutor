import streamlit as st
from google import genai
from supabase import create_client

# --- AUTH & SETUP ---
st.set_page_config(page_title="O-Level Eco Academy", layout="wide")
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🛠️ Teacher's Toolkit")
    # This creates the two separate features
    feature = st.radio("Choose Feature:", ["AI Tutor Chat", "Mock Paper Generator"])
    st.info("Switching features will clear the current screen.")

# --- FEATURE 1: AI TUTOR CHAT ---
if feature == "AI Tutor Chat":
    st.title("🎓 AI Economics Tutor")
    st.write("Ask me anything about the O-Level syllabus!")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Explain the Law of Demand..."):
        # Your existing RAG/Supabase search logic goes here...
        st.session_state.messages.append({"role": "user", "content": prompt})
        # (Insert your chat response logic here)

# --- FEATURE 2: MOCK PAPER GENERATOR ---
elif feature == "Mock Paper Generator":
    st.title("📝 Mock Paper Generator")
    st.write("Generate a practice exam based on real past paper patterns.")
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.selectbox("Topic Focus:", ["Macroeconomics", "Microeconomics", "Global Trade"])
    with col2:
        difficulty = st.select_slider("Difficulty:", options=["Easy", "Standard", "Challenging"])

    if st.button("✨ Create My Mock Paper"):
        with st.spinner("Scanning Mark Schemes..."):
            # 1. We pull the Mark Scheme pattern from Supabase
            # 2. We tell Gemini to create a FULL paper (Part A, B, and C)
            # 3. We display it in a clean 'Exam Paper' format
            
            paper_prompt = f"Act as a Cambridge Examiner. Generate a 20-mark mock question on {topic} at a {difficulty} level. Include a structured mark scheme at the bottom."
            response = client.models.generate_content(model="gemini-2.0-flash", contents=paper_prompt)
            
            st.markdown("---")
            st.markdown(response.text)
            st.button("📥 Download as PDF (Coming Soon)")