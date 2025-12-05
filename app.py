import streamlit as st
from google import genai
from google.genai import types
import time
import os

# Set up page configuration
st.set_page_config(page_title="The Student Assistant", page_icon="🧠", layout="wide")

# Custom CSS for Layout
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; color: #4F8BF9; text-align: center; margin-bottom: 1rem; }
    .success-text { color: #28a745; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# API Key Handling
client = None
if "GEMINI_API_KEY" in st.secrets:
    # If the API Key is available in Streamlit Secrets, use it
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
else:
    # If the API Key is not available, allow the user to enter their own
    with st.sidebar:
        st.title("🔐 Authorization")
        api_key = st.text_input("Gemini API Key", type="password")
        if api_key:
            client = genai.Client(api_key=api_key)
            st.success("API Key loaded!")
        else:
            st.warning("API Key required.")

# Session State Initialization
if "uploaded_file_ref" not in st.session_state:
    st.session_state.uploaded_file_ref = None
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = None
if "workflow_status" not in st.session_state:
    st.session_state.workflow_status = "idle" # idle, processing, done
if "concept_map" not in st.session_state:
    st.session_state.concept_map = None
if "flashcards_csv" not in st.session_state:
    st.session_state.flashcards_csv = None
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []

# Gemini Caller
def generate(prompt, content_part=None, model="gemini-2.0-flash"):
    """
    Call Gemini API to generate content based on the prompt and provided file data.
    
    :param prompt: The text prompt for generating content.
    :param content_part: The file data bytes for additional context.
    :param model: The model to use for content generation.
    :return: The generated content text or an error message if an exception occurs.
    """
    if not client: return "Error: No API Key"
    try:
        contents = [prompt]
        if content_part:
            contents.append(content_part)
        
        response = client.models.generate_content(
            model=model,
            contents=contents
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"


# Main UI

st.markdown('<div class="main-header">🧠 The Student Assistant</div>', unsafe_allow_html=True)

# Section for uploading lecture content to use for agentic workflow
st.write("### 📂 Step 1: Upload Source Material")
uploaded_file = st.file_uploader(
    "Upload Lecture (Audio/Video), Slides (PDF), or Notes (Image)", 
    type=['pdf', 'txt', 'png', 'jpg', 'mp3', 'wav', 'mp4']
)

# Handle new uploaded files
if uploaded_file and uploaded_file.name != st.session_state.current_file_name:
    # Reset session state variables
    st.session_state.uploaded_file_ref = None
    st.session_state.workflow_status = "idle"
    st.session_state.concept_map = None
    st.session_state.flashcards_csv = None
    st.session_state.quiz_history = []

    # Process the new file
    with st.spinner("Uploading and processing file..."):
        try:
            file_bytes = uploaded_file.getvalue()
            st.session_state.uploaded_file_ref = types.Part.from_bytes(
                data=file_bytes,
                mime_type=uploaded_file.type
            )
            st.session_state.current_file_name = uploaded_file.name
            st.rerun()
        except Exception as e:
            st.error(f"Error processing file: {e}")

# Detect file removal and reset session state variables
if not uploaded_file and st.session_state.uploaded_file_ref:
    st.session_state.uploaded_file_ref = None
    st.session_state.current_file_name = None
    st.session_state.workflow_status = "idle"
    st.session_state.concept_map = None
    st.session_state.flashcards_csv = None
    st.session_state.quiz_history = []
    st.rerun()

# After the user has uploaded a file...
if st.session_state.uploaded_file_ref:
    
    # If workflow hasn't run yet, show the Launch Button
    if st.session_state.workflow_status == "idle":
        st.info("File uploaded successfully. Ready to analyze.")
        if st.button("Launch Student Assistant Agent", type="primary"):
            st.session_state.workflow_status = "processing"
            st.rerun()

    # If workflow is processing, run the sequential agent steps
    elif st.session_state.workflow_status == "processing":
        with st.status("Agent Orchestrating Workflow...", expanded=True) as status:
            
            # Step 1: Concept Map Synthesis
            st.write("**Analysis Agent:** Reading content and generating a Concept Map...")
            summary_prompt = """
            Analyze the attached material deeply.
            Create a 'Concept Map' Summary:
            1. **Main Topic**: What is this primarily about?
            2. **Core Concepts**: List the top 5-20 most important terms with definitions.
            3. **The 'Aha!' Moment**: The most complex idea explained simply.
            """
            st.session_state.concept_map = generate(summary_prompt, st.session_state.uploaded_file_ref)
            st.write("Concept Map generated.")
            
            # Step 2: Flashcard Generation
            st.write("**Flashcard Agent:** Extracting key terms for Flashcards...")
            flashcard_prompt = """
            Create a CSV formatted list of flashcards from this content.
            The flashcards should be useful for studying the main course content covered and not any unrelevant information.
            Format: "Front","Back"
            Generate 20 cards. No markdown code blocks and no escaping characters, just raw CSV.
            """
            st.session_state.flashcards_csv = generate(flashcard_prompt, st.session_state.uploaded_file_ref)
            st.write("Flashcards created.")
            
            # Step 3: Quiz Initialization
            st.write("**Quiz Agent:** Priming quiz engine...")
            q1_prompt = """
            You are a rigorous but fair tutor providing a practice quiz to a student. 
            Ask me the first distinct question based on the uploaded file. Do not give the answer.
            """
            first_question = generate(q1_prompt, st.session_state.uploaded_file_ref)
            st.session_state.quiz_history = [("assistant", first_question)]
            st.write("Tutor ready.")
            
            status.update(label="Workflow Complete! Dashboard Ready.", state="complete", expanded=False)
            
            st.session_state.workflow_status = "done"
            time.sleep(1)
            st.rerun()

    # Dashboard View
    elif st.session_state.workflow_status == "done":
        
        # 2-column layout for Concept Map & Flashcards
        col1, col2 = st.columns([0.6, 0.4])
        
        with col1:
            with st.container():
                st.subheader("📖 Concept Map")
                # Use expander so it doesn't dominate the page when unused
                # Start with expander collapsed to avoid auto-scrolling to the bottom
                with st.expander("View Summary Notes", expanded=False):
                    st.markdown(st.session_state.concept_map)
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            with st.container():
                st.subheader("⚡ Study Flashcards")
                st.success(f"Generated 20 Flashcards")
                st.download_button(
                    label="Download Anki/CSV Deck",
                    data=str(st.session_state.flashcards_csv),
                    file_name="flashcards.csv",
                    mime="text/csv"
                )
                st.markdown('</div>', unsafe_allow_html=True)

        # Use full page width for the Interactive Quiz
        st.markdown("---")
        st.subheader("👨‍🏫 Interactive Quiz")
        st.caption("The agent has prepared a quiz based on your specific file. Answer below.")
        
        # Chat Interface
        chat_container = st.container()
        with chat_container:
            for role, text in st.session_state.quiz_history:
                with st.chat_message(role):
                    st.markdown(text)

        # Input handling
        if user_answer := st.chat_input("Answer the quiz question..."):
            st.session_state.quiz_history.append(("user", user_answer))
            with st.chat_message("user"):
                st.markdown(user_answer)
            
            with st.chat_message("assistant"):
                with st.spinner("Grading..."):
                    # Construct context for the grading agent
                    history_text = "\n".join([f"{role}: {text}" for role, text in st.session_state.quiz_history])
                    grading_prompt = f"""
                    Context: The user is answering a quiz based on the uploaded file.
                    History: {history_text}
                    
                    Task:
                    1. Grade the user's last answer based strictly on the file.
                    2. If wrong, explain why briefly.
                    3. Ask the NEXT distinct question.
                    """
                    response = generate(grading_prompt, st.session_state.uploaded_file_ref)
                    st.markdown(response)
                    st.session_state.quiz_history.append(("assistant", response))