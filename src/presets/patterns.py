"""
Regex pattern presets for pattern validation.

This module defines regex patterns for common data formats as specified
in Section 23.1 of the acceptance criteria.
"""

import re
from typing import Optional


# Pattern preset definitions
# Each preset is a tuple of (pattern, description, example)
REGEX_PRESETS = {
    # Common formats
    "email": (
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "Email address",
        "user@example.com",
    ),
    "phone_us": (
        r"^(\+1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}$",
        "US phone number (with optional country code and formatting)",
        "(555) 123-4567 or +1-555-123-4567",
    ),
    "zip_us_5": (
        r"^\d{5}$",
        "US 5-digit ZIP code",
        "12345",
    ),
    "zip_us_9": (
        r"^\d{5}(-\d{4})?$",
        "US ZIP+4 code (5 digits or 5+4 format)",
        "12345-6789",
    ),
    "url": (
        r"^https?://[^\s/$.?#].[^\s]*$",
        "URL (HTTP or HTTPS)",
        "https://example.com/path",
    ),
    "uuid": (
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        "Universally Unique Identifier (UUID)",
        "550e8400-e29b-41d4-a716-446655440000",
    ),
    "ipv4": (
        r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
        "IPv4 address",
        "192.168.1.1",
    ),
    "ipv6": (
        r"^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|"
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}"
        r"(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}"
        r"(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        r":((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+|"
        r"::(ffff(:0{1,4})?:)?((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}"
        r"(25[0-5]|(2[0-4]|1?[0-9])?[0-9])|([0-9a-fA-F]{1,4}:){1,4}:"
        r"((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}(25[0-5]|(2[0-4]|1?[0-9])?[0-9]))$",
        "IPv6 address",
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
    ),
    # Character type patterns
    "numeric_only": (
        r"^\d+$",
        "Numbers only (0-9)",
        "12345",
    ),
    "alphanumeric_only": (
        r"^[a-zA-Z0-9]+$",
        "Letters and numbers only",
        "ABC123",
    ),
    "letters_only": (
        r"^[a-zA-Z]+$",
        "Letters only (A-Z, a-z)",
        "Hello",
    ),
}

# Human-readable display names for UI dropdown (in order)
# Format: internal_key -> display_name
PATTERN_DISPLAY_NAMES = {
    "email": "Email Address (e.g., user@example.com)",
    "phone_us": "US Phone Number (e.g., 555-123-4567)",
    "zip_us_5": "US ZIP Code - 5 Digit (e.g., 12345)",
    "zip_us_9": "US ZIP Code - 9 Digit (e.g., 12345-6789)",
    "url": "Web URL (e.g., https://example.com)",
    "uuid": "UUID / GUID (e.g., 550e8400-e29b-...)",
    "ipv4": "IP Address v4 (e.g., 192.168.1.1)",
    "ipv6": "IP Address v6",
    "numeric_only": "Numeric Only - digits 0-9 (e.g., 12345)",
    "alphanumeric_only": "Alphanumeric Only - letters & numbers (e.g., ABC123)",
    "letters_only": "Letters Only - A-Z (e.g., Hello)",
    # Builder patterns - displayed at end
    "starts_with": "Starts With... (specify prefix)",
    "ends_with": "Ends With... (specify suffix)",
    "contains": "Contains... (specify text)",
    "custom": "Custom Pattern (advanced)",
}

# Reverse mapping
PATTERN_DISPLAY_TO_KEY = {v: k for k, v in PATTERN_DISPLAY_NAMES.items()}

# Which patterns need additional input
PATTERNS_REQUIRING_INPUT = {"starts_with", "ends_with", "contains", "custom"}


# Compiled patterns cache
_compiled_patterns: dict[str, re.Pattern] = {}


def get_preset_pattern(preset_name: str) -> Optional[str]:
    """
    Get the regex pattern for a preset.

    Args:
        preset_name: Name of the preset (e.g., "uuid", "email")

    Returns:
        Regex pattern string or None if preset not found
    """
    preset = REGEX_PRESETS.get(preset_name)
    if preset:
        return preset[0]
    return None


def get_preset_description(preset_name: str) -> Optional[str]:
    """
    Get the description for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Description string or None if preset not found
    """
    preset = REGEX_PRESETS.get(preset_name)
    if preset:
        return preset[1]
    return None


def get_preset_example(preset_name: str) -> Optional[str]:
    """
    Get an example for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Example string or None if preset not found
    """
    preset = REGEX_PRESETS.get(preset_name)
    if preset:
        return preset[2]
    return None


def get_compiled_pattern(preset_name: str) -> Optional[re.Pattern]:
    """
    Get a compiled regex pattern for a preset (cached).

    Args:
        preset_name: Name of the preset

    Returns:
        Compiled Pattern object or None if preset not found
    """
    if preset_name in _compiled_patterns:
        return _compiled_patterns[preset_name]

    pattern_str = get_preset_pattern(preset_name)
    if pattern_str:
        compiled = re.compile(pattern_str)
        _compiled_patterns[preset_name] = compiled
        return compiled

    return None


def validate_with_preset(value: str, preset_name: str) -> bool:
    """
    Validate a value against a preset pattern.

    Args:
        value: The string value to validate
        preset_name: Name of the preset pattern

    Returns:
        True if value matches the pattern, False otherwise
    """
    pattern = get_compiled_pattern(preset_name)
    if pattern is None:
        return False

    return bool(pattern.match(value))


def validate_with_custom_pattern(value: str, pattern_str: str) -> bool:
    """
    Validate a value against a custom regex pattern.

    Args:
        value: The string value to validate
        pattern_str: The regex pattern string

    Returns:
        True if value matches the pattern, False otherwise
    """
    try:
        pattern = re.compile(pattern_str)
        return bool(pattern.match(value))
    except re.error:
        return False


def get_all_preset_names() -> list[str]:
    """
    Get all available preset names (internal keys).

    Returns:
        List of preset names
    """
    return list(REGEX_PRESETS.keys())


def get_all_pattern_display_names() -> list[str]:
    """
    Get all pattern display names for UI dropdown.

    Returns:
        List of human-readable pattern names in order
    """
    return list(PATTERN_DISPLAY_NAMES.values())


def get_pattern_key_from_display(display_name: str) -> str:
    """
    Convert a display name back to internal key.

    Args:
        display_name: The human-readable display name

    Returns:
        Internal pattern key
    """
    return PATTERN_DISPLAY_TO_KEY.get(display_name, display_name)


def pattern_requires_input(pattern_key: str) -> bool:
    """
    Check if a pattern requires additional user input.

    Args:
        pattern_key: The internal pattern key

    Returns:
        True if pattern needs additional input
    """
    return pattern_key in PATTERNS_REQUIRING_INPUT


def get_preset_info() -> list[dict]:
    """
    Get information about all presets for UI display.

    Returns:
        List of dicts with name, description, example, and pattern
    """
    result = []
    for name, (pattern, description, example) in REGEX_PRESETS.items():
        result.append({
            "name": name,
            "description": description,
            "example": example,
            "pattern": pattern,
        })
    return result


def build_pattern_from_builder(
    allowed_characters: Optional[list[str]] = None,
    length_exact: Optional[int] = None,
    length_min: Optional[int] = None,
    length_max: Optional[int] = None,
    starts_with: Optional[str] = None,
    ends_with: Optional[str] = None,
) -> str:
    """
    Build a regex pattern from builder tier parameters.

    Args:
        allowed_characters: List of character classes ("digits", "letters", "alphanumeric")
        length_exact: Exact length requirement
        length_min: Minimum length
        length_max: Maximum length
        starts_with: Required prefix
        ends_with: Required suffix

    Returns:
        Constructed regex pattern string
    """
    # Build character class
    char_class_parts = []
    if allowed_characters:
        for char_type in allowed_characters:
            if char_type == "digits":
                char_class_parts.append("0-9")
            elif char_type == "letters":
                char_class_parts.append("a-zA-Z")
            elif char_type == "alphanumeric":
                char_class_parts.append("a-zA-Z0-9")
            elif char_type == "uppercase":
                char_class_parts.append("A-Z")
            elif char_type == "lowercase":
                char_class_parts.append("a-z")

    if char_class_parts:
        char_class = f"[{''.join(char_class_parts)}]"
    else:
        char_class = "."  # Any character

    # Build length quantifier
    if length_exact is not None:
        quantifier = f"{{{length_exact}}}"
    elif length_min is not None and length_max is not None:
        quantifier = f"{{{length_min},{length_max}}}"
    elif length_min is not None:
        quantifier = f"{{{length_min},}}"
    elif length_max is not None:
        quantifier = f"{{0,{length_max}}}"
    else:
        quantifier = "*"

    # Build main pattern
    main_pattern = f"{char_class}{quantifier}"

    # Add starts_with and ends_with
    pattern = "^"
    if starts_with:
        pattern += re.escape(starts_with)
    pattern += main_pattern
    if ends_with:
        pattern += re.escape(ends_with)
    pattern += "$"

    return pattern


def compile_custom_pattern(pattern_str: str) -> tuple[Optional[re.Pattern], Optional[str]]:
    """
    Compile a custom regex pattern with error handling.

    Args:
        pattern_str: The regex pattern string

    Returns:
        Tuple of (compiled_pattern, error_message)
        If successful, error_message is None
    """
    try:
        compiled = re.compile(pattern_str)
        return compiled, None
    except re.error as e:
        return None, f"Invalid regex pattern: {str(e)}"
