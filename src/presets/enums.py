"""
Enum preset validations.

This module defines allowed value lists for common categorical data
as specified in Section 23.8 of the acceptance criteria.
"""

from typing import Optional


# US State codes (2-letter abbreviations)
US_STATE_2_LETTER = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL",
    "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
    "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}

# US State full names
US_STATE_FULL_NAME = {
    "ALABAMA", "ALASKA", "ARIZONA", "ARKANSAS", "CALIFORNIA",
    "COLORADO", "CONNECTICUT", "DELAWARE", "DISTRICT OF COLUMBIA",
    "FLORIDA", "GEORGIA", "HAWAII", "IDAHO", "ILLINOIS", "INDIANA",
    "IOWA", "KANSAS", "KENTUCKY", "LOUISIANA", "MAINE", "MARYLAND",
    "MASSACHUSETTS", "MICHIGAN", "MINNESOTA", "MISSISSIPPI", "MISSOURI",
    "MONTANA", "NEBRASKA", "NEVADA", "NEW HAMPSHIRE", "NEW JERSEY",
    "NEW MEXICO", "NEW YORK", "NORTH CAROLINA", "NORTH DAKOTA", "OHIO",
    "OKLAHOMA", "OREGON", "PENNSYLVANIA", "RHODE ISLAND", "SOUTH CAROLINA",
    "SOUTH DAKOTA", "TENNESSEE", "TEXAS", "UTAH", "VERMONT", "VIRGINIA",
    "WASHINGTON", "WEST VIRGINIA", "WISCONSIN", "WYOMING",
}

# Combined state codes and names (for flexible matching)
US_STATE_CODE_OR_NAME = US_STATE_2_LETTER | US_STATE_FULL_NAME

# ISO 3166-1 alpha-2 country codes
COUNTRY_ISO3166_ALPHA2 = {
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
    "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS",
    "BT", "BV", "BW", "BY", "BZ",
    "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN", "CO", "CR", "CU", "CV", "CW",
    "CX", "CY", "CZ",
    "DE", "DJ", "DK", "DM", "DO", "DZ",
    "EC", "EE", "EG", "EH", "ER", "ES", "ET",
    "FI", "FJ", "FK", "FM", "FO", "FR",
    "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT",
    "GU", "GW", "GY",
    "HK", "HM", "HN", "HR", "HT", "HU",
    "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS", "IT",
    "JE", "JM", "JO", "JP",
    "KE", "KG", "KH", "KI", "KM", "KN", "KP", "KR", "KW", "KY", "KZ",
    "LA", "LB", "LC", "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY",
    "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK", "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS",
    "MT", "MU", "MV", "MW", "MX", "MY", "MZ",
    "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ",
    "OM",
    "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY",
    "QA",
    "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "SS",
    "ST", "SV", "SX", "SY", "SZ",
    "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TR", "TT", "TV", "TW", "TZ",
    "UA", "UG", "UM", "US", "UY", "UZ",
    "VA", "VC", "VE", "VG", "VI", "VN", "VU",
    "WF", "WS",
    "YE", "YT",
    "ZA", "ZM", "ZW",
}

# ANSI Packaging Units of Measure
UOM_ANSI_PACKAGING = {
    # General Packaging
    "EA", "PK", "CT", "CS", "BX", "BG", "RL", "TU", "CN", "BT", "JR",
    # Bulk / Logistics
    "PL", "SK", "DR", "TN", "LB", "KG",
    # Healthcare / Medical / Lab
    "VL", "AM", "SY", "KT", "TR", "DV",
    # Length / Material
    "FT", "IN", "YD",
}

# UOM descriptions for display
UOM_ANSI_PACKAGING_DESCRIPTIONS = {
    "EA": "Each",
    "PK": "Pack",
    "CT": "Carton",
    "CS": "Case",
    "BX": "Box",
    "BG": "Bag",
    "RL": "Roll",
    "TU": "Tube",
    "CN": "Can",
    "BT": "Bottle",
    "JR": "Jar",
    "PL": "Pallet",
    "SK": "Skid",
    "DR": "Drum",
    "TN": "Tin",
    "LB": "Pound",
    "KG": "Kilogram",
    "VL": "Vial",
    "AM": "Ampule",
    "SY": "Syringe",
    "KT": "Kit",
    "TR": "Tray",
    "DV": "Device",
    "FT": "Foot",
    "IN": "Inch",
    "YD": "Yard",
}

# ANSI X12 Full UOM list (subset of commonly used codes)
UOM_ANSI_X12 = {
    # All packaging codes plus additional common units
    *UOM_ANSI_PACKAGING,
    # Additional quantity units
    "DZ", "GR", "PR", "SET",
    # Volume units
    "GL", "QT", "PT", "OZ", "ML", "LT",
    # Weight units
    "OZ", "GR", "MG",
    # Area units
    "SF", "SY",
    # Time units
    "HR", "DA", "WK", "MO", "YR",
}

# Preset name to set mapping (internal keys)
ENUM_PRESETS = {
    "us_state_2_letter": US_STATE_2_LETTER,
    "us_state_full_name": US_STATE_FULL_NAME,
    "us_state_code_or_name": US_STATE_CODE_OR_NAME,
    "country_iso3166_alpha2": COUNTRY_ISO3166_ALPHA2,
    "uom_ansi_packaging": UOM_ANSI_PACKAGING,
    "uom_ansi_x12": UOM_ANSI_X12,
}

# Human-readable display names for UI dropdown
ENUM_PRESET_DISPLAY_NAMES = {
    "us_state_2_letter": "US States - 2 Letter (e.g., AK for Alaska)",
    "us_state_full_name": "US States - Full Name (e.g., Alaska)",
    "us_state_code_or_name": "US States - Code or Name (e.g., AK or Alaska)",
    "country_iso3166_alpha2": "Country Codes - ISO 2 Letter (e.g., US, CA, GB)",
    "uom_ansi_packaging": "Units of Measure - Packaging (e.g., EA, BX, CS)",
    "uom_ansi_x12": "Units of Measure - Extended (e.g., EA, LB, GL)",
}

# Reverse mapping from display name to internal key
ENUM_DISPLAY_TO_KEY = {v: k for k, v in ENUM_PRESET_DISPLAY_NAMES.items()}


def get_enum_preset(preset_name: str) -> Optional[set[str]]:
    """
    Get the allowed values set for an enum preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Set of allowed values or None if preset not found
    """
    return ENUM_PRESETS.get(preset_name)


def validate_with_enum_preset(
    value: str,
    preset_name: str,
    case_insensitive: bool = True,
) -> bool:
    """
    Validate a value against an enum preset.

    Args:
        value: The value to validate
        preset_name: Name of the preset
        case_insensitive: Whether to ignore case (default True)

    Returns:
        True if value is in the allowed set
    """
    preset_values = get_enum_preset(preset_name)
    if preset_values is None:
        return False

    if case_insensitive:
        return value.upper().strip() in preset_values
    else:
        return value.strip() in preset_values


def validate_with_custom_enum(
    value: str,
    allowed_values: list[str],
    case_insensitive: bool = True,
) -> bool:
    """
    Validate a value against a custom list of allowed values.

    Args:
        value: The value to validate
        allowed_values: List of allowed values
        case_insensitive: Whether to ignore case

    Returns:
        True if value is in the allowed list
    """
    if case_insensitive:
        allowed_set = {v.upper().strip() for v in allowed_values}
        return value.upper().strip() in allowed_set
    else:
        allowed_set = {v.strip() for v in allowed_values}
        return value.strip() in allowed_set


def get_all_enum_preset_names() -> list[str]:
    """
    Get all available enum preset names (internal keys).

    Returns:
        List of preset names
    """
    return list(ENUM_PRESETS.keys())


def get_all_enum_preset_display_names() -> list[str]:
    """
    Get all available enum preset display names for UI.

    Returns:
        List of human-readable preset names
    """
    return list(ENUM_PRESET_DISPLAY_NAMES.values())


def get_enum_key_from_display(display_name: str) -> str:
    """
    Convert a display name back to internal key.

    Args:
        display_name: The human-readable display name

    Returns:
        Internal preset key
    """
    return ENUM_DISPLAY_TO_KEY.get(display_name, display_name)


def get_enum_preset_info() -> list[dict]:
    """
    Get information about all enum presets for UI display.

    Returns:
        List of dicts with name, description, and count
    """
    descriptions = {
        "us_state_2_letter": "US state 2-letter codes (TX, CA, etc.)",
        "us_state_full_name": "US state full names (Texas, California, etc.)",
        "us_state_code_or_name": "US state codes or full names",
        "country_iso3166_alpha2": "ISO 3166-1 alpha-2 country codes",
        "uom_ansi_packaging": "ANSI packaging units of measure",
        "uom_ansi_x12": "ANSI X12 units of measure (extended)",
    }

    result = []
    for name, values in ENUM_PRESETS.items():
        result.append({
            "name": name,
            "description": descriptions.get(name, ""),
            "count": len(values),
            "sample": sorted(list(values))[:5],
        })
    return result


def get_enum_preset_values_display(preset_name: str) -> list[str]:
    """
    Get sorted list of values for a preset (for display).

    Args:
        preset_name: Name of the preset

    Returns:
        Sorted list of values
    """
    preset_values = get_enum_preset(preset_name)
    if preset_values:
        return sorted(list(preset_values))
    return []
