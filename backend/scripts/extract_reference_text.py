"""
Helper script to extract plain text from SRT-formatted reference transcripts.
Removes timestamps and extracts only the transcribed text.
"""

import re
import sys
from pathlib import Path


def extract_text_from_srt(srt_path: Path) -> str:
    """
    Extract plain text from SRT-formatted transcript file.

    Args:
        srt_path: Path to SRT-formatted reference_transcript.txt

    Returns:
        Plain text with timestamps removed
    """
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove BOM if present
    content = content.lstrip('\ufeff')

    # Pattern to match SRT timestamp lines: [HH:MM:SS.mmm --> HH:MM:SS.mmm]
    timestamp_pattern = r'\[[\d:\.]+\s*-->\s*[\d:\.]+\]\s*'

    # Remove timestamps and extract text
    lines = content.split('\n')
    text_lines = []

    for line in lines:
        # Remove timestamp prefix if present
        cleaned = re.sub(timestamp_pattern, '', line)
        cleaned = cleaned.strip()

        # Skip empty lines
        if cleaned:
            text_lines.append(cleaned)

    # Join with spaces
    plain_text = ' '.join(text_lines)

    return plain_text


def main():
    """Process all reference transcripts in test-fixtures directory."""
    # test-fixtures is in project root, not in backend
    test_fixtures_dir = Path(__file__).parent.parent.parent / 'test-fixtures'

    if not test_fixtures_dir.exists():
        print(f"Error: test-fixtures directory not found: {test_fixtures_dir}")
        sys.exit(1)

    # Find all reference_transcript.txt files
    reference_files = list(test_fixtures_dir.glob('*/reference_transcript.txt'))

    if not reference_files:
        print("No reference_transcript.txt files found")
        sys.exit(1)

    print(f"Found {len(reference_files)} reference transcript files\n")

    for ref_file in reference_files:
        sample_name = ref_file.parent.name
        print(f"Processing {sample_name}...")

        # Extract plain text
        plain_text = extract_text_from_srt(ref_file)

        # Save to new file (for verification)
        output_file = ref_file.parent / 'reference_text_plain.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(plain_text)

        print(f"  ✓ Extracted {len(plain_text)} characters")
        print(f"  ✓ Saved to: {output_file.name}")
        print(f"  Preview: {plain_text[:100]}...\n")

    print(f"✓ Processed {len(reference_files)} files successfully")


if __name__ == '__main__':
    main()
