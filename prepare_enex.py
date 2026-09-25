from pathlib import Path
import sys
import shutil
import re
import xml.etree.ElementTree as ET


def validate_xml(path):
    try:
        ET.parse(path)
        return True, None
    except ET.ParseError as e:
        return False, e


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 prepare_enex.py <path-to-enex>")
        sys.exit(1)

    source = Path(sys.argv[1]).expanduser().resolve()

    if not source.exists():
        print(f"ERROR: File not found: {source}")
        sys.exit(1)

    if source.suffix.lower() != ".enex":
        print("ERROR: Input file must be an .enex file")
        sys.exit(1)

    output = source.with_name(f"{source.stem} - Ready for Joplin.enex")

    # Never modify the original Evernote export.
    shutil.copy2(source, output)

    print(f"Original:     {source}")
    print(f"Working copy: {output}")

    # Validate before making any changes.
    valid, error = validate_xml(output)

    if not valid:
        print(f"XML validation: FAIL — {error}")
        print("The original was preserved.")
        print("No image changes were made because the ENEX needs XML repair first.")
        sys.exit(2)

    print("Initial XML validation: PASS")

    # Apply the image sizing rule validated during the pilot migration.
    text = output.read_text(encoding="utf-8")
    count = 0
    already_sized = 0

    def resize(match):
        nonlocal count, already_sized
        tag = match.group(0)

        if 'type="image/' not in tag:
            return tag

        # Make processing idempotent.
        if 'max-width: 800px;' in tag:
            already_sized += 1
            return tag

        if 'style="' in tag:
            tag = tag.replace(
                'style="',
                'style="max-width: 800px; width: 100%; height: auto; ',
                1
            )
        else:
            tag = (
                tag[:-2]
                + ' style="max-width: 800px; width: 100%; height: auto;" />'
            )

        count += 1
        return tag

    text = re.sub(r'<en-media\b[^>]*?/>', resize, text)
    output.write_text(text, encoding="utf-8")

    print(f"Image tags updated: {count}")
    print(f"Image tags already sized: {already_sized}")

    # Validate again after transformation.
    valid, error = validate_xml(output)

    if not valid:
        print(f"Final XML validation: FAIL — {error}")
        print("Do NOT import this working copy.")
        sys.exit(3)

    print("Final XML validation: PASS")
    print()
    print("READY FOR JOPLIN")
    print(f"Import this file as HTML: {output}")


if __name__ == "__main__":
    main()
