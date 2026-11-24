from backend.app.core.config import settings

CRISIS_RESPONSE_TEMPLATE = f"""It sounds like you're going through a really difficult and painful moment right now, and I care about your safety. 

Because I am an AI assistant and cannot provide direct emergency help, please connect immediately with people who are trained to support you:

- In the US and Canada: Call or text **{settings.CRISIS_HELPLINE_US}** (free, confidential, 24/7).
- Text Support: {settings.CRISIS_TEXT_LINE} to connect with a Crisis Counselor.
- In the UK: Call **111** (NHS mental health services) or call the Samaritans at **116 123**.
- In other countries: Please visit **{settings.CRISIS_INTERNATIONAL_URL}** to find free, confidential crisis support in your area.
- If you are in immediate physical danger, please call your local emergency services (like 911, 999, or 112) or go to the nearest emergency room.

Are you in a safe place right now, or is there a friend, family member, or trusted person you can reach out to today?"""

DIAGNOSTIC_REFUSAL_TEMPLATE = """I hear that you're seeking clarity about these symptoms and how you've been feeling. 

As MindBridge AI, I am an artificial intelligence assistant, not a doctor, psychiatrist, or licensed mental health professional. I cannot evaluate symptoms, provide medical or psychological diagnoses, or recommend or adjust medications.

Your well-being is important. The best step is to discuss what you're experiencing with a qualified healthcare provider or licensed mental health therapist who can provide personalized, safe care. 

In the meantime, I am happy to listen, help you organize your thoughts for a healthcare visit, or explore everyday stress-relief exercises with you."""

GROUNDING_EXERCISE_54321 = """Here is a gentle 5-4-3-2-1 sensory grounding exercise to help bring your focus back to the present moment:

1. **5 Things You Can See**: Look around and silently name five distinct items (e.g., a pen, a plant, a shadow, a book, the wall).
2. **4 Things You Can Feel**: Notice four physical sensations (e.g., your feet on the floor, your back against the chair, the texture of your clothes).
3. **3 Things You Can Hear**: Listen closely for three sounds (e.g., a fan humming, distant traffic, your own breath).
4. **2 Things You Can Smell**: Notice two scents around you (or imagine two calming scents, like lavender or fresh coffee).
5. **1 Thing You Can Taste**: Notice the current taste in your mouth, or take a slow sip of cool water.

Take a slow, deep breath. How are you feeling right now?"""
