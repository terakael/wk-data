#!/usr/bin/env python3
"""
WaniKani Kanji Scraper

Extracts readings, radical combinations, and mnemonics from WaniKani kanji pages.
Processes levels incrementally with checkpoint/resume capability.
"""

import json
import time
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("kanji_scraper.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


class WaniKaniScraper:
    def __init__(
        self,
        input_file: str = "kanji.json",
        output_file: str = "wanikani_kanji_complete.json",
    ):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.checkpoint_file = Path("kanji_scraper_checkpoint.json")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # Load kanji data
        self.kanji_data = self._load_kanji_data()
        self.results = {}

    def _load_kanji_data(self) -> Dict[str, List[Dict[str, str]]]:
        """Load the kanji.json file"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Input file {self.input_file} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in {self.input_file}")
            sys.exit(1)

    def _save_checkpoint(self, level: int):
        """Save checkpoint after processing a level"""
        checkpoint = {"last_completed_level": level, "timestamp": time.time()}
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2)
        logging.info(f"Checkpoint saved after level {level}")

    def _load_checkpoint(self) -> Optional[int]:
        """Load checkpoint to resume from last completed level"""
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
                return checkpoint.get("last_completed_level")
        except (json.JSONDecodeError, KeyError):
            logging.warning("Invalid checkpoint file, starting fresh")
            return None

    def _save_results(self):
        """Save current results to output file"""
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a kanji page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, "lxml")
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {url}: {e}")
            raise

    def extract_readings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract on'yomi, kun'yomi, and nanori readings"""
        readings = {"on'yomi": [], "kun'yomi": [], "nanori": []}

        # Find the Readings section
        reading_section = None
        for heading in soup.find_all("h2"):
            if "Readings" in heading.get_text():
                reading_section = heading.find_next("div")
                break

        if not reading_section:
            return readings

        # Extract readings using the specific HTML structure
        # Each reading type is in a div with class "subject-readings__reading"
        reading_divs = reading_section.find_all(
            "div", class_="subject-readings__reading"
        )

        for reading_div in reading_divs:
            # Get the reading type from the h3 title
            title_element = reading_div.find(
                "h3", class_="subject-readings__reading-title"
            )
            if not title_element:
                continue

            title_text = title_element.get_text().strip()

            # Determine reading type using simple pattern matching
            if "On" in title_text and "yomi" in title_text:
                readings_type = "on'yomi"
            elif "Kun" in title_text and "yomi" in title_text:
                readings_type = "kun'yomi"
            elif "Nanori" in title_text:
                readings_type = "nanori"
            else:
                continue

            # Get the readings from the p tag with class "subject-readings__reading-items"
            readings_element = reading_div.find(
                "p", class_="subject-readings__reading-items"
            )
            if not readings_element:
                continue

            readings_text = readings_element.get_text().strip()

            # Extract readings (skip "None" values)
            if readings_text and readings_text.lower() != "none":
                readings_list = [
                    r.strip()
                    for r in readings_text.replace("、", ",").split(",")
                    if r.strip() and r.strip().lower() != "none"
                ]
                if readings_list:
                    readings[readings_type].extend(readings_list)

        return readings

        # Extract readings - structure is div containing reading type and readings
        # Each div has the reading type as the first element and readings as the second
        divs = reading_section.find_all("div")
        for div in divs:
            div_text = div.get_text().strip()

            # Check what reading type this div contains
            if "On'yomi" in div_text:
                readings_type = "on'yomi"
            elif "Kun'yomi" in div_text:
                readings_type = "kun'yomi"
            elif "Nanori" in div_text:
                readings_type = "nanori"
            else:
                continue

            # Get all text content and extract the readings part
            # The readings are the part after the reading type name
            lines = div_text.split("\n")
            readings_text = ""

            # Find the line that contains the actual readings
            for line in lines:
                line = line.strip()
                if line and line not in ["On'yomi", "Kun'yomi", "Nanori", "None"]:
                    readings_text = line
                    break

            # Extract readings (skip "None" values)
            if readings_text and readings_text.lower() != "none":
                readings_list = [
                    r.strip()
                    for r in readings_text.replace("、", ",").split(",")
                    if r.strip() and r.strip().lower() != "none"
                ]
                if readings_list:
                    readings[readings_type].extend(readings_list)

        return readings

        # Extract readings - structure is h3 followed by p tag containing readings
        h3_tags = reading_section.find_all("h3")
        for h3 in h3_tags:
            heading_text = h3.get_text().strip()

            # Get the paragraph immediately following this h3
            next_p = h3.find_next_sibling("p")
            if not next_p:
                continue

            readings_text = next_p.get_text().strip()

            # Determine reading type and extract readings
            if "On'yomi" in heading_text:
                readings_type = "on'yomi"
            elif "Kun'yomi" in heading_text:
                readings_type = "kun'yomi"
            elif "Nanori" in heading_text:
                readings_type = "nanori"
            else:
                continue

            # Extract readings (skip "None" values)
            if readings_text and readings_text.lower() != "none":
                readings_list = [
                    r.strip()
                    for r in readings_text.replace("、", ",").split(",")
                    if r.strip() and r.strip().lower() != "none"
                ]
                if readings_list:
                    readings[readings_type].extend(readings_list)

        return readings

    def extract_radical_combination(self, soup: BeautifulSoup) -> List[str]:
        """Extract radical combination (English names only)"""
        radicals = []

        # Find the Radical Combination section
        rad_section = None
        for heading in soup.find_all("h2"):
            if "Radical Combination" in heading.get_text():
                rad_section = heading.find_next("div")
                break

        if not rad_section:
            return radicals

        # Extract radical names
        for link in rad_section.find_all("a"):
            # Get the English name (usually the text after the Japanese character)
            text = link.get_text().strip()
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                # Check if it's English (contains letters, not just Japanese characters)
                if line and any(c.isascii() and c.isalpha() for c in line):
                    if line not in radicals:
                        radicals.append(line)

        return radicals

    def extract_mnemonics(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meaning and reading mnemonics with HTML tags preserved"""
        mnemonics = {"meaning": "", "reading": ""}

        # Find all h3 tags that say "Mnemonic"
        for heading in soup.find_all("h3", class_="subject-section__subtitle"):
            if "Mnemonic" not in heading.get_text().strip():
                continue
            
            # Find the subsection containing this mnemonic
            subsection = heading.find_parent("section", class_="subject-section__subsection")
            if not subsection:
                continue
            
            # Collect mnemonic paragraphs (both main text and hints)
            mnemonic_parts = []
            
            # Get main mnemonic text
            for p in subsection.find_all("p", class_="subject-section__text"):
                inner_html = "".join(str(content) for content in p.contents)
                mnemonic_parts.append(inner_html.strip())
            
            # Get hint texts
            for p in subsection.find_all("p", class_="subject-hint__text"):
                inner_html = "".join(str(content) for content in p.contents)
                mnemonic_parts.append(inner_html.strip())
            
            mnemonic_html = "\n\n".join(mnemonic_parts)
            
            # Determine if it's meaning or reading mnemonic
            # Check if this subsection is within the Reading section
            parent_section = subsection.find_parent("section", class_="subject-section")
            if parent_section:
                classes = parent_section.get("class")
                # Handle case where class attribute might be a string or list
                if classes:
                    if isinstance(classes, list):
                        is_reading = "subject-section--reading" in classes
                    else:
                        is_reading = "subject-section--reading" in str(classes)
                else:
                    is_reading = False
                
                if is_reading:
                    mnemonics["reading"] = mnemonic_html
                else:
                    mnemonics["meaning"] = mnemonic_html

        return mnemonics

    def extract_kanji_data(self, kanji_info: Dict[str, str]) -> Dict[str, Any]:
        """Extract all data for a single kanji"""
        url = kanji_info["url"]
        character = kanji_info["character"]

        logging.info(f"Processing {character}: {url}")

        try:
            soup = self.fetch_page(url)

            # Extract all components
            readings = self.extract_readings(soup)
            radical_combination = self.extract_radical_combination(soup)
            mnemonics = self.extract_mnemonics(soup)

            return {
                "character": character,
                "url": url,
                "meaning": kanji_info.get("meaning", ""),
                "readings": readings,
                "radical_combination": radical_combination,
                "mnemonics": mnemonics,
            }

        except Exception as e:
            logging.error(f"Error processing {character}: {e}")
            raise

    def process_level(self, level: int) -> List[Dict[str, Any]]:
        """Process all kanji in a specific level"""
        level_str = str(level)
        if level_str not in self.kanji_data:
            logging.error(f"Level {level} not found in kanji data")
            raise ValueError(f"Level {level} not found")

        kanji_list = self.kanji_data[level_str]
        level_results = []

        logging.info(f"Processing level {level} with {len(kanji_list)} kanji")

        for kanji_info in tqdm(kanji_list, desc=f"Level {level}"):
            try:
                kanji_data = self.extract_kanji_data(kanji_info)
                level_results.append(kanji_data)
                # Rate limiting
                time.sleep(1.5)
            except Exception as e:
                logging.error(
                    f"Failed to process {kanji_info.get('character', 'unknown')}: {e}"
                )
                raise

        return level_results

    def run(self, start_level: int = 1, end_level: int = 60):
        """Run the scraper from start_level to end_level"""
        # Check for checkpoint to resume
        checkpoint = self._load_checkpoint()
        if checkpoint is not None:
            start_level = checkpoint + 1
            logging.info(f"Resuming from level {start_level}")

        # Load any existing results
        if self.output_file.exists():
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    self.results = json.load(f)
                logging.info(f"Loaded existing results with {len(self.results)} levels")
            except json.JSONDecodeError:
                logging.warning("Invalid existing results file, starting fresh")

        # Process each level
        for level in range(start_level, end_level + 1):
            try:
                logging.info(f"Starting level {level}")
                level_results = self.process_level(level)
                self.results[str(level)] = level_results

                # Save after each level
                self._save_results()
                self._save_checkpoint(level)

                logging.info(f"Completed level {level} with {len(level_results)} kanji")

            except Exception as e:
                logging.error(f"Failed to process level {level}: {e}")
                logging.error("Script stopping on error as requested")
                sys.exit(1)

        logging.info(
            f"Scraping completed successfully! Processed {end_level - start_level + 1} levels"
        )

        # Clean up checkpoint file on successful completion
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()


def main():
    parser = argparse.ArgumentParser(description="WaniKani Kanji Scraper")
    parser.add_argument("--start", type=int, default=1, help="Start level (default: 1)")
    parser.add_argument("--end", type=int, default=60, help="End level (default: 60)")
    parser.add_argument("--input", default="kanji.json", help="Input JSON file")
    parser.add_argument(
        "--output", default="wanikani_kanji_complete.json", help="Output JSON file"
    )

    args = parser.parse_args()

    # Validate levels
    if not (1 <= args.start <= args.end <= 60):
        logging.error("Invalid level range. Must be 1-60 with start <= end")
        sys.exit(1)

    scraper = WaniKaniScraper(args.input, args.output)
    scraper.run(args.start, args.end)


if __name__ == "__main__":
    main()
