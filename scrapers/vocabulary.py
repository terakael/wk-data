#!/usr/bin/env python3
"""
WaniKani Vocabulary Scraper - CLEAN Version with Proper XML Tags
Extracts detailed vocabulary information including properly XML-tagged keywords from WaniKani vocabulary pages
"""

import json
import time
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class WaniKaniVocabularyScraper:
    def __init__(
        self,
        input_file: str = "vocabulary.json",
        output_file: str = "wanikani_vocabulary_complete.json",
        checkpoint_file: str = "vocab_scraper_checkpoint.json",
    ):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.checkpoint_file = Path(checkpoint_file)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("vocab_scraper.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Setup session
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        # Load vocabulary data
        self._load_vocabulary_data()

        # Initialize results
        self.results = self._load_existing_results()

    def _load_vocabulary_data(self):
        """Load vocabulary data from input file"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                self.vocab_data = json.load(f)
            self.logger.info(
                f"Loaded vocabulary data for {len(self.vocab_data)} levels"
            )
        except Exception as e:
            self.logger.error(f"Failed to load vocabulary data: {e}")
            raise

    def _load_existing_results(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load existing results from output file"""
        if self.output_file.exists():
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    return json.load(f)
                self.logger.info(f"Loaded existing results from {self.output_file}")
            except Exception as e:
                self.logger.warning(f"Could not load existing results: {e}")
        return {}

    def _save_checkpoint(self, level: int):
        """Save checkpoint after completing a level"""
        try:
            with open(self.checkpoint_file, "w") as f:
                json.dump({"last_completed_level": level}, f)
        except Exception as e:
            self.logger.warning(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> Optional[int]:
        """Load checkpoint to resume from specific level"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r") as f:
                    data = json.load(f)
                    return data.get("last_completed_level")
            except Exception as e:
                self.logger.warning(f"Failed to load checkpoint: {e}")
        return None

    def _save_results(self):
        """Save current results to output file"""
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a web page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            raise

    def extract_meanings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract primary and alternative meanings"""
        meanings = {"primary": "", "alternatives": []}

        # Find primary meaning section
        primary_section = soup.find("div", class_="subject-section__meanings--primary")
        if primary_section:
            primary_element = primary_section.find(
                "p", class_="subject-section__meanings-items"
            )
            if primary_element:
                primary_text = primary_element.get_text().strip()
                meanings["primary"] = primary_text

        # Find alternative meaning section (separate from primary)
        # Look for any meaning section that contains "Alternatives" in the header
        all_meaning_sections = soup.find_all("div", class_="subject-section__meanings")
        for section in all_meaning_sections:
            section_classes = section.get("class") or []
            # Skip primary sections
            if "subject-section__meanings--primary" in section_classes:
                continue

            # Look for "Alternative" or "Alternatives" header - check any element in the section
            all_elements = section.find_all()
            for element in all_elements:
                element_text = element.get_text().strip()
                if element_text.lower() in ["alternative", "alternatives"]:
                    # Found the alternatives header - now find the meaning items
                    alt_element = section.find(
                        "p", class_="subject-section__meanings-items"
                    )
                    if alt_element:
                        alt_text = alt_element.get_text().strip()
                        # Split by comma
                        if "," in alt_text:
                            alternatives = [
                                part.strip() for part in alt_text.split(",")
                            ]
                            meanings["alternatives"].extend(
                                [alt for alt in alternatives if alt and len(alt) > 1]
                            )
                        else:
                            meanings["alternatives"].append(alt_text)
                    break

        return meanings

    def extract_reading(self, soup: BeautifulSoup) -> str:
        """Extract vocabulary reading"""
        # Find Reading section
        reading_section = None
        for heading in soup.find_all("h2"):
            if "Reading" in heading.get_text():
                reading_section = heading.find_next("div")
                break

        if not reading_section:
            return ""

        # Look for reading element with specific class
        reading_element = reading_section.find(
            "div", class_="reading-with-audio__reading"
        )
        if reading_element:
            return reading_element.get_text().strip()

        # Fallback: find any Japanese text in section
        for element in reading_section.find_all(["p", "span", "div"]):
            text = element.get_text().strip()
            if text and any(
                "\u3040" <= c <= "\u309f" or "\u30a0" <= c <= "\u30ff" for c in text
            ):
                if len(text) < 20:  # Likely a reading, not a description
                    return text

        return ""

    def extract_explanation_with_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract explanations with embedded XML-style tags for keywords"""
        explanations = {"meaning": "", "reading": ""}

        # Find all explanation sections
        for heading in soup.find_all("h3"):
            if "Explanation" in heading.get_text():
                # Find the parent section
                section = heading.find_parent("section", class_="subject-section")
                if not section:
                    continue

                # Get all explanation paragraphs within this section
                explanation_parts = []
                for p in section.find_all("p", class_="subject-section__text"):
                    # Preserve inner HTML content
                    inner_html = ""
                    for content in p.contents:
                        inner_html += str(content)
                    explanation_parts.append(inner_html.strip())

                explanation = " ".join(explanation_parts)

                # Determine context by finding previous h2 heading
                prev_h2 = heading.find_previous("h2")
                if prev_h2:
                    context = prev_h2.get_text().strip().lower()

                    # Categorize based on context
                    if "meaning" in context or "word type" in context:
                        explanations["meaning"] = explanation
                    elif "reading" in context:
                        explanations["reading"] = explanation
                else:
                    # Fallback: if no clear context, assume it's meaning explanation
                    if not explanations["meaning"]:
                        explanations["meaning"] = explanation

        return explanations

    def extract_kanji_composition(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract kanji composition with kanji, reading, and meaning"""
        kanji_components = []

        # Find Kanji Composition section
        comp_section = None
        for heading in soup.find_all("h2"):
            if "Kanji Composition" in heading.get_text():
                comp_section = heading.find_next("div")
                break

        if not comp_section:
            return kanji_components

        # Find all kanji items in composition grid
        kanji_items = comp_section.find_all("li", class_="subject-character-grid__item")

        for item in kanji_items:
            # Extract kanji character
            kanji_element = item.find(
                "span", class_="subject-character__characters-text"
            )
            kanji = kanji_element.get_text().strip() if kanji_element else ""

            # Extract reading
            reading_element = item.find("span", class_="subject-character__reading")
            reading = reading_element.get_text().strip() if reading_element else ""

            # Extract meaning
            meaning_element = item.find("span", class_="subject-character__meaning")
            meaning = meaning_element.get_text().strip() if meaning_element else ""

            # Get URL if available
            link_element = item.find("a")
            url = link_element.get("href", "") if link_element else ""

            if kanji:  # Only add if we have kanji character
                kanji_components.append(
                    {"kanji": kanji, "reading": reading, "meaning": meaning, "url": url}
                )

        return kanji_components

    def extract_vocabulary_data(self, vocab_info: Dict[str, str]) -> Dict[str, Any]:
        """Extract all data for a single vocabulary item"""
        url = vocab_info["url"]
        character = vocab_info["character"]

        self.logger.info(f"Processing {character}: {url}")

        try:
            soup = self.fetch_page(url)

            # Extract all components
            meanings = self.extract_meanings(soup)
            reading = self.extract_reading(soup)
            explanations = self.extract_explanation_with_tags(soup)
            kanji_composition = self.extract_kanji_composition(soup)

            return {
                "character": character,
                "url": url,
                "meaning": vocab_info.get("meaning", ""),
                "primary_meaning": meanings["primary"],
                "alternative_meanings": meanings["alternatives"],
                "reading": reading,
                "meaning_explanation": explanations["meaning"],
                "reading_explanation": explanations["reading"],
                "kanji_composition": kanji_composition,
                "type": vocab_info.get("type", ""),
            }

        except Exception as e:
            self.logger.error(f"Error processing {character}: {e}")
            raise

    def process_level(self, level: int) -> List[Dict[str, Any]]:
        """Process all vocabulary in a specific level"""
        level_str = str(level)
        if level_str not in self.vocab_data:
            self.logger.error(f"Level {level} not found in vocabulary data")
            raise ValueError(f"Level {level} not found")

        vocab_list = self.vocab_data[level_str]
        level_results = []

        self.logger.info(
            f"Processing level {level} with {len(vocab_list)} vocabulary items"
        )

        for vocab_info in tqdm(vocab_list, desc=f"Level {level}"):
            try:
                vocab_data = self.extract_vocabulary_data(vocab_info)
                level_results.append(vocab_data)
                # Rate limiting
                time.sleep(1.5)
            except Exception as e:
                self.logger.error(
                    f"Failed to process {vocab_info.get('character', 'unknown')}: {e}"
                )
                raise

        return level_results

    def run(self, start_level: int = 1, end_level: int = 60):
        """Run scraper from start_level to end_level"""
        # Check for checkpoint to resume
        checkpoint = self._load_checkpoint()
        if checkpoint is not None:
            start_level = checkpoint + 1
            self.logger.info(f"Resuming from level {start_level}")

        # Load any existing results
        if self.output_file.exists():
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    self.results = json.load(f)
                self.logger.info(
                    f"Loaded existing results with {len(self.results)} levels"
                )
            except Exception as e:
                self.logger.warning(f"Could not load existing results: {e}")
                self.results = {}

        # Process each level
        for level in range(start_level, end_level + 1):
            self.logger.info(f"Starting level {level}")

            try:
                level_results = self.process_level(level)
                self.results[str(level)] = level_results

                # Save results after each level
                self._save_results()
                self._save_checkpoint(level)

                self.logger.info(
                    f"Completed level {level}: {len(level_results)} vocabulary items"
                )

            except Exception as e:
                self.logger.error(f"Failed to process level {level}: {e}")
                raise

        self.logger.info(f"Scraping completed! Processed {len(self.results)} levels")

        # Clean up checkpoint file
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()


if __name__ == "__main__":
    scraper = WaniKaniVocabularyScraper()
    scraper.run(start_level=1, end_level=60)
