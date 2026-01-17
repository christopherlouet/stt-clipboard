# Language Support

STT Clipboard supports multiple languages for transcription and post-processing. Each language has specific typography rules and filler word removal.

## Supported Languages

| Language | Code | Status |
|----------|------|--------|
| French   | `fr` | Full support |
| English  | `en` | Full support |
| German   | `de` | Full support |
| Spanish  | `es` | Full support |
| Italian  | `it` | Full support |

## Language Configuration

### Auto-detection (Recommended)

Set `language: ""` (empty string) in your config to let Whisper auto-detect the language:

```yaml
transcription:
  language: ""  # Auto-detect
```

### Force Specific Language

If you primarily speak one language, you can force it for better accuracy:

```yaml
transcription:
  language: "fr"  # Always use French
```

## Typography Rules

Each language has specific typography rules applied during post-processing:

### French (`fr`)

- **Space before punctuation**: Space before `? ! : ;`
- **Quotes**: Uses guillemets `« »`
- **Filler words removed**: euh, euuh, euhh, hum, humm, hmmm, bah, ben

Example:
- Input: `"bonjour euh comment allez vous?"`
- Output: `"Bonjour comment allez vous ?"`

### English (`en`)

- **Space before punctuation**: No space before any punctuation
- **Quotes**: Uses straight quotes `" "`
- **Filler words removed**: uh, uhh, um, umm, hum, hmm, hmmm, like, you know

Example:
- Input: `"hello um how are you ?"`
- Output: `"Hello how are you?"`

### German (`de`)

- **Space before punctuation**: No space before any punctuation
- **Quotes**: Uses German quotes `„ "`
- **Filler words removed**: aeh, aehm, oehm, hm, hmm, also, ja

Example:
- Input: `"hallo aehm wie geht es dir ?"`
- Output: `"Hallo wie geht es dir?"`

### Spanish (`es`)

- **Space before punctuation**: No space before any punctuation
- **Quotes**: Uses guillemets `« »`
- **Filler words removed**: eh, ehh, um, umm, este, pues, bueno, o sea

Example:
- Input: `"hola pues como estas ?"`
- Output: `"Hola como estas?"`

### Italian (`it`)

- **Space before punctuation**: No space before any punctuation
- **Quotes**: Uses guillemets `« »`
- **Filler words removed**: eh, ehm, uhm, cioe, allora, praticamente, insomma

Example:
- Input: `"ciao allora come stai ?"`
- Output: `"Ciao come stai?"`

## Common Rules (All Languages)

These rules apply to all languages:

1. **Capitalization**: First letter of text and after `.`, `!`, `?` are capitalized
2. **No space before comma/period**: Spaces before `,` and `.` are removed
3. **Space after punctuation**: Ensures space after `,` and `.` when followed by a letter
4. **Multiple punctuation cleanup**: Consecutive `...` or `!!!` are reduced to single mark

## Adding New Languages

To add support for a new language:

1. Add the language to `SupportedLanguage` enum in `src/languages.py`
2. Define `LanguageRules` with:
   - `space_before_punctuation`: List of punctuation marks requiring space before
   - `filler_words`: Common speech artifacts to remove
   - `opening_quote` / `closing_quote`: Quotation mark style
3. Add to `LANGUAGE_RULES` dictionary
4. Add display name in `get_display_name()` function
5. Add tests in `tests/test_languages.py` and `tests/test_punctuation.py`

## Whisper Language Support

While STT Clipboard focuses on 5 languages with full post-processing, Whisper itself supports 99+ languages for transcription. Languages without custom rules will use English rules by default.

See [Whisper language list](https://github.com/openai/whisper#available-models-and-languages) for all supported languages.
