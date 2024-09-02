import json
import logging
from typing import Dict, List

import pandas as pd


class PartsOfTheBookOrder:
    """
    Class to manage the order of parts in a book according to Chicago Manual of Style 18th edition.

    Attributes:
        parts (Dict[str, List[str]]): A dictionary representing the structure of the book, where keys are divisions
            (e.g., "Front matter", "Body", "Back matter") and values are lists of parts within that division.
        default_order (List[str]): A list representing the default order of divisions in the book.
        logger (logging.Logger): A logger instance for logging information.

    Methods:
        create_blank_class(self): Creates a blank PartsOfTheBookOrder object with all parts initialized.
        create_blank_class_with_parts(self, parts: List[str]): Creates a blank PartsOfTheBookOrder object with
            specified parts included or excluded.
        create_new_default_order(self, new_order: List[str]): Changes the default order of divisions in the book.
        to_dict(self) -> Dict[str, List[str]]: Returns a dictionary representation of the PartsOfTheBookOrder object.
        to_json(self, file_path: str): Saves the PartsOfTheBookOrder object to a JSON file.
        to_dataframe(self) -> pd.DataFrame: Returns a Pandas DataFrame representation of the PartsOfTheBookOrder object.
        list_missing_parts(self, target_parts: List[str]) -> List[str]: Returns a list of parts missing from the
            current PartsOfTheBookOrder object.
        list_potential_duplicates(self) -> List[str]: Returns a list of parts that potentially have duplicates in
            the current PartsOfTheBookOrder object.
    """

    def __init__(self):
        self.parts = {
            "Front matter": [
                "Praise page(s)",
                "Book half title",
                "Series title, other works, frontispiece, or blank",
                "Title page",
                "Copyright page",
                "Dedication",
                "Epigraph",
                "(Table of) Contents",
                "(List of) Illustrations",
                "(List of) Tables",
                "Foreword",
                "Preface",
                "Acknowledgments (if not in preface or back matter)",
                "Introduction (if not part of text)",
                "Abbreviations (if not in back matter)",
                "Chronology (if not in back matter)"
            ],
            "Body": [
                "Second half title",
                "First part title",
                "Blank spacer page (verso)",
                "Introduction (if present)",
                "Chapters",
                "Conclusion",
                "Epilogue or Afterword"
            ],
            "Back matter": [
                "Acknowledgments",
                "Appendix (or first appendix, if more than one)",
                "Subsequent appendixes",
                "Chronology (if not in front matter)",
                "(List of) Abbreviations (if not in front matter)",
                "Glossary",
                "Notes (if not footnotes or chapter endnotes)",
                "Bibliography or References",
                "(List of) Contributors",
                "Illustration credits (if not in captions or elsewhere)",
                "Index(es)",
                "Reading group guide",
                "About the author (if not on back cover or elsewhere)",
                "Colophon (production details)"
            ],
            "Cover text": [],
            "Outside-the-pages text": [],
            "Foldouts (only if specified)": [],
            "Included Artifacts (only if specified)": []
        }
        self.default_order = [
            "Front matter",
            "Body",
            "Back matter",
            "Cover text",
            "Outside-the-pages text",
            "Foldouts (only if specified)",
            "Included Artifacts (only if specified)"
        ]
        self.logger = logging.getLogger(__name__)

    def create_blank_class(self):
        """Creates a blank PartsOfTheBookOrder object with all parts initialized."""
        self.parts = {
            "Front matter": [],
            "Body": [],
            "Back matter": [],
            "Cover text": [],
            "Outside-the-pages text": [],
            "Foldouts (only if specified)": [],
            "Included Artifacts (only if specified)": []
        }

    def create_blank_class_with_parts(self, parts: List[str]):
        """
        Creates a blank PartsOfTheBookOrder object with specified parts included or excluded.

        Args:
            parts (List[str]): A list of parts to include in the blank object.
        """
        self.create_blank_class()
        for part in parts:
            for division, division_parts in self.parts.items():
                if part in division_parts:
                    self.parts[division].append(part)

    def create_new_default_order(self, new_order: List[str]):
        """
        Changes the default order of divisions in the book.

        Args:
            new_order (List[str]): A list representing the new default order of divisions.
        """
        self.default_order = new_order

    def to_dict(self) -> Dict[str, List[str]]:
        """Returns a dictionary representation of the PartsOfTheBookOrder object."""
        return {
            "parts": self.parts,
            "default_order": self.default_order
        }

    def to_json(self, file_path: str):
        """Saves the PartsOfTheBookOrder object to a JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            self.logger.info(f"PartsOfTheBookOrder object saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving PartsOfTheBookOrder object to JSON: {e}")

    def to_dataframe(self) -> pd.DataFrame:
        """Returns a Pandas DataFrame representation of the PartsOfTheBookOrder object."""
        # TODO: Implement this method to create a Pandas DataFrame from the parts dictionary.
        pass

    def list_missing_parts(self, target_parts: List[str]) -> List[str]:
        """
        Returns a list of parts missing from the current PartsOfTheBookOrder object.

        Args:
            target_parts (List[str]): A list of parts to check for.
        """
        missing_parts = []
        for part in target_parts:
            found = False
            for division, division_parts in self.parts.items():
                if part in division_parts:
                    found = True
                    break
            if not found:
                missing_parts.append(part)
        return missing_parts

    def list_potential_duplicates(self) -> List[str]:
        """Returns a list of parts that potentially have duplicates in the current PartsOfTheBookOrder object."""
        potential_duplicates = []
        for division, division_parts in self.parts.items():
            for part in division_parts:
                if division_parts.count(part) > 1:
                    potential_duplicates.append(part)
        return potential_duplicates
