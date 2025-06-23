import openai
import logging

logger = logging.getLogger(__name__)

def generate_persona_response(openai_client, personality_state, user_input, conversation_history):
    """
    Generate a response based on the personality's reasoning style, emotional state, and conversation history.
    This function now takes the initialized openai_client directly.
    """
    try:
        internal_reasoning_prompt = f"""
        INTERNAL THOUGHT PROCESS (not shown to user):
        You are {personality_state.name}. Think as they would, step by step:
        - Interpret the user's message.
        - Reflect on your emotional state: {personality_state.emotional_state} (Intensity: {personality_state.emotional_intensity}).
        - Incorporate these anchors: {', '.join(personality_state.anchors)}.
        - Consider your reasoning style: {personality_state.reasoning_style}.
        - Formulate a brief, persona-appropriate response.
        - Your final output should be ONLY the persona's response, without internal thoughts or extra text.
        """
        user_prompt = f"""
        USER MESSAGE: {user_input}
        Respond as {personality_state.name}, considering your thought process and reasoning style.
        """
        
        # Ensure conversation_history is correctly formatted as list of dicts.
        # The system prompt from personality_state is already the first entry in conversation_history,
        # which is ideal for OpenAI.
        
        # Add the internal reasoning as a system message right before the user's current message.
        # This keeps the instruction separate from the chat history.
        messages = conversation_history + [
            {"role": "system", "content": internal_reasoning_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = openai_client.chat.completions.create( # UPDATED SYNTAX
            model="gpt-4o", # Using gpt-4o as it's generally better and more cost-effective for conversational tasks
            messages=messages,
            temperature=0.8,
            max_tokens=300,
            top_p=0.95,
            frequency_penalty=0.2,
            presence_penalty=0.4
        )
        return response.choices[0].message.content.strip() # UPDATED ACCESS AND STRIP
    except openai.APIStatusError as e: # UPDATED ERROR HANDLING to catch v1.x.x errors
        logger.error(f"OpenAI API error in generate_persona_response: {e}")
        if e.status_code == 401:
            return "I'm sorry, but my connection to the mind-stream is reporting an invalid access key. Please ensure my operator has set up the OpenAI API key correctly."
        elif e.status_code == 429: # Rate limit
            return "My thoughts are racing, but I'm being asked to slow down. Please give me a moment before asking again."
        elif e.status_code == 400: # Bad request, e.g., prompt too long
            return "My internal processing is encountering a complex input I cannot fully parse. Could you rephrase or simplify?"
        else:
            return f"I seem to have encountered a temporary disruption in my thought process (API Error: {e.status_code}). Please try again shortly."
    except Exception as e:
        logger.error(f"An unexpected error occurred in generate_persona_response: {e}")
        return f"I seem to have encountered an unexpected error in my thoughts: {e}"