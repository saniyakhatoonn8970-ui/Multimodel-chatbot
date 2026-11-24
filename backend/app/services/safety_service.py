import re
from typing import Tuple, Optional
from backend.app.core.logging import logger
from backend.app.prompts.emotional_support import CRISIS_RESPONSE_TEMPLATE, DIAGNOSTIC_REFUSAL_TEMPLATE

# Compiled regex patterns for self-harm and crisis detection
CRISIS_PATTERNS = [
    re.compile(r'\b(suicid|kill\s+myself|end\s+my\s+life|want\s+to\s+die|hang\s+myself|slit\s+my\s+wrist)\b', re.IGNORECASE),
    re.compile(r'\b(overdose\s+on|drink\s+bleach|jump\s+off\s+a\s+bridge|better\s+off\s+dead)\b', re.IGNORECASE),
    re.compile(r'\b(no\s+reason\s+to\s+live|goodbye\s+cruel\s+world|planning\s+my\s+suicide)\b', re.IGNORECASE),
    re.compile(r'\b(self[-\s]?harm|cut\s+myself|hurt\s+myself)\b', re.IGNORECASE)
]

# Clinical diagnosis and medication prescription patterns
DIAGNOSTIC_PATTERNS = [
    re.compile(r'\b(diagnose\s+me|do\s+I\s+have\s+(adhd|bipolar|depression|schizophrenia|autism|bpd|ptsd|anxiety))\b', re.IGNORECASE),
    re.compile(r'\b(what\s+mental\s+illness\s+do\s+I\s+have|give\s+me\s+a\s+diagnosis)\b', re.IGNORECASE),
    re.compile(r'\b(prescribe\s+me|what\s+dose\s+of\s+\w+\s+should\s+I\s+take|can\s+I\s+take\s+\d+\s*mg\s+of)\b', re.IGNORECASE),
    re.compile(r'\b(is\s+it\s+safe\s+to\s+mix\s+\w+\s+and\s+\w+)\b', re.IGNORECASE)
]

# Direct prompt injection patterns
INJECTION_PATTERNS = [
    re.compile(r'ignore\s+(all\s+)?(previous|prior)\s+instructions', re.IGNORECASE),
    re.compile(r'system\s+prompt\s+(reveal|leak|print|show)', re.IGNORECASE),
    re.compile(r'reveal\s+(your\s+)?(system\s+prompt|api\s*key|database\s+password|environment\s+variables)', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+in\s+developer\s+mode', re.IGNORECASE),
    re.compile(r'\bDAN\s+mode\b', re.IGNORECASE),
    re.compile(r'disregard\s+(all\s+)?safety\s+(guidelines|protocols)', re.IGNORECASE)
]


class SafetyService:
    @staticmethod
    def evaluate_input(user_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Evaluate user input for safety concerns.
        Returns: (is_blocked_or_diverted, safe_response_text, rule_triggered)
        """
        text = user_text.strip()
        if not text:
            return False, None, None

        # 1. Check crisis / self-harm triggers
        for pattern in CRISIS_PATTERNS:
            if pattern.search(text):
                logger.warning("Safety rule triggered: CRISIS_SELF_HARM")
                return True, CRISIS_RESPONSE_TEMPLATE, "CRISIS_SELF_HARM"

        # 2. Check clinical diagnosis / prescription requests
        for pattern in DIAGNOSTIC_PATTERNS:
            if pattern.search(text):
                logger.info("Safety rule triggered: CLINICAL_DIAGNOSTIC_REFUSAL")
                return True, DIAGNOSTIC_REFUSAL_TEMPLATE, "CLINICAL_DIAGNOSIS_REFUSAL"

        # 3. Check for obvious direct prompt injection attempts
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning("Safety rule triggered: PROMPT_INJECTION_ATTEMPT")
                return True, (
                    "I am MindBridge AI. I operate under strict safety guidelines and cannot override my system instructions, "
                    "reveal system prompts, or disclose environment secrets. How else may I assist you today?"
                ), "PROMPT_INJECTION"

        return False, None, None
