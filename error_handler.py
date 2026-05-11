# error_handler.py — Challenge 2 error handling

import os
from pathlib import Path

def validate_setup() -> tuple[bool, list[str]]:
    """Check all prerequisites before running.
    Returns (is_valid, list_of_error_messages)."""
    errors = []

    if not os.getenv("ANTHROPIC_API_KEY"):
        errors.append("ANTHROPIC_API_KEY missing — check your .env file.")

    if not Path("documents").exists():
        errors.append("documents/ folder not found — create it and add .txt files.")
    elif not list(Path("documents").glob("*.txt")):
        errors.append("No .txt files found in documents/ — add at least one.")

    return len(errors) == 0, errors


def safe_read_file(filepath: str) -> tuple[bool, str]:
    """Safely read a file — handles encoding errors.
    Returns (success, content_or_error_message)."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return True, f.read()
    except UnicodeDecodeError:
        return False, "Encoding error — file is not valid UTF-8 text"
    except PermissionError:
        return False, "Permission denied — cannot read this file"
    except Exception as e:
        return False, f"Read error: {str(e)}"