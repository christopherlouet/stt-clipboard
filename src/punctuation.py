"""Language-aware punctuation post-processing for transcribed text.

This module provides punctuation normalization and typography rules for
transcribed text, with support for French and English typography conventions.

French typography rules:
    - Space BEFORE: ? ! : ;
    - No space before: , .
    - Proper handling of guillemets (« »)
    - Contraction handling (l', d', qu', etc.)

English typography rules:
    - No space before any punctuation
    - Space after punctuation marks

Example:
    Basic usage with auto-detected language::

        from src.punctuation import apply_french_punctuation

        # French text
        text = apply_french_punctuation(
            "comment allez vous?",
            detected_language="fr"
        )
        # Result: "Comment allez vous ?"

        # English text
        text = apply_french_punctuation(
            "how are you?",
            detected_language="en"
        )
        # Result: "How are you?"

    Using the processor class::

        from src.punctuation import PunctuationProcessor

        processor = PunctuationProcessor(enable_french_spacing=True)
        text = processor.process("bonjour comment vas tu", detected_language="fr")
"""

import re

from loguru import logger


def apply_french_punctuation(
    text: str, enable_french_spacing: bool = True, detected_language: str | None = None
) -> str:
    """Apply language-appropriate typography rules to transcribed text.

    French typography requires:
    - Space before: ? ! : ;
    - No space before: , .
    - Capitalization after sentence-ending punctuation
    - Proper handling of apostrophes and quotes

    English typography requires:
    - No space before any punctuation
    - Space after punctuation
    - Capitalization after sentence-ending punctuation

    Args:
        text: Input text to process
        enable_french_spacing: Whether to apply French spacing rules when detected
        detected_language: Detected language code (e.g., "fr", "en")

    Returns:
        Processed text with proper punctuation for the detected language
    """
    if not text or not text.strip():
        return text

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Determine if we should apply French spacing based on detected language
    # Apply French spacing only if: enabled AND (no language detected OR language is French)
    apply_french_rules = enable_french_spacing and (
        detected_language is None or detected_language == "fr"
    )

    if apply_french_rules:
        # Add space before French punctuation marks (if not already present)
        # Handle: ? ! : ;
        text = re.sub(r"\s*([?!:;])", r" \1", text)

        # Remove space after opening quotes
        text = re.sub(r"«\s+", "« ", text)

        # Remove space before closing quotes
        text = re.sub(r"\s+»", " »", text)
    else:
        # For English and other languages: ensure NO space before punctuation
        text = re.sub(r"\s+([?!:;])", r"\1", text)

    # Remove space before commas and periods
    text = re.sub(r"\s+([,.])", r"\1", text)

    # Ensure space after commas and periods (if followed by a letter)
    text = re.sub(r"([,.])([A-Za-zÀ-ÿ])", r"\1 \2", text)

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    # Capitalize after sentence-ending punctuation (. ! ?)
    def capitalize_after_punctuation(match):
        punct = match.group(1)
        space = match.group(2)
        letter = match.group(3).upper()
        return f"{punct}{space}{letter}"

    text = re.sub(r"([.!?])(\s+)([a-zà-ÿ])", capitalize_after_punctuation, text)

    # Handle common French contractions and apostrophes (only for French)
    if apply_french_rules:
        # Ensure no space after apostrophe
        text = re.sub(r"([ldjmtscn])\s+'", r"\1'", text, flags=re.IGNORECASE)
        text = re.sub(r"qu\s+'", "qu'", text, flags=re.IGNORECASE)

    # Fix common Whisper artifacts
    # Remove multiple punctuation marks
    text = re.sub(r"([.!?]){2,}", r"\1", text)

    # Clean up multiple spaces again (in case we introduced any)
    text = re.sub(r"\s+", " ", text)

    # Final trim
    text = text.strip()

    lang_info = f"lang={detected_language}" if detected_language else "lang=unknown"
    rules_applied = "French" if apply_french_rules else "English/other"
    logger.debug(f"Punctuation processed: {len(text)} chars ({lang_info}, {rules_applied} rules)")

    return text


def clean_whisper_artifacts(text: str) -> str:
    """Remove common Whisper transcription artifacts.

    Args:
        text: Input text from Whisper

    Returns:
        Cleaned text
    """
    # Remove common filler words that Whisper sometimes adds
    fillers = [
        r"\b(euh|euuh|euhh)\b",
        r"\b(hum|humm|hmmm)\b",
    ]

    for filler in fillers:
        text = re.sub(filler, "", text, flags=re.IGNORECASE)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def format_for_code(text: str) -> str:
    """Format text for code/command input.

    Removes punctuation that might interfere with code/commands.

    Args:
        text: Input text

    Returns:
        Text formatted for code input
    """
    # Keep only alphanumeric, spaces, and basic programming characters
    # This is useful for dictating commands or code
    text = text.strip()

    # Remove sentence-ending punctuation if it's at the end
    text = re.sub(r"[.!?;:,]+$", "", text)

    return text.strip()


class PunctuationProcessor:
    """Punctuation processor with configurable options."""

    def __init__(
        self,
        enable_french_spacing: bool = True,
        clean_artifacts: bool = True,
        capitalize: bool = True,
    ):
        """Initialize punctuation processor.

        Args:
            enable_french_spacing: Apply French typography rules
            clean_artifacts: Remove Whisper artifacts
            capitalize: Capitalize sentences
        """
        self.enable_french_spacing = enable_french_spacing
        self.clean_artifacts = clean_artifacts
        self.capitalize = capitalize

    def process(self, text: str, detected_language: str | None = None) -> str:
        """Process text with configured options.

        Args:
            text: Input text
            detected_language: Detected language code (e.g., "fr", "en")

        Returns:
            Processed text with language-appropriate rules
        """
        if not text or not text.strip():
            return text

        # Clean artifacts first
        if self.clean_artifacts:
            text = clean_whisper_artifacts(text)

        # Apply punctuation rules based on detected language
        text = apply_french_punctuation(
            text,
            enable_french_spacing=self.enable_french_spacing,
            detected_language=detected_language,
        )

        return text


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_texts = [
        "bonjour comment allez vous",
        "je m appelle claude et j aime programmer",
        "quelle est la météo aujourd hui",
        "attention  c est important",
        "l homme est arrivé hier soir. il était fatigué",
        "pourquoi pas?c'est une bonne idée!",
    ]

    print("French Punctuation Tests:")
    print("=" * 60)

    processor = PunctuationProcessor()

    for text in test_texts:
        result = processor.process(text)
        print(f"Input:  {text}")
        print(f"Output: {result}")
        print("-" * 60)
