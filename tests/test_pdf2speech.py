"""Tests for pdf2speech.extract_text against a small fixture PDF.

tests/fixtures/sample.pdf is a 2-page PDF (generated once with fpdf2, not a
runtime dependency) where page 1 ends with a hyphenated line break
("mod-\\nerate") and each page has a bare page number on its own final line,
so we can assert both the hyphen-rejoin and page-number-stripping behavior.
"""

from pathlib import Path

from pdf2speech import extract_text

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample.pdf"


def test_extract_text_rejoins_hyphens_and_strips_page_numbers() -> None:
    result = extract_text(FIXTURE)

    assert result == (
        "This is a moderate example sentence for testing. "
        "Second page content continues here."
    )
    assert "moderate" in result
    assert "mod-" not in result  # hyphenated line break was rejoined
    assert not any(ch.isdigit() for ch in result)  # page numbers stripped
    assert "  " not in result  # whitespace collapsed
    assert "\n" not in result
