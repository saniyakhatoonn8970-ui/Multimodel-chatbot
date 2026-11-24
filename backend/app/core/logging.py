import logging
import sys
import re

LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"

# Patterns to mask sensitive tokens/keys in log records if accidentally included
SENSITIVE_PATTERNS = [
    (re.compile(r'(api_key|apikey|token|password|secret|bearer\s+[A-Za-z0-9_\-\.]+)', re.IGNORECASE), r'\1=***REDACTED***')
]


class SanitizedFormatter(logging.Formatter):
    """Custom logging formatter to sanitize sensitive tokens before writing to log streams."""
    def format(self, record: logging.LogRecord) -> str:
        orig = super().format(record)
        sanitized = orig
        for pattern, repl in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(repl, sanitized)
        return sanitized


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("mindbridge")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(SanitizedFormatter(LOG_FORMAT))
        logger.addHandler(handler)
        
    return logger


logger = setup_logging()
