"""
Convert plain text reference transcripts to JSON format for QualityValidator.
Creates segment format expected by validate_quality.py.
"""

import json
import sys
from pathlib import Path


def create_json_reference(plain_text: str, sample_id: str) -> dict:
    """
    Create JSON reference file from plain text.

    For CER/WER calculation, we just need the text content.
    Create a single segment with all the text (segmentation doesn't matter for accuracy).

    Args:
        plain_text: Plain text reference transcript
        sample_id: Sample identifier

    Returns:
        Dict with segments array
    """
    # Create single segment with all text
    # Start/end times don't matter for CER/WER (only text is compared)
    segment = {
        "start": 0.0,
        "end": 1.0,  # Placeholder
        "text": plain_text.strip()
    }

    return {
        "sample_id": sample_id,
        "segments": [segment]
    }


def main():
    """Process all plain text references and create JSON files."""
    test_fixtures_dir = Path(__file__).parent.parent.parent / 'test-fixtures'

    if not test_fixtures_dir.exists():
        print(f"Error: test-fixtures directory not found: {test_fixtures_dir}")
        sys.exit(1)

    # Find all reference_text_plain.txt files
    plain_files = list(test_fixtures_dir.glob('*/reference_text_plain.txt'))

    if not plain_files:
        print("No reference_text_plain.txt files found")
        sys.exit(1)

    print(f"Found {len(plain_files)} plain text reference files\n")

    for plain_file in plain_files:
        sample_name = plain_file.parent.name
        print(f"Processing {sample_name}...")

        # Read plain text
        with open(plain_file, 'r', encoding='utf-8') as f:
            plain_text = f.read()

        # Create JSON reference
        json_data = create_json_reference(plain_text, sample_name)

        # Save to JSON file
        json_file = plain_file.parent / 'reference.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"  ✓ Created {json_file.name}")
        print(f"  ✓ Text length: {len(plain_text)} characters\n")

    print(f"✓ Created {len(plain_files)} JSON reference files")


if __name__ == '__main__':
    main()
