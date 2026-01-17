"""Language configuration and rules for STT Clipboard."""

from dataclasses import dataclass, field
from enum import Enum


class SupportedLanguage(Enum):
    """Supported languages for transcription and post-processing."""

    FRENCH = "fr"
    ENGLISH = "en"
    GERMAN = "de"
    SPANISH = "es"
    ITALIAN = "it"

    @classmethod
    def from_code(cls, code: str | None) -> "SupportedLanguage | None":
        """Get language from ISO 639-1 code.

        Args:
            code: ISO 639-1 language code (e.g., "fr", "en")

        Returns:
            SupportedLanguage enum value, or None if not supported
        """
        if code is None:
            return None

        code = code.lower()
        for lang in cls:
            if lang.value == code:
                return lang
        return None

    @classmethod
    def is_supported(cls, code: str | None) -> bool:
        """Check if a language code is supported.

        Args:
            code: ISO 639-1 language code

        Returns:
            True if supported, False otherwise
        """
        return cls.from_code(code) is not None

    @classmethod
    def all_codes(cls) -> list[str]:
        """Get all supported language codes.

        Returns:
            List of ISO 639-1 codes
        """
        return [lang.value for lang in cls]


@dataclass
class LanguageRules:
    """Typography and processing rules for a language."""

    # Punctuation spacing
    space_before_punctuation: list[str] = field(default_factory=list)
    no_space_before_punctuation: list[str] = field(default_factory=lambda: [".", ","])

    # Filler words to remove (speech artifacts)
    filler_words: list[str] = field(default_factory=list)

    # Quotation marks style
    opening_quote: str = '"'
    closing_quote: str = '"'

    # Whether to capitalize after sentence-ending punctuation
    capitalize_after_sentence: bool = True


# Language-specific rules
LANGUAGE_RULES: dict[SupportedLanguage, LanguageRules] = {
    SupportedLanguage.FRENCH: LanguageRules(
        space_before_punctuation=["?", "!", ":", ";"],
        filler_words=["euh", "euuh", "euhh", "hum", "humm", "hmmm", "bah", "ben"],
        opening_quote="\u00ab",  # <<
        closing_quote="\u00bb",  # >>
    ),
    SupportedLanguage.ENGLISH: LanguageRules(
        space_before_punctuation=[],
        filler_words=["uh", "uhh", "um", "umm", "hum", "hmm", "hmmm", "like", "you know"],
        opening_quote='"',
        closing_quote='"',
    ),
    SupportedLanguage.GERMAN: LanguageRules(
        space_before_punctuation=[],
        filler_words=["aeh", "aehm", "oehm", "hm", "hmm", "also", "ja"],
        opening_quote="\u201e",  # German low-9 quote
        closing_quote="\u201c",  # German high-6 quote
    ),
    SupportedLanguage.SPANISH: LanguageRules(
        space_before_punctuation=[],
        filler_words=["eh", "ehh", "um", "umm", "este", "pues", "bueno", "o sea"],
        opening_quote="\u00ab",  # <<
        closing_quote="\u00bb",  # >>
    ),
    SupportedLanguage.ITALIAN: LanguageRules(
        space_before_punctuation=[],
        filler_words=["eh", "ehm", "uhm", "cioe", "allora", "praticamente", "insomma"],
        opening_quote="\u00ab",  # <<
        closing_quote="\u00bb",  # >>
    ),
}


def get_language_rules(language_code: str | None) -> LanguageRules:
    """Get rules for a specific language.

    Args:
        language_code: ISO 639-1 language code, or None for default

    Returns:
        LanguageRules for the specified language, or English rules as default
    """
    if language_code is None:
        return LANGUAGE_RULES[SupportedLanguage.ENGLISH]

    language = SupportedLanguage.from_code(language_code)
    if language is None:
        return LANGUAGE_RULES[SupportedLanguage.ENGLISH]

    return LANGUAGE_RULES[language]


def get_display_name(language_code: str) -> str:
    """Get display name for a language code.

    Args:
        language_code: ISO 639-1 language code

    Returns:
        Human-readable language name
    """
    display_names = {
        "fr": "French",
        "en": "English",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
    }
    return display_names.get(language_code.lower(), language_code)
