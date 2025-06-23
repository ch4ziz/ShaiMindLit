import json
import os

class PersonalityState:
    def __init__(
        self,
        name: str,
        traits: str,
        emotional_state: str,
        emotional_intensity: int,
        reasoning_style: str,
        anchors: list,
        system_prompt: str,
        preferred_topics: list = None,
        avoided_topics: list = None,
        writing_style: dict = None,
        behavioral_guidelines: list = None,
        historical_context: dict = None
    ):
        self.name = name
        self.traits = traits
        self.emotional_state = emotional_state
        self.emotional_intensity = emotional_intensity
        self.reasoning_style = reasoning_style
        self.anchors = anchors
        self.system_prompt = system_prompt
        self.preferred_topics = preferred_topics or []
        self.avoided_topics = avoided_topics or []
        self.writing_style = writing_style or {}
        self.behavioral_guidelines = behavioral_guidelines or []
        self.historical_context = historical_context or {}

def load_personality(personality_path: str) -> PersonalityState:
    """Load a personality from a JSON file."""
    if not os.path.exists(personality_path):
        raise FileNotFoundError(f"Personality file not found: {personality_path}")

    with open(personality_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return PersonalityState(
        name=data["name"],
        traits=data["traits"],
        emotional_state=data["emotional_state"],
        emotional_intensity=data["emotional_intensity"],
        reasoning_style=data["reasoning_style"],
        anchors=data["anchors"],
        system_prompt=data["system_prompt"],
        preferred_topics=data.get("preferred_topics", []),
        avoided_topics=data.get("avoided_topics", []),
        writing_style=data.get("writing_style", {}),
        behavioral_guidelines=data.get("behavioral_guidelines", []),
        historical_context=data.get("historical_context", {})
    )
