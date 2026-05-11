# classifier.py — Batch Document Classifier
# Scans a folder of text files, classifies each with Claude,
# outputs a master JSON summary sorted by urgency
# Python 3.12 | Anthropic SDK 0.40.0
# Run: python classifier.py


import os
import json
import glob  # glob is a Python module for finding files that match a pattern.
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

from error_handler import validate_setup, safe_read_file

# ── Setup ─────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

DOCUMENTS_FOLDER = BASE_DIR / "documents"
OUTPUT_FOLDER = BASE_DIR / "output"
MODEL = "claude-sonnet-4-5"

client = Anthropic()

# Allowed values — Claude must pick from these lists
CATEGORIES = ["contract", "complaint", "invoice",
              "policy", "meeting_notes", "other"]
URGENCY_LEVELS = ["urgent", "standard", "low"]

# ── Functions ───────────────────────────────────

# finds all the files in the folder


def scan_documents(folder: Path) -> list[dict]:
    """Find all .txt files in the documents folder.
    Returns a list of dicts — each has filename and filepath."""
    filepaths = glob.glob(str(folder / "*.txt")
                          # returns a list of all files matching that pattern — every .txt file in the documents folder.
                          )
    if not filepaths:
        print(f"No .txt files found in {folder}")
        return []

    documents = []
    for filepath in filepaths:
        documents.append({
            # Extracts just the filename from a full path
            "filename": os.path.basename(filepath),
            "filepath": filepath
        })

    print(f"Found {len(documents)} documents to classify")
    return documents


def read_document(filepath: str) -> str:      # opens and reads each one
    """Read the full text content of one file.
    Returns the content as a plain string."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"  Read: {os.path.basename(filepath)} ({len(content)} chars)")
    return content


def classify_document(doc_info: dict, content: str) -> dict:
    """Send one document to Claude for classification.
    Returns a dictionary with category, urgency, summary, and action."""
    filename = doc_info["filename"]
    print(f"  Classifying: {filename}")

    prompt = f"""Classify this document. Return ONLY a JSON object.
No explanation. No markdown. No code blocks. Raw JSON only.

Return exactly this structure:
{{
  "category": "one of: {', '.join(CATEGORIES)}",
  "urgency": "one of: {', '.join(URGENCY_LEVELS)}",
  "summary": "one sentence — what this document is",
  "key_action": "the single most important action needed",
  "deadline_mentioned": true or false,
  "estimated_value_kes": 0
}}

Rules:
- category must be exactly one value from the list above
- urgency is urgent only if action is needed today or tomorrow
- estimated_value_kes is 0 if no money is mentioned
- deadline_mentioned is true if any date or deadline appears

Document filename: {filename}
Document content:
{content}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.content[0].text.strip()

        # Clean markdown wrappers if Claude added them
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        # Parse JSON string into Python dictionary
        classification = json.loads(response_text)

        # Add metadata Claude did not return
        classification["filename"] = filename
        classification["classified_at"] = datetime.now().isoformat()
        classification["status"] = "success"

        return classification

    except json.JSONDecodeError as e:
        print(f"  WARNING: JSON parse failed for {filename}")
        return {"filename": filename, "status": "parse_error",
                "error": str(e)}

    except Exception as e:
        print(f"  ERROR: API call failed for {filename}")
        return {"filename": filename, "status": "api_error",
                "error": str(e)}


def save_results(results: list[dict]) -> str:
    """Save all classification results to a master JSON file.
    Sorts by urgency — urgent first. Prints a summary to terminal."""
    OUTPUT_FOLDER.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = OUTPUT_FOLDER / f"classification_{timestamp}.json"

    # Sort results: urgent=0, standard=1, low=2 (lower number = first)
    urgency_order = {"urgent": 0, "standard": 1, "low": 2}
    results_sorted = sorted(
        results,
        key=lambda r: urgency_order.get(r.get("urgency", "low"), 2)
    )

    # Build master output structure
    output = {
        "run_timestamp":   datetime.now().isoformat(),
        "total_documents": len(results),
        "successful":      sum(1 for r in results if r.get("status") == "success"),
        "errors":          sum(1 for r in results if r.get("status") != "success"),
        "urgent_count":    sum(1 for r in results if r.get("urgency") == "urgent"),
        "classifications": results_sorted
    }

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print readable terminal summary
    print(f"\n{'='*50}")
    print("CLASSIFICATION COMPLETE")
    print(f"{'='*50}")
    print(f"Total:    {output['total_documents']}")
    print(f"Success:  {output['successful']}")
    print(f"Errors:   {output['errors']}")
    print(f"URGENT:   {output['urgent_count']}\n")

    for result in results_sorted:
        if result.get("status") == "success":
            urg = result.get("urgency", "?").upper()
            cat = result.get("category", "?")
            name = result.get("filename", "?")
            act = result.get("key_action", "none")
            print(f"  [{urg}] {name} — {cat}")
            print(f"    Action: {act}")

    print(f"\nSaved: {output_file}")
    return str(output_file)


def main():
    """Main pipeline — scan folder, classify all, save results."""
    print("=== Batch Document Classifier ===")

    is_valid, errors = validate_setup()
    if not is_valid:
        print("Setup errors found:")
        for error in errors:
            print(f"  - {error}")
        return

    documents = scan_documents(DOCUMENTS_FOLDER)
    if not documents:
        print("No documents found. Add .txt files to documents/ folder.")
        return

    results = []
    for i, doc in enumerate(documents, 1):
        print(f"\nDocument {i}/{len(documents)}: {doc['filename']}")
        content = read_document(doc["filepath"])
        result = classify_document(doc, content)
        results.append(result)

    save_results(results)


if __name__ == "__main__":
    main()
