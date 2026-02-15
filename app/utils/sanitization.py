"""
Input sanitization utilities
Protects against prompt injection and other security issues
"""
import re
import logging

logger = logging.getLogger(__name__)


def sanitize_for_llm_prompt(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input before including in LLM prompt.

    Prevents prompt injection attacks by:
    1. Removing control characters
    2. Escaping special markers
    3. Limiting length
    4. Removing common injection patterns

    Args:
        text: User-provided text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text safe for LLM prompts
    """
    if not text:
        return ""

    # Convert to string if not already
    text = str(text)

    # Remove control characters (except newlines, tabs, carriage returns)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Remove common prompt injection patterns
    injection_patterns = [
        r'ignore\s+previous\s+instructions',
        r'ignore\s+all\s+previous',
        r'disregard\s+previous',
        r'forget\s+previous',
        r'new\s+instructions:',
        r'system\s+prompt:',
        r'you\s+are\s+now',
        r'\[SYSTEM\]',
        r'\[INST\]',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
    ]

    for pattern in injection_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Escape special tokens that might be interpreted as commands
    special_tokens = {
        '###': '[HASH]',
        '```': '[CODE]',
        '---': '[DASH]',
        '===': '[EQUAL]',
    }

    for token, replacement in special_tokens.items():
        text = text.replace(token, replacement)

    # Limit consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Limit consecutive spaces
    text = re.sub(r' {3,}', '  ', text)

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length] + "..."
        logger.warning(f"Text truncated from {len(text)} to {max_length} chars")

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def sanitize_project_name(name: str) -> str:
    """
    Sanitize project name for use in prompts.

    Args:
        name: Project name

    Returns:
        Sanitized project name
    """
    return sanitize_for_llm_prompt(name, max_length=200)


def sanitize_po_number(po_number: str) -> str:
    """
    Sanitize PO number for use in prompts.

    Args:
        po_number: Purchase order number

    Returns:
        Sanitized PO number
    """
    # PO numbers should be simple alphanumeric
    po_number = str(po_number)
    po_number = re.sub(r'[^A-Za-z0-9\-_]', '', po_number)
    return po_number[:50]  # Reasonable limit for PO numbers


def sanitize_reason_code(code: str) -> str:
    """
    Sanitize reason code for use in prompts.

    Args:
        code: Reason code

    Returns:
        Sanitized reason code
    """
    code = str(code)
    code = re.sub(r'[^A-Za-z0-9\-_ ]', '', code)
    return code[:100]


def validate_numeric_input(value: float, field_name: str, min_val: float = None, max_val: float = None) -> float:
    """
    Validate numeric input to prevent injection via numbers.

    Args:
        value: Numeric value to validate
        field_name: Name of field (for error messages)
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validated numeric value

    Raises:
        ValueError: If value is invalid
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")

    if min_val is not None and value < min_val:
        raise ValueError(f"{field_name} must be >= {min_val}")

    if max_val is not None and value > max_val:
        raise ValueError(f"{field_name} must be <= {max_val}")

    # Check for infinity or NaN
    if not (-1e15 < value < 1e15):
        raise ValueError(f"{field_name} value out of reasonable range")

    return value
