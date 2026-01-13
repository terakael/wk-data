#!/usr/bin/env python3
"""
WaniKani Radicals Scraper
Extracts mnemonic text and images from WaniKani radical pages with HTML tags preserved.
"""

import json
import time
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class RadicalsScraper:
    def __init__(
        self,
        input_file: str = "characters.json",
        output_file: str = "wanikani_radicals_complete.json",
        checkpoint_file: str = "radicals_scraper_checkpoint.json",
    ):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.checkpoint_file = Path(checkpoint_file)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("radicals_scraper.log"),
                logging.StreamHandler(sys.stdout),
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

        # Load radical data
        self._load_radicals_data()

        # Initialize results
        self.results = self._load_existing_results()

    def _load_radicals_data(self):
        """Load radicals data from input file"""
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                self.radicals_data = json.load(f)
            self.logger.info(
                f"Loaded radicals data for {len(self.radicals_data)} levels"
            )
        except Exception as e:
            self.logger.error(f"Failed to load radicals data: {e}")
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

    def extract_mnemonic(self, soup: BeautifulSoup) -> str:
        """Extract mnemonic text with <mark> tags preserved"""
        # Find all h3 elements with class 'subject-section__subtitle'
        for heading in soup.find_all("h3", class_="subject-section__subtitle"):
            if "Mnemonic" in heading.get_text():
                # Find the parent section
                section = heading.find_parent("section", class_="subject-section")
                if not section:
                    continue

                # Get all mnemonic paragraphs within this section
                mnemonic_parts = []
                for p in section.find_all("p", class_="subject-section__text"):
                    # Get the inner HTML to preserve mark tags
                    mnemonic_html = ""
                    for content in p.contents:
                        mnemonic_html += str(content)
                    mnemonic_parts.append(mnemonic_html.strip())

                mnemonic = " ".join(mnemonic_parts)
                if mnemonic.strip():
                    return mnemonic.strip()

        # If we get here, no mnemonic was found - this should never happen
        raise ValueError("No mnemonic found on this radical page")

    def extract_mnemonic_image(self, soup: BeautifulSoup) -> str:
        """Extract mnemonic image URL from wk-mnemonic-image element"""
        # Find wk-mnemonic-image element
        mnemonic_image = soup.find("wk-mnemonic-image")
        if mnemonic_image:
            src = mnemonic_image.get("src")
            if src and isinstance(src, str):
                return src.strip()

        # If no mnemonic image found, return empty string
        return ""

    def extract_radical_data(self, radical_info: Dict[str, str]) -> Dict[str, Any]:
        """Extract all data for a single radical"""
        url = radical_info["url"]
        character = radical_info["character"]

        self.logger.info(f"Processing {character}: {url}")

        try:
            soup = self.fetch_page(url)

            # Extract all components
            mnemonic = self.extract_mnemonic(soup)
            mnemonic_image = self.extract_mnemonic_image(soup)

            return {
                "character": character,
                "url": url,
                "meaning": radical_info.get("meaning", ""),
                "mnemonic": mnemonic,
                "mnemonic_image": mnemonic_image,
                "type": radical_info.get("type", ""),
            }

        except Exception as e:
            self.logger.error(f"Error processing {character}: {e}")
            raise

    def process_level(self, level: int) -> List[Dict[str, Any]]:
        """Process all radicals in a specific level"""
        level_str = str(level)
        if level_str not in self.radicals_data:
            self.logger.warning(f"Level {level} not found in radicals data, skipping")
            return []

        radicals_list = self.radicals_data[level_str]
        if not radicals_list:
            self.logger.warning(f"Level {level} has no radicals, skipping")
            return []

        level_results = []

        self.logger.info(
            f"Processing level {level} with {len(radicals_list)} radical items"
        )

        for radical_info in tqdm(radicals_list, desc=f"Level {level}"):
            try:
                radical_data = self.extract_radical_data(radical_info)
                level_results.append(radical_data)
                # Rate limiting
                time.sleep(1.5)
            except Exception as e:
                self.logger.error(
                    f"Failed to process {radical_info.get('character', 'unknown')}: {e}"
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
                if level_results:  # Only save levels with results
                    self.results[str(level)] = level_results

                    # Save results after each level
                    self._save_results()
                    self._save_checkpoint(level)

                    self.logger.info(
                        f"Completed level {level}: {len(level_results)} radical items"
                    )
                else:
                    self.logger.info(f"Skipped level {level}: no radicals found")
                    # Still save checkpoint for skipped levels
                    self._save_checkpoint(level)

            except Exception as e:
                self.logger.error(f"Failed to process level {level}: {e}")
                raise

        self.logger.info(f"Scraping completed! Processed {len(self.results)} levels")

        # Clean up checkpoint file
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()


if __name__ == "__main__":
    scraper = RadicalsScraper()
    scraper.run(start_level=1, end_level=60)
