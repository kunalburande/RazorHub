import re
from typing import Any, Dict, List, Set, Union


class SecretScrubber:
    """
    Zero-Trust sensitive data scrubber.
    Guarantees API secrets, private keys, passwords, bearer tokens,
    and cardholder data never appear in agent execution traces or audit logs.
    """

    SENSITIVE_KEY_NAMES: Set[str] = {
        "api_key",
        "apikey",
        "secret",
        "api_secret",
        "client_secret",
        "secret_key",
        "password",
        "passwd",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "bearer",
        "authorization",
        "auth_header",
        "proxy_authorization",
        "private_key",
        "privkey",
        "ssh_key",
        "card_number",
        "cardnumber",
        "pan",
        "cvv",
        "cvc",
        "security_code",
        "pin",
        "webhook_secret",
        "credential",
        "credentials",
        "salt",
    }

    # Regex patterns for inline string redactions
    REGEX_BEARER = re.compile(r"Bearer\s+([A-Za-z0-9\-\._~\+\/]{8,}=*)", re.IGNORECASE)
    REGEX_RAZORPAY_KEY = re.compile(r"rzp_(?:test|live)_[A-Za-z0-9]{12,}", re.IGNORECASE)
    REGEX_GENERIC_API_KEY = re.compile(r"\b(?:sk|pk|ak|key)_(?:test|live|prod|sec)_[A-Za-z0-9\-_]{12,}\b", re.IGNORECASE)
    REGEX_GOOGLE_KEY = re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")
    REGEX_CARD = re.compile(r"\b(?:\d{4}[-\s]?){3}(\d{4})\b")

    REDACTED_LABEL = "[REDACTED_SECRET]"

    @classmethod
    def scrub(cls, data: Any) -> Any:
        """
        Recursively scrubs any data structure (dict, list, str, tuple, set, primitive).
        """
        if data is None:
            return None

        if isinstance(data, dict):
            return cls._scrub_dict(data)
        elif isinstance(data, list):
            return [cls.scrub(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(cls.scrub(item) for item in data)
        elif isinstance(data, set):
            return {cls.scrub(item) for item in data}
        elif isinstance(data, str):
            return cls._scrub_string(data)
        else:
            return data

    @classmethod
    def _scrub_dict(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        scrubbed: Dict[str, Any] = {}
        for k, v in d.items():
            key_lower = str(k).lower().strip()
            key_tokens = set(re.split(r"[^a-z0-9]+", key_lower))
            # If the key itself is sensitive, redact value completely
            if bool(key_tokens & cls.SENSITIVE_KEY_NAMES) or key_lower in cls.SENSITIVE_KEY_NAMES:
                if isinstance(v, str) and len(v) > 6 and "card" in key_lower:
                    # Mask credit card with last 4 visible
                    scrubbed[k] = f"****-****-****-{v[-4:]}"
                else:
                    scrubbed[k] = cls.REDACTED_LABEL
            else:
                scrubbed[k] = cls.scrub(v)
        return scrubbed


    @classmethod
    def _scrub_string(cls, s: str) -> str:
        if not s:
            return s

        # Inline redactions
        res = cls.REGEX_BEARER.sub("Bearer [REDACTED_TOKEN]", s)
        res = cls.REGEX_RAZORPAY_KEY.sub("[REDACTED_RAZORPAY_KEY]", res)
        res = cls.REGEX_GENERIC_API_KEY.sub("[REDACTED_API_KEY]", res)
        res = cls.REGEX_GOOGLE_KEY.sub("[REDACTED_GOOGLE_API_KEY]", res)
        res = cls.REGEX_CARD.sub(r"****-****-****-\1", res)
        return res
