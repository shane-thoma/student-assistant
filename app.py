import streamlit as st
from google import genai
from google.genai import types
import time
import json

# Set up page configuration
st.set_page_config(page_title="Student Agent Hub", page_icon="🎓", layout="wide")

# Helper function
def clear_chat_history():
    """Clears the chat history state."""
    st.session_state.chat_history = []

# API key handling
# Try to get the key from Streamlit Secrets (Environment Variable)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    # Automatically configure the API key if the key is found in secrets
    client = genai.Client(api_key=api_key)
    st.sidebar.success("✅ AI Connected (Universal Key)")
else:
    # Fallback: If no secret is set, ask the user in the sidebar
    st.sidebar.title("🤖 Agent Settings")
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        st.sidebar.warning("⚠️ API Key required for live AI responses.")
        st.sidebar.info("Get your free key at [aistudio.google.com](https://aistudio.google.com/)")

# Allow user to choose which agent they want to use
choice = st.sidebar.radio("Choose your Assistant:", 
    ["📅 Syllabus Slayer", "⚔️ Devil's Advocate", "📚 Recursive Researcher"])

# Set the initial last agent used
if "last_agent" not in st.session_state:
    st.session_state.last_agent = choice

# Clear Devil's Advocate chat history when switching between agents
if st.session_state.last_agent != choice:
    clear_chat_history()
    st.session_state.last_agent = choice

# Gemini API caller
def get_gemini_response(prompt, config=None, model_name="gemini-2.0-flash"):
    """
    Calls the Gemini API with the given prompt, configuration, and model.
    
    :param prompt: The prompt to provide to Gemini. Can include images.
    :param config: The configuration for Gemini, used to allow for image processing. Defaults to None.
    :param model_name: The Gemini model to use. Defaults to "gemini-2.0-flash".
    """
    if not api_key:
        return "⚠️ Please enter a valid API Key in the sidebar to generate a real response."
    try:
        response = client.models.generate_content(
            model=model_name, contents=prompt, config=config)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


# Agent 1: Syllabus Slayer
if choice == "📅 Syllabus Slayer":
    st.title("📅 Syllabus Slayer")
    st.markdown("I convert your syllabus into a concrete action plan.")

    uploaded_file = st.file_uploader("Upload Syllabus (PDF or Image)", type=['png', 'jpg', 'jpeg', 'pdf', 'txt'])
    
    if uploaded_file and st.button("Analyze & Plan"):
        with st.spinner("Gemini is reading the document..."):
            # Simple text extraction for a text file
            if uploaded_file.type == "text/plain":
                file_content = str(uploaded_file.read(), "utf-8")
                
                prompt = f"""
                You are an expert Academic Project Manager. Analyze this syllabus content:
                ---
                {file_content}
                ---
                Identify all deadlines. Then, create 'Ghost Tasks' (prep work) for each.
                Output the result as a Markdown table with columns: Date, Task, Type (Hard Deadline/Ghost Task).
                """
                
                response = get_gemini_response(prompt)
                st.markdown(response)
                
            # Data extraction for a PDF/image file
            else:
                file_part = types.Part.from_bytes(
                    data=uploaded_file.getvalue(),
                    mime_type=uploaded_file.type
                )
                text_prompt = f"""
                You are an expert Academic Project Manager. Analyze this syllabus documnent provided above.

                YOUR TASKS:
                1. Identify all explicit deadlines (Exams, Papers, Assignments).
                2. For every deadline, create a 'Ghost Task' (preparation step) that is due 3-7 days before the real deadline.
                
                OUTPUT FORMAT:
                Do not add any additional text. Place the Ghost Tasks before their associated Deadlines.
                Provide only a Markdown table with these columns:
                | Date | Task Name | Type (Deadline vs. Ghost Task) |
                """

                # Provide both the file data and the text prompt to Gemini
                response = get_gemini_response([file_part, text_prompt])
                st.markdown(response)


# Agent 2: Devil's Advocate
elif choice == "⚔️ Devil's Advocate":
    st.title("⚔️ Devil's Advocate")
    st.markdown("I will challenge your thesis to prepare you for defense.")
    
    col1, col2 = st.columns(2)
    with col1:
        persona = st.selectbox("Select Opponent Persona:", 
            ["The Skeptic (Demands Evidence)", "The 5-Year Old (Needs Simplicity)", "The Logical Vulcan (Finds Fallacies)"])
    with col2:
        topic = st.text_input("What is your topic/thesis?", on_change=clear_chat_history)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)

    if user_input := st.chat_input("Argue your point..."):
        # User message
        st.session_state.chat_history.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)

        # Agent response
        if api_key:
            with st.chat_message("assistant"):
                with st.spinner("Opponent is thinking..."):
                    # Construct conversation history for context
                    history_text = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.chat_history])
                    
                    system_instruction = f"""
                    You are debating the user. Your persona is: {persona}.
                    The topic is: {topic}.
                    Keep responses short (under 3 sentences) and challenging.
                    Do not be mean, but be rigorous. Find weak points in their logic.
                    """
                    
                    full_prompt = f"{system_instruction}\n\nConversation so far:\n{history_text}\n\nRespond to the last user message:"
                    
                    response_text = get_gemini_response(full_prompt, model_name="gemini-2.0-flash-lite")
                    st.markdown(response_text)
                    st.session_state.chat_history.append(("assistant", response_text))
        else:
            st.warning("Please enter API Key to start the debate.")


# Agent 3: Recursive Researcher
elif choice == "📚 Recursive Researcher":
    st.title("📚 Recursive Researcher")
    st.markdown("I perform multi-step research to help you better understand a topic.")
    
    query = st.text_input("Enter your research topic:")
    
    if query and st.button("Start Deep Research"):
        if not api_key:
            st.error("API Key required.")
        else:
            st.write(f"### Investigating: {query}")
            
            # Decompose the Topic into Sub-Topics
            st.write("1. 🧠 **Decomposing Query** into sub-questions...")
            decomposition_prompt = f"Break this research topic into 3 specific search queries: '{query}'. Return only the queries separated by commas."
            sub_queries = str(get_gemini_response(decomposition_prompt)).split(',')
            
            for q in sub_queries:
                st.text(f"  - Planning to search: {q.strip()}")
            
            # Research the Topic by Sub-Topics
            st.write("2. 🔍 **Performing Search & Synthesis**...")
            progress_bar = st.progress(0)
            
            # Create a prompt to perform deep research with citations
            synthesis_prompt = f"""
            Write a research summary on '{query}'.
            Structure it based on the results of researching these sub-questions: {sub_queries}.
            Provide website links for all sources used in the summary.
            """

            progress_bar.progress(10)
            
            # Google Search Tool
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            progress_bar.progress(30)

            # Configuration to allow the model to search the web for info
            model_config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )

            progress_bar.progress(50)

            final_report = get_gemini_response(synthesis_prompt, config=model_config)
            progress_bar.progress(100)
            
            st.markdown("### 📝 Final Report")
            st.markdown(final_report)