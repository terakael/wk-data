#!/usr/bin/env python3
"""
Create a WaniKani Anki deck with HTML collapsible mnemonics sections.
"""

import json
import csv
from typing import Dict, List, Any, Optional


def clean_text(text: str) -> str:
    """Clean text for CSV by removing HTML tags and unescaping HTML entities."""
    if not text:
        return ""

    # Remove HTML tags but keep the content
    import re

    text = re.sub(r"<[^>]+>", "", text)

    # Unescape HTML entities
    import html

    text = html.unescape(text)

    # Replace newlines with spaces for cleaner CSV
    text = text.replace("\n", " ").replace("\r", " ")

    # Remove extra whitespace
    text = " ".join(text.split())

    return text


def process_radicals(
    data: Dict[str, Any], target_level: Optional[int] = None
) -> List[Dict[str, str]]:
    """Process radicals data into card format."""
    cards = []

    for level, items in data.items():
        level_num = int(level)
        if target_level and level_num != target_level:
            continue

        for item in items:
            # Handle image radicals
            if item["character"].startswith("http"):
                character_display = f'<img src="{item["character"]}" style="filter: brightness(0) invert(1) sepia(1) hue-rotate(200deg) saturate(2);">'
            else:
                character_display = item["character"]

            front = f'<div style="font-size: 10px; color: #666;">Radical - Level {level_num}</div><div style="font-size: 24px; color: #1E90FF; text-align: center; margin: 15px 0;">{character_display}</div>'

            # Create collapsible mnemonic section
            mnemonic = item.get("mnemonic", "")
            if mnemonic:
                # Add CSS styling to properly render HTML in mnemonic
                styled_mnemonic = f"""<div style="background-color: #2d2d2d; font-size: 8px; color: #fff; line-height: 1.4;">
                    <style>
                        .radical-highlight {{ color: #87CEEB; font-weight: bold; }}
                        .kanji-highlight {{ color: #FFB347; font-weight: bold; }}
                        .reading-highlight {{ color: #98FB98; font-weight: bold; }}
                        .vocabulary-highlight {{ color: #FFB6C1; font-weight: bold; }}
                    </style>
                    {mnemonic}
                </div>"""

                back = f'<span style="font-size: 16px;">{item["meaning"]}</span><br><br><details><summary style="cursor: pointer; color: #666; font-size: 12px;">📖 Show Mnemonic</summary>{styled_mnemonic}</details>'
            else:
                back = f'<span style="font-size: 16px;">{item["meaning"]}</span>'

            cards.append(
                {
                    "level": level_num,
                    "type": "radical",
                    "front": front,
                    "back": back,
                    "tags": f"wanikani radical level-{level_num}",
                }
            )

    return cards


def process_kanji_meanings(
    data: Dict[str, Any], target_level: Optional[int] = None
) -> List[Dict[str, str]]:
    """Process kanji data into meaning cards."""
    cards = []

    for level, items in data.items():
        level_num = int(level)
        if target_level and level_num != target_level:
            continue

        for item in items:
            front = f'<div style="font-size: 10px; color: #666;">Kanji - Level {level_num}</div><div style="font-size: 24px; color: #FF8C00; text-align: center; margin: 15px 0;">{item["character"]}</div><div style="font-size: 10px; color: #666;">Meaning</div>'
            back = f'<span style="font-size: 16px;">{item["meaning"]}</span>'

            cards.append(
                {
                    "level": level_num,
                    "type": "kanji-meaning",
                    "front": front,
                    "back": back,
                    "tags": f"wanikani kanji-meaning level-{level_num}",
                }
            )

    return cards


def process_kanji_readings(
    data: Dict[str, Any], target_level: Optional[int] = None
) -> List[Dict[str, str]]:
    """Process kanji data into reading cards."""
    cards = []

    for level, items in data.items():
        level_num = int(level)
        if target_level and level_num != target_level:
            continue

        for item in items:
            front = f'<div style="font-size: 10px; color: #666;">Kanji - Level {level_num}</div><div style="font-size: 24px; color: #FF8C00; text-align: center; margin: 15px 0;">{item["character"]}</div><div style="font-size: 10px; color: #666;">Reading</div>'

            # Combine all readings
            readings = []
            if item.get("readings", {}).get("on'yomi"):
                readings.extend(item["readings"]["on'yomi"])
            if item.get("readings", {}).get("kun'yomi"):
                readings.extend(item["readings"]["kun'yomi"])

            # Get reading mnemonic
            reading_mnemonic = item.get("mnemonics", {}).get("reading", "")
            if reading_mnemonic:
                # Add CSS styling to properly render HTML in mnemonic
                styled_mnemonic = f"""<div style="background-color: #2d2d2d; font-size: 8px; color: #fff; line-height: 1.4;">
                    <style>
                        .radical-highlight {{ color: #87CEEB; font-weight: bold; }}
                        .kanji-highlight {{ color: #FFB347; font-weight: bold; }}
                        .reading-highlight {{ color: #98FB98; font-weight: bold; }}
                        .vocabulary-highlight {{ color: #FFB6C1; font-weight: bold; }}
                    </style>
                    {reading_mnemonic}
                </div>"""

                back = f'<span style="font-size: 16px;">{", ".join(readings)}</span><br><br><details><summary style="cursor: pointer; color: #666; font-size: 12px;">📖 Show Reading Mnemonic</summary>{styled_mnemonic}</details>'
            else:
                back = f'<span style="font-size: 16px;">{", ".join(readings)}</span>'

            cards.append(
                {
                    "level": level_num,
                    "type": "kanji-reading",
                    "front": front,
                    "back": back,
                    "tags": f"wanikani kanji-reading level-{level_num}",
                }
            )

    return cards


def process_vocab_meanings(
    data: Dict[str, Any], target_level: Optional[int] = None
) -> List[Dict[str, str]]:
    """Process vocabulary data into meaning cards."""
    cards = []

    for level, items in data.items():
        level_num = int(level)
        if target_level and level_num != target_level:
            continue

        for item in items:
            front = f'<div style="font-size: 10px; color: #666;">Vocab - Level {level_num}</div><div style="font-size: 24px; color: #228B22; text-align: center; margin: 15px 0;">{item["character"]}</div><div style="font-size: 10px; color: #666;">Meaning</div>'

            # Combine primary meaning with alternatives
            meanings = [item["primary_meaning"]]
            if item.get("alternative_meanings"):
                meanings.extend(item["alternative_meanings"])

            back = f'<span style="font-size: 16px;">{", ".join(meanings)}</span>'

            cards.append(
                {
                    "level": level_num,
                    "type": "vocab-meaning",
                    "front": front,
                    "back": back,
                    "tags": f"wanikani vocab-meaning level-{level_num}",
                }
            )

    return cards


def process_vocab_readings(
    data: Dict[str, Any], target_level: Optional[int] = None
) -> List[Dict[str, str]]:
    """Process vocabulary data into reading cards."""
    cards = []

    for level, items in data.items():
        level_num = int(level)
        if target_level and level_num != target_level:
            continue

        for item in items:
            front = f'<div style="font-size: 10px; color: #666;">Vocab - Level {level_num}</div><div style="font-size: 24px; color: #228B22; text-align: center; margin: 15px 0;">{item["character"]}</div><div style="font-size: 10px; color: #666;">Reading</div>'
            back = f'<span style="font-size: 16px;">{item["reading"]}</span>'

            cards.append(
                {
                    "level": level_num,
                    "type": "vocab-reading",
                    "front": front,
                    "back": back,
                    "tags": f"wanikani vocab-reading level-{level_num}",
                }
            )

    return cards


def main():
    """Main function to convert JSON files to Anki CSV with collapsible mnemonics."""
    target_level = None  # All levels for complete deck

    # Load JSON files
    with open("wanikani_radicals_complete.json", "r", encoding="utf-8") as f:
        radicals_data = json.load(f)

    with open("wanikani_kanji_complete.json", "r", encoding="utf-8") as f:
        kanji_data = json.load(f)

    with open("wanikani_vocabulary_complete.json", "r", encoding="utf-8") as f:
        vocabulary_data = json.load(f)

    # Process all data
    all_cards = []

    # Add radicals
    radical_cards = process_radicals(radicals_data, target_level)
    all_cards.extend(radical_cards)

    # Add kanji meaning cards
    kanji_meaning_cards = process_kanji_meanings(kanji_data, target_level)
    all_cards.extend(kanji_meaning_cards)

    # Add kanji reading cards
    kanji_reading_cards = process_kanji_readings(kanji_data, target_level)
    all_cards.extend(kanji_reading_cards)

    # Add vocab meaning cards
    vocab_meaning_cards = process_vocab_meanings(vocabulary_data, target_level)
    all_cards.extend(vocab_meaning_cards)

    # Add vocab reading cards
    vocab_reading_cards = process_vocab_readings(vocabulary_data, target_level)
    all_cards.extend(vocab_reading_cards)

    # Sort by level, then by type order
    type_order = {
        "radical": 0,
        "kanji-meaning": 1,
        "kanji-reading": 2,
        "vocab-meaning": 3,
        "vocab-reading": 4,
    }
    all_cards.sort(key=lambda x: (x["level"], type_order[x["type"]]))

    # Write to CSV
    filename = "wanikani_complete_collapsible_deck.csv"
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Front", "Back", "Tags"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")

        # Write header for Anki compatibility
        writer.writerow({"Front": "#separator:Semicolon", "Back": "", "Tags": ""})
        writer.writerow({"Front": "#html:true", "Back": "", "Tags": ""})

        # Write cards
        for card in all_cards:
            writer.writerow(
                {"Front": card["front"], "Back": card["back"], "Tags": card["tags"]}
            )

    print(f"Created complete collapsible deck with {len(all_cards)} cards!")
    print(f"Output file: {filename}")
    print(f"Radicals: {len(radical_cards)}")
    print(f"Kanji meanings: {len(kanji_meaning_cards)}")
    print(f"Kanji readings: {len(kanji_reading_cards)}")
    print(f"Vocab meanings: {len(vocab_meaning_cards)}")
    print(f"Vocab readings: {len(vocab_reading_cards)}")
    print("\nFeatures:")
    print("- HTML <details>/<summary> for collapsible sections")
    print("- Click '📖 Show Mnemonic' to expand")
    print("- Dark background (#2d2d2d) for dark mode")
    print("- Small text (8px) for mnemonics")
    print("- Full HTML content preserved with CSS styling")
    print(
        "- Color-coded highlights: radicals(blue), kanji(orange), readings(green), vocab(pink)"
    )
    print("- Level and type information on each card")
    print("\nImport instructions:")
    print("1. Anki → File → Import...")
    print("2. Select 'wanikani_complete_collapsible_deck.csv'")
    print("3. ✅ Check 'Allow HTML in fields'")


if __name__ == "__main__":
    main()
