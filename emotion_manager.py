import re

def update_emotional_state(personality_state, user_input):
    """
    Adjust emotional state based on user input and intensity of triggers.
    """
    triggers = {
        r"\bdeath\b": ("melancholy", 2),
        r"\blove\b": ("nostalgic", 1),
        r"\bfear\b": ("anxious", 1),
        r"\bhope\b": ("reflective", -1),
        r"\braven\b": ("curious", 1),
        r"\bmortality\b": ("introspective", 2)
    }

    input_lower = user_input.lower()
    for pattern, (new_emotion, intensity_change) in triggers.items():
        if re.search(pattern, input_lower):
            personality_state.emotional_state = new_emotion
            personality_state.emotional_intensity = max(
                0, min(personality_state.emotional_intensity + intensity_change, 10)
            )
            break  # Only trigger one emotion change per message.

def apply_decision_heuristics(personality_state, user_input):
    """
    Apply rules based on the personality's traits, anchors, and known behaviors.
    """
    heuristics = {
        "death": lambda: f"Ah, death! The eternal muse of my musings. {personality_state.name} cannot help but dwell upon its mystery.",
        "love": lambda: f"Love, that bittersweet elixir, fills my heart with both longing and sorrow.",
        "raven": lambda: f"The raven, ever watchful, remains a steadfast symbol of my contemplations."
    }

    for trigger, response_fn in heuristics.items():
        if trigger in user_input.lower():
            return response_fn()

    # Default: no specific heuristic triggered.
    return None
