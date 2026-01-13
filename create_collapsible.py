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
                # Get mnemonic image if available
                mnemonic_image = item.get("mnemonic_image", "")
                mnemonic_image_html = ""
                if mnemonic_image:
                    mnemonic_image_html = f'<img src="{mnemonic_image}" style="max-width: 100%; margin: 10px 0; display: block;">'
                
                # Add CSS styling to properly render HTML in mnemonic
                styled_mnemonic = f"""<div style="background-color: #2d2d2d; font-size: 8px; color: #fff; line-height: 1.4;">
                    <style>
                        .radical-highlight {{ color: #87CEEB; font-weight: bold; }}
                        .kanji-highlight {{ color: #FFB347; font-weight: bold; }}
                        .reading-highlight {{ color: #98FB98; font-weight: bold; }}
                        .vocabulary-highlight {{ color: #FFB6C1; font-weight: bold; }}
                    </style>
                    {mnemonic_image_html}
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
            
            # Get meaning mnemonic
            meaning_mnemonic = item.get("mnemonics", {}).get("meaning", "")
            if meaning_mnemonic:
                # Add CSS styling to properly render HTML in mnemonic
                styled_mnemonic = f"""<div style="background-color: #2d2d2d; font-size: 8px; color: #fff; line-height: 1.4;">
                    <style>
                        .radical-highlight {{ color: #87CEEB; font-weight: bold; }}
                        .kanji-highlight {{ color: #FFB347; font-weight: bold; }}
                        .reading-highlight {{ color: #98FB98; font-weight: bold; }}
                        .vocabulary-highlight {{ color: #FFB6C1; font-weight: bold; }}
                    </style>
                    {meaning_mnemonic}
                </div>"""

                back = f'<span style="font-size: 16px;">{item["meaning"]}</span><br><br><details><summary style="cursor: pointer; color: #666; font-size: 12px;">📖 Show Meaning Mnemonic</summary>{styled_mnemonic}</details>'
            else:
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

            # Group readings by category
            onyomi_readings = item.get("readings", {}).get("on'yomi", [])
            kunyomi_readings = item.get("readings", {}).get("kun'yomi", [])
            nanori_readings = item.get("readings", {}).get("nanori", [])

            # Build reading display with category-specific tag styling
            reading_lines = []
            
            if onyomi_readings:
                tags = "".join([f'<span style="display: inline-block; padding: 3px 8px; margin: 2px; background: rgba(74, 144, 226, 0.2); color: #2C5AA0; border-radius: 3px; font-size: 14px;">{reading}</span>' for reading in onyomi_readings])
                reading_lines.append(f'<div style="margin-bottom: 6px;"><span style="font-size: 12px; font-weight: bold; color: #4A90E2;">On\'yomi:</span> {tags}</div>')
            
            if kunyomi_readings:
                tags = "".join([f'<span style="display: inline-block; padding: 3px 8px; margin: 2px; background: rgba(80, 200, 120, 0.2); color: #2E7D46; border-radius: 3px; font-size: 14px;">{reading}</span>' for reading in kunyomi_readings])
                reading_lines.append(f'<div style="margin-bottom: 6px;"><span style="font-size: 12px; font-weight: bold; color: #50C878;">Kun\'yomi:</span> {tags}</div>')
            
            if nanori_readings:
                tags = "".join([f'<span style="display: inline-block; padding: 3px 8px; margin: 2px; background: rgba(155, 89, 182, 0.2); color: #6A1B9A; border-radius: 3px; font-size: 14px;">{reading}</span>' for reading in nanori_readings])
                reading_lines.append(f'<div style="margin-bottom: 6px;"><span style="font-size: 12px; font-weight: bold; color: #9B59B6;">Nanori:</span> {tags}</div>')
            
            reading_display = "".join(reading_lines)

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

                back = f'<div style="font-size: 16px;">{reading_display}</div><br><details><summary style="cursor: pointer; color: #666; font-size: 12px;">📖 Show Reading Mnemonic</summary>{styled_mnemonic}</details>'
            else:
                back = f'<div style="font-size: 16px;">{reading_display}</div>'

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

            # Get meaning explanation
            meaning_explanation = item.get("meaning_explanation", "")
            if meaning_explanation:
                # Add CSS styling to properly render HTML in mnemonic
                styled_mnemonic = f"""<div style="background-color: #2d2d2d; font-size: 8px; color: #fff; line-height: 1.4;">
                    <style>
                        .radical-highlight {{ color: #87CEEB; font-weight: bold; }}
                        .kanji-highlight {{ color: #FFB347; font-weight: bold; }}
                        .reading-highlight {{ color: #98FB98; font-weight: bold; }}
                        .vocabulary-highlight {{ color: #FFB6C1; font-weight: bold; }}
                    </style>
                    {meaning_explanation}
                </div>"""

                back = f'<span style="font-size: 16px;">{", ".join(meanings)}</span><br><br><details><summary style="cursor: pointer; color: #666; font-size: 12px;">📖 Show Meaning Explanation</summary>{styled_mnemonic}</details>'
            else:
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
            
            # Get reading explanation
            reading_explanation = item.get("reading_explanation", "")
            if reading_explanation:
                # Add CSS styling to properly render HTML in mnemonic
                styled_mnemonic = f"""<div style="background-color: #2d2d2d; font-size: 8px; color: #fff; line-height: 1.4;">
                    <style>
                        .radical-highlight {{ color: #87CEEB; font-weight: bold; }}
                        .kanji-highlight {{ color: #FFB347; font-weight: bold; }}
                        .reading-highlight {{ color: #98FB98; font-weight: bold; }}
                        .vocabulary-highlight {{ color: #FFB6C1; font-weight: bold; }}
                    </style>
                    {reading_explanation}
                </div>"""

                back = f'<span style="font-size: 16px;">{item["reading"]}</span><br><br><details><summary style="cursor: pointer; color: #666; font-size: 12px;">📖 Show Reading Explanation</summary>{styled_mnemonic}</details>'
            else:
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

    # Process all data - by level, interleaving meanings and readings for each item
    all_cards = []
    
    # Track card counts for summary
    radical_count = 0
    kanji_meaning_count = 0
    kanji_reading_count = 0
    vocab_meaning_count = 0
    vocab_reading_count = 0

    # Get all unique levels (assuming all data structures have the same levels)
    all_levels = sorted(set(
        list(radicals_data.keys()) + 
        list(kanji_data.keys()) + 
        list(vocabulary_data.keys())
    ), key=int)

    # Process each level in order
    for level in all_levels:
        level_num = int(level)
        
        # Add radicals for this level
        radical_cards = process_radicals(radicals_data, level_num)
        all_cards.extend(radical_cards)
        radical_count += len(radical_cards)
        
        # Add kanji for this level - interleave meaning and reading
        kanji_meaning_cards = process_kanji_meanings(kanji_data, level_num)
        kanji_reading_cards = process_kanji_readings(kanji_data, level_num)
        
        for meaning_card, reading_card in zip(kanji_meaning_cards, kanji_reading_cards):
            all_cards.append(meaning_card)
            all_cards.append(reading_card)
            kanji_meaning_count += 1
            kanji_reading_count += 1
        
        # Add vocabulary for this level - interleave meaning and reading
        vocab_meaning_cards = process_vocab_meanings(vocabulary_data, level_num)
        vocab_reading_cards = process_vocab_readings(vocabulary_data, level_num)
        
        for meaning_card, reading_card in zip(vocab_meaning_cards, vocab_reading_cards):
            all_cards.append(meaning_card)
            all_cards.append(reading_card)
            vocab_meaning_count += 1
            vocab_reading_count += 1

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
    print(f"Radicals: {radical_count}")
    print(f"Kanji meanings: {kanji_meaning_count}")
    print(f"Kanji readings: {kanji_reading_count}")
    print(f"Vocab meanings: {vocab_meaning_count}")
    print(f"Vocab readings: {vocab_reading_count}")
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
