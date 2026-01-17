#!/usr/bin/env python3
"""Property-based tests for punctuation module using hypothesis."""

import string

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.punctuation import PunctuationProcessor


class TestPunctuationProcessorProperties:
    """Property-based tests for PunctuationProcessor."""

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_process_never_returns_none_for_non_none_input(self, text: str):
        """Property: process() never returns None for non-None input."""
        processor = PunctuationProcessor()
        result = processor.process(text, detected_language="en")
        assert result is not None

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_process_preserves_alphanumeric_content(self, text: str):
        """Property: alphanumeric characters are preserved."""
        # Filter to text with at least one alphanumeric character
        assume(any(c.isalnum() for c in text))

        processor = PunctuationProcessor()
        result = processor.process(text, detected_language="en")

        # Extract alphanumeric chars from input and output
        input_alnum = "".join(c.lower() for c in text if c.isalnum())
        output_alnum = "".join(c.lower() for c in result if c.isalnum())

        assert input_alnum == output_alnum

    @given(st.text(alphabet=string.ascii_letters + " ", min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_no_double_spaces_after_processing(self, text: str):
        """Property: no double spaces in output."""
        processor = PunctuationProcessor()
        result = processor.process(text, detected_language="en")

        assert "  " not in result

    @given(st.text(alphabet=string.ascii_letters + " .!?", min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_sentences_start_with_capital_after_processing(self, text: str):
        """Property: sentences start with capital letter after processing."""
        # Skip empty or whitespace-only texts
        assume(text.strip())
        assume(any(c.isalpha() for c in text))

        processor = PunctuationProcessor()
        result = processor.process(text, detected_language="en")

        # Check if result starts with a letter
        stripped = result.lstrip()
        if stripped and stripped[0].isalpha():
            assert stripped[0].isupper(), f"Expected capital start, got: {result!r}"

    @given(st.sampled_from(["en", "fr"]))
    @settings(max_examples=10)
    def test_empty_input_returns_empty(self, language: str):
        """Property: empty string returns empty string."""
        processor = PunctuationProcessor()
        result = processor.process("", detected_language=language)
        assert result == ""

    @given(st.text(alphabet=" \t\n", min_size=1, max_size=10))
    @settings(max_examples=20)
    def test_whitespace_only_returns_whitespace(self, text: str):
        """Property: whitespace-only input returns the input."""
        processor = PunctuationProcessor()
        result = processor.process(text, detected_language="en")
        # Whitespace-only input is returned as-is by the processor
        assert result == text


class TestFrenchPunctuationProperties:
    """Property-based tests for French punctuation rules."""

    @given(st.text(alphabet=string.ascii_letters + " ", min_size=1, max_size=30))
    @settings(max_examples=50)
    def test_french_spacing_adds_space_before_punctuation(self, text: str):
        """Property: French text has space before ? ! : ;"""
        assume(text.strip())

        processor = PunctuationProcessor(enable_french_spacing=True)

        # Add punctuation to test
        test_text = text.strip() + "?"
        result = processor.process(test_text, detected_language="fr")

        # Should have space before ?
        if "?" in result:
            idx = result.index("?")
            if idx > 0:
                assert result[idx - 1] == " ", f"Expected space before ?, got: {result!r}"

    @given(st.sampled_from(["?", "!", ":", ";"]))
    @settings(max_examples=20)
    def test_french_double_punctuation_with_word(self, punct: str):
        """Property: French double punctuation always has preceding space."""
        processor = PunctuationProcessor(enable_french_spacing=True)

        test_text = f"test{punct}"
        result = processor.process(test_text, detected_language="fr")

        # Find the punctuation and check for space before it
        if punct in result:
            idx = result.index(punct)
            if idx > 0:
                assert result[idx - 1] == " ", f"Expected space before {punct}, got: {result!r}"


class TestEnglishPunctuationProperties:
    """Property-based tests for English punctuation rules."""

    @given(st.text(alphabet=string.ascii_letters + " ", min_size=1, max_size=30))
    @settings(max_examples=50)
    def test_english_no_space_before_punctuation(self, text: str):
        """Property: English text has no space before . , ? !"""
        assume(text.strip())

        processor = PunctuationProcessor()

        # Add punctuation to test
        test_text = text.strip() + "."
        result = processor.process(test_text, detected_language="en")

        # Should NOT have space before .
        if "." in result:
            idx = result.index(".")
            if idx > 0:
                assert result[idx - 1] != " ", f"Unexpected space before ., got: {result!r}"

    @given(st.sampled_from([".", ",", "?", "!", ";"]))
    @settings(max_examples=25)
    def test_english_punctuation_attached_to_word(self, punct: str):
        """Property: English punctuation is attached to preceding word."""
        processor = PunctuationProcessor()

        test_text = f"word {punct}"  # Space before punct (should be removed)
        result = processor.process(test_text, detected_language="en")

        # The punctuation should be attached to the word
        if punct in result:
            idx = result.index(punct)
            if idx > 0:
                assert result[idx - 1] != " ", f"Space before {punct} in: {result!r}"


class TestPunctuationIdempotence:
    """Test idempotence properties of punctuation processing."""

    @given(st.text(alphabet=string.ascii_letters + " .!?,", min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_double_processing_is_stable(self, text: str):
        """Property: processing twice gives same result as processing once."""
        assume(text.strip())

        processor = PunctuationProcessor()

        result1 = processor.process(text, detected_language="en")
        result2 = processor.process(result1, detected_language="en")

        # Second processing should not change the result
        assert result1 == result2, f"Not idempotent: {result1!r} -> {result2!r}"


class TestPunctuationArtifactCleaning:
    """Property-based tests for artifact cleaning."""

    @given(st.sampled_from(["euh", "euuh", "hum", "humm", "hmmm"]))
    @settings(max_examples=10)
    def test_filler_words_are_removed(self, filler: str):
        """Property: common filler words are removed."""
        processor = PunctuationProcessor(clean_artifacts=True)

        test_text = f"Hello {filler} world"
        result = processor.process(test_text, detected_language="en")

        # Filler word should be removed (check case-insensitively)
        assert filler.lower() not in result.lower()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
