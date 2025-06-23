import streamlit as st
from personality_manager import load_personality, PersonalityState # Import PersonalityState for type hinting clarity
from emotion_manager import update_emotional_state, apply_decision_heuristics
import llm_handler # Renamed from main to llm_handler
import os
import logging
import openai # Import openai here for client initialization

# Set up logging for Streamlit
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 1. OpenAI API Key and Client Initialization
# ----------------------------------------------------
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("OpenAI API key not found in Streamlit Secrets. Please add it to run this app.")
    st.stop() # Stop execution if API key is missing

if "openai_client" not in st.session_state:
    st.session_state.openai_client = openai.OpenAI(api_key=api_key)

# ----------------------------------------------------
# 2. Load Personalities
# ----------------------------------------------------
identities_folder = "identities"
personalities = {}

# Check if the identities folder exists before listing
if os.path.exists(identities_folder):
    for filename in os.listdir(identities_folder):
        if filename.endswith(".json"):
            try:
                personality_name = filename.replace(".json", "")
                personalities[personality_name] = load_personality(os.path.join(identities_folder, filename))
            except Exception as e:
                logger.error(f"Error loading personality {filename}: {e}")
                st.warning(f"Could not load personality '{personality_name}'. Error: {e}")
else:
    st.error(f"Personality identities folder '{identities_folder}' not found. Please ensure it's in your repository.")
    st.stop() # Stop if identities folder is missing

if not personalities:
    st.error("No personality files found in the 'identities' folder. Please add some .json files (e.g., edgar_alan_poe.json).")
    st.stop()

logger.info(f"Loaded Personalities: {list(personalities.keys())}")


# ----------------------------------------------------
# 3. Streamlit UI Setup and Session State Management
# ----------------------------------------------------
st.set_page_config(page_title="Shaimind AI", layout="centered")

st.title("🤖 ShaiMind - AI Personalities")
st.subheader("Talk to historical figures like Edgar Allan Poe and Nikola Tesla.")

# Initialize session state variables if they don't exist
# Default to the first personality found if none selected or if previously selected is no longer available
if "selected_persona" not in st.session_state or st.session_state.selected_persona not in personalities:
    st.session_state.selected_persona = list(personalities.keys())[0]

# Dropdown for personality selection
selected_persona_from_ui = st.selectbox(
    "Choose a personality:",
    list(personalities.keys()),
    index=list(personalities.keys()).index(st.session_state.selected_persona)
)

# Load the currently selected personality (either initial or from dropdown)
# This `personality_state` object will be updated on persona change
personality_state: PersonalityState = personalities[selected_persona_from_ui]


# Logic to handle personality change: Reset conversation history
if selected_persona_from_ui != st.session_state.selected_persona:
    st.session_state.selected_persona = selected_persona_from_ui
    # Reset conversation history with the new personality's system prompt
    st.session_state.conversation_history = [{"role": "system", "content": personality_state.system_prompt}]
    st.session_state.last_response = ""
    st.rerun() # Rerun to apply the change and refresh the UI state

# Initialize conversation history for the current persona if not already set
# This ensures it's set correctly on first load or after a persona change
if "conversation_history" not in st.session_state or st.session_state.conversation_history[0].get("content") != personality_state.system_prompt:
    st.session_state.conversation_history = [{"role": "system", "content": personality_state.system_prompt}]

# ----------------------------------------------------
# 4. Display Persona Information
# ----------------------------------------------------
st.markdown(f"**Talking to:** {personality_state.name}")
st.write(f"🧠 Traits: {personality_state.traits}")
st.write(f"💭 Current Mood: {personality_state.emotional_state} (Intensity: {personality_state.emotional_intensity})")

# ----------------------------------------------------
# 5. Conversation History Display
# ----------------------------------------------------
st.subheader("📜 Conversation History")
# Display messages in reverse for chat-like interface (newest at bottom)
# Skip the very first system message as it's internal to the AI's setup
for message in reversed(st.session_state.conversation_history[1:]): # Start from 1 to skip initial system prompt
    if message["role"] == "user":
        st.chat_message("user").write(message['content'])
    elif message["role"] == "assistant":
        st.chat_message("assistant").write(message['content'])
    elif message["role"] == "system": # Optionally display internal system messages for debugging
        # st.chat_message("system").write(f"_System: {message['content']}_")
        pass # Don't display system messages

# ----------------------------------------------------
# 6. User Input and Response Generation
# ----------------------------------------------------

# Function to clean response output - keeping this as it's useful
def extract_final_response(raw_text):
    """
    Extract only the final response from AI output, removing internal thought processing
    or markdown code block fences.
    """
    cleaned_text = raw_text
    
    # Heuristic: Remove content before "USER MESSAGE:" if it slipped through
    if "USER MESSAGE:" in cleaned_text:
        cleaned_text = cleaned_text.split("USER MESSAGE:")[-1].strip()

    # Heuristic: Remove content before "Respond as [Persona Name]," if it slipped through
    if f"Respond as {personality_state.name}," in cleaned_text:
         cleaned_text = cleaned_text.split(f"Respond as {personality_state.name},")[-1].strip()
    
    # Heuristic: Look for common start markers for AI response if a specific one isn't enforced
    # (e.g., "AI response:", "RESPONSE:")
    if "RESPONSE:" in cleaned_text:
        cleaned_text = cleaned_text.split("RESPONSE:")[-1].strip()

    # Remove markdown code block fences if they were added by the AI
    if cleaned_text.startswith("```") and cleaned_text.endswith("```"):
        cleaned_text = cleaned_text.removeprefix("```").removesuffix("```").strip()
        # Also remove language specifier if present (e.g., "python\n", "json\n", "text\n")
        lines = cleaned_text.split('\n')
        if len(lines) > 1:
            first_line_stripped = lines[0].strip().lower()
            # Basic check for common markdown language specifiers
            if len(first_line_stripped) < 20 and not ' ' in first_line_stripped and first_line_stripped.isalpha(): # Simple check if it looks like a language specifier
                cleaned_text = "\n".join(lines[1:]).strip()
    
    return cleaned_text

# Text input for user messages (using st.chat_input for better mobile experience)
user_input = st.chat_input("Type your message here...", key="chat_input")

if user_input:
    # Add user message to history immediately for display
    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    with st.spinner("ShaiMind is thinking..."):
        # Process emotion & decision heuristics
        heuristic_response = apply_decision_heuristics(personality_state, user_input)
        if heuristic_response:
            response_text = heuristic_response
        else:
            # Update emotion before generating response
            update_emotional_state(personality_state, user_input)
            
            # Pass the OpenAI client to the generate_persona_response function
            response_text = llm_handler.generate_persona_response(
                st.session_state.openai_client, # Pass the client
                personality_state,
                user_input,
                st.session_state.conversation_history # Pass current history for context
            )
            response_text = extract_final_response(response_text) # Clean response after generation


        # Store AI response in history
        st.session_state.conversation_history.append({"role": "assistant", "content": response_text})
        st.session_state.last_response = response_text
    
    # Rerun the app to update the conversation history display immediately
    st.rerun()

# ----------------------------------------------------
# 7. Instructions
# ----------------------------------------------------
st.markdown("---")
st.markdown("### How to Use:")
st.markdown(
    """
    1.  **Choose a personality** from the dropdown menu.
    2.  **Type your message** in the chat box at the bottom and press Enter or the Send button.
    3.  Observe how the AI responds based on its selected personality, emotional state, and conversation history.
    4.  **Note**: The AI's internal thought process is hidden, but its effects are visible in the response.
    """
)