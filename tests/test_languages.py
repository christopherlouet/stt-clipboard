"""Tests for language configuration and rules."""

from src.languages import (
    LANGUAGE_RULES,
    LanguageRules,
    SupportedLanguage,
    get_display_name,
    get_language_rules,
)


class TestSupportedLanguage:
    """Tests for SupportedLanguage enum."""

    def test_french_code(self):
        """Test French language code."""
        assert SupportedLanguage.FRENCH.value == "fr"

    def test_english_code(self):
        """Test English language code."""
        assert SupportedLanguage.ENGLISH.value == "en"

    def test_german_code(self):
        """Test German language code."""
        assert SupportedLanguage.GERMAN.value == "de"

    def test_spanish_code(self):
        """Test Spanish language code."""
        assert SupportedLanguage.SPANISH.value == "es"

    def test_italian_code(self):
        """Test Italian language code."""
        assert SupportedLanguage.ITALIAN.value == "it"


class TestSupportedLanguageFromCode:
    """Tests for SupportedLanguage.from_code method."""

    def test_from_code_french(self):
        """Test getting French from code."""
        assert SupportedLanguage.from_code("fr") == SupportedLanguage.FRENCH

    def test_from_code_english(self):
        """Test getting English from code."""
        assert SupportedLanguage.from_code("en") == SupportedLanguage.ENGLISH

    def test_from_code_german(self):
        """Test getting German from code."""
        assert SupportedLanguage.from_code("de") == SupportedLanguage.GERMAN

    def test_from_code_uppercase(self):
        """Test code is case-insensitive."""
        assert SupportedLanguage.from_code("FR") == SupportedLanguage.FRENCH

    def test_from_code_none(self):
        """Test None input returns None."""
        assert SupportedLanguage.from_code(None) is None

    def test_from_code_unsupported(self):
        """Test unsupported code returns None."""
        assert SupportedLanguage.from_code("jp") is None


class TestSupportedLanguageIsSupported:
    """Tests for SupportedLanguage.is_supported method."""

    def test_french_supported(self):
        """Test French is supported."""
        assert SupportedLanguage.is_supported("fr") is True

    def test_english_supported(self):
        """Test English is supported."""
        assert SupportedLanguage.is_supported("en") is True

    def test_japanese_not_supported(self):
        """Test Japanese is not supported."""
        assert SupportedLanguage.is_supported("jp") is False

    def test_none_not_supported(self):
        """Test None is not supported."""
        assert SupportedLanguage.is_supported(None) is False


class TestSupportedLanguageAllCodes:
    """Tests for SupportedLanguage.all_codes method."""

    def test_returns_all_codes(self):
        """Test all codes are returned."""
        codes = SupportedLanguage.all_codes()
        assert "fr" in codes
        assert "en" in codes
        assert "de" in codes
        assert "es" in codes
        assert "it" in codes

    def test_returns_five_codes(self):
        """Test exactly five codes are returned."""
        assert len(SupportedLanguage.all_codes()) == 5


class TestLanguageRules:
    """Tests for LanguageRules dataclass."""

    def test_default_rules(self):
        """Test default rules are sensible."""
        rules = LanguageRules()
        assert rules.space_before_punctuation == []
        assert "." in rules.no_space_before_punctuation
        assert "," in rules.no_space_before_punctuation
        assert rules.capitalize_after_sentence is True

    def test_french_rules_have_space_before_punctuation(self):
        """Test French rules require space before punctuation."""
        rules = LANGUAGE_RULES[SupportedLanguage.FRENCH]
        assert "?" in rules.space_before_punctuation
        assert "!" in rules.space_before_punctuation
        assert ":" in rules.space_before_punctuation
        assert ";" in rules.space_before_punctuation

    def test_english_rules_no_space_before_punctuation(self):
        """Test English rules have no space before punctuation."""
        rules = LANGUAGE_RULES[SupportedLanguage.ENGLISH]
        assert rules.space_before_punctuation == []

    def test_german_rules(self):
        """Test German-specific rules."""
        rules = LANGUAGE_RULES[SupportedLanguage.GERMAN]
        assert rules.opening_quote == "\u201e"  # German opening quote
        assert rules.closing_quote == "\u201c"  # German closing quote

    def test_spanish_rules(self):
        """Test Spanish-specific rules."""
        rules = LANGUAGE_RULES[SupportedLanguage.SPANISH]
        assert "pues" in rules.filler_words
        assert rules.opening_quote == "\u00ab"  # French-style quotes

    def test_italian_rules(self):
        """Test Italian-specific rules."""
        rules = LANGUAGE_RULES[SupportedLanguage.ITALIAN]
        assert rules.opening_quote == "\u00ab"  # French-style quotes


class TestGetLanguageRules:
    """Tests for get_language_rules function."""

    def test_get_french_rules(self):
        """Test getting French rules."""
        rules = get_language_rules("fr")
        assert "?" in rules.space_before_punctuation

    def test_get_english_rules(self):
        """Test getting English rules."""
        rules = get_language_rules("en")
        assert rules.space_before_punctuation == []

    def test_none_returns_english_default(self):
        """Test None input returns English rules as default."""
        rules = get_language_rules(None)
        assert rules == LANGUAGE_RULES[SupportedLanguage.ENGLISH]

    def test_unsupported_returns_english_default(self):
        """Test unsupported language returns English rules."""
        rules = get_language_rules("jp")
        assert rules == LANGUAGE_RULES[SupportedLanguage.ENGLISH]


class TestGetDisplayName:
    """Tests for get_display_name function."""

    def test_french_display_name(self):
        """Test French display name."""
        assert get_display_name("fr") == "French"

    def test_english_display_name(self):
        """Test English display name."""
        assert get_display_name("en") == "English"

    def test_german_display_name(self):
        """Test German display name."""
        assert get_display_name("de") == "German"

    def test_spanish_display_name(self):
        """Test Spanish display name."""
        assert get_display_name("es") == "Spanish"

    def test_italian_display_name(self):
        """Test Italian display name."""
        assert get_display_name("it") == "Italian"

    def test_uppercase_code(self):
        """Test uppercase code is handled."""
        assert get_display_name("FR") == "French"

    def test_unknown_returns_code(self):
        """Test unknown code returns the code itself."""
        assert get_display_name("xx") == "xx"
