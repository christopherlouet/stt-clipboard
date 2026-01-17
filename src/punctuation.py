"""Language-aware punctuation post-processing for transcribed text."""

import re

from loguru import logger

from src.languages import get_language_rules


def apply_punctuation_rules(
    text: str, enable_french_spacing: bool = True, detected_language: str | None = None
) -> str:
    """Apply language-appropriate typography rules to transcribed text.

    Applies language-specific rules for:
    - French: Space before ? ! : ; and « » quotes
    - German: „ " quotes, no space before punctuation
    - Spanish/Italian: « » quotes, no space before punctuation
    - English: " " quotes, no space before punctuation

    Args:
        text: Input text to process
        enable_french_spacing: Whether to apply French spacing rules when detected
        detected_language: Detected language code (e.g., "fr", "en", "de", "es", "it")

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

    # Get language rules for other processing (quotes, capitalization)
    rules = get_language_rules(detected_language)

    # Apply space before punctuation based on French rules setting
    if apply_french_rules:
        # Add space before French punctuation marks (? ! : ;)
        text = re.sub(r"\s*([?!:;])", r" \1", text)
    else:
        # For non-French: ensure NO space before punctuation
        text = re.sub(r"\s+([?!:;])", r"\1", text)

    # Remove space before commas and periods (universal rule)
    no_space_pattern = "".join(re.escape(p) for p in rules.no_space_before_punctuation)
    text = re.sub(rf"\s+([{no_space_pattern}])", r"\1", text)

    # Handle quotes based on language
    if rules.opening_quote == "\u00ab":  # French-style « »
        text = re.sub(r"\u00ab\s+", "\u00ab ", text)
        text = re.sub(r"\s+\u00bb", " \u00bb", text)
    elif rules.opening_quote == "\u201e":  # German-style „ "
        text = re.sub(r"\u201e\s+", "\u201e", text)
        text = re.sub(r"\s+\u201c", "\u201c", text)

    # Ensure space after commas and periods (if followed by a letter)
    text = re.sub(r"([,.])([A-Za-z\u00c0-\u00ff])", r"\1 \2", text)

    # Capitalize first letter
    if text and rules.capitalize_after_sentence:
        text = text[0].upper() + text[1:]

    # Capitalize after sentence-ending punctuation (. ! ?)
    if rules.capitalize_after_sentence:

        def capitalize_after_punctuation(match: re.Match[str]) -> str:
            punct = match.group(1)
            space = match.group(2)
            letter = match.group(3).upper()
            return f"{punct}{space}{letter}"

        text = re.sub(r"([.!?])(\s+)([a-z\u00e0-\u00ff])", capitalize_after_punctuation, text)

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
    rules_applied = "French" if apply_french_rules else f"{detected_language or 'default'}"
    logger.debug(f"Punctuation processed: {len(text)} chars ({lang_info}, {rules_applied} rules)")

    return text


def clean_whisper_artifacts(text: str, detected_language: str | None = None) -> str:
    """Remove common Whisper transcription artifacts.

    Uses language-specific filler word lists for better cleanup.
    When no language is detected, uses French filler words (backward compatible).

    Args:
        text: Input text from Whisper
        detected_language: Detected language code for language-specific cleanup

    Returns:
        Cleaned text
    """
    # Get language-specific filler words
    # Default to French when no language detected (backward compatible)
    effective_language = detected_language if detected_language else "fr"
    rules = get_language_rules(effective_language)

    # Remove filler words from the language rules
    for filler in rules.filler_words:
        text = re.sub(rf"\b{re.escape(filler)}\b", "", text, flags=re.IGNORECASE)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# Backward compatibility alias
def apply_french_punctuation(
    text: str, enable_french_spacing: bool = True, detected_language: str | None = None
) -> str:
    """Apply language-appropriate typography rules to transcribed text.

    Deprecated: Use apply_punctuation_rules() instead.
    This alias is kept for backward compatibility.
    """
    return apply_punctuation_rules(text, enable_french_spacing, detected_language)


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
            detected_language: Detected language code (e.g., "fr", "en", "de", "es", "it")

        Returns:
            Processed text with language-appropriate rules
        """
        if not text or not text.strip():
            return text

        # Clean artifacts first (with language-specific filler words)
        if self.clean_artifacts:
            text = clean_whisper_artifacts(text, detected_language)

        # Apply punctuation rules based on detected language
        text = apply_punctuation_rules(
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
