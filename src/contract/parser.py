"""
YAML contract parsing.

This module handles loading and serializing YAML contracts.
"""

from typing import Optional

import yaml

from src.contract.schema import Contract, contract_to_dict, dict_to_contract


class ContractParseError(Exception):
    """Exception raised when contract parsing fails."""

    pass


def parse_yaml_contract(yaml_content: str) -> tuple[Optional[Contract], Optional[str]]:
    """
    Parse a YAML string into a Contract object.

    Args:
        yaml_content: YAML content as string

    Returns:
        Tuple of (Contract, error_message). If successful, error_message is None.
        If failed, Contract is None.
    """
    try:
        # Parse YAML
        data = yaml.safe_load(yaml_content)

        if data is None:
            return None, "YAML file is empty."

        if not isinstance(data, dict):
            return None, "YAML root must be a mapping (dictionary)."

        # Convert to Contract object
        contract = dict_to_contract(data)

        return contract, None

    except yaml.YAMLError as e:
        return None, f"Invalid YAML syntax: {str(e)}"
    except Exception as e:
        return None, f"Error parsing contract: {str(e)}"


def parse_yaml_file(file_content: bytes) -> tuple[Optional[Contract], Optional[str]]:
    """
    Parse a YAML file (as bytes) into a Contract object.

    Args:
        file_content: YAML file content as bytes

    Returns:
        Tuple of (Contract, error_message)
    """
    try:
        yaml_content = file_content.decode("utf-8")
        return parse_yaml_contract(yaml_content)
    except UnicodeDecodeError:
        return None, "Contract file must be UTF-8 encoded."


def serialize_contract_to_yaml(contract: Contract) -> str:
    """
    Serialize a Contract object to YAML string.

    Args:
        contract: The Contract to serialize

    Returns:
        YAML string representation
    """
    # Convert to dictionary
    contract_dict = contract_to_dict(contract)

    # Serialize to YAML with nice formatting
    yaml_content = yaml.dump(
        contract_dict,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )

    return yaml_content


def serialize_contract_to_bytes(contract: Contract) -> bytes:
    """
    Serialize a Contract object to YAML bytes (for download).

    Args:
        contract: The Contract to serialize

    Returns:
        YAML content as bytes
    """
    yaml_content = serialize_contract_to_yaml(contract)
    return yaml_content.encode("utf-8")


def merge_contract_with_defaults(
    contract: Contract,
    column_names: list[str],
) -> Contract:
    """
    Merge a contract with defaults for any missing columns.

    This is used when loading a contract that may not have all columns
    from the current dataset defined.

    Args:
        contract: The loaded contract
        column_names: Column names from the current dataset

    Returns:
        Contract with missing columns added
    """
    from src.contract.schema import create_default_column_config

    # Get existing column names in contract
    existing_names = {col.name for col in contract.columns}

    # Add missing columns with defaults
    for col_name in column_names:
        if col_name not in existing_names:
            contract.columns.append(create_default_column_config(col_name))

    return contract


def extract_contract_metadata(contract: Contract) -> dict:
    """
    Extract metadata from a contract for display.

    Args:
        contract: The Contract

    Returns:
        Dictionary with metadata fields
    """
    return {
        "contract_version": contract.contract_version,
        "contract_id": contract.contract_id,
        "created_at_utc": contract.created_at_utc,
        "app_name": contract.app.name,
        "app_version": contract.app.version,
        "column_count": len(contract.columns),
        "dataset_test_count": len(contract.dataset_tests),
        "fk_check_count": len(contract.foreign_key_checks),
    }
