"""Tests for make_audiobook.extract_md_text."""

from pathlib import Path

from make_audiobook import extract_md_text


def test_extract_md_text_strips_markdown_markup(tmp_path: Path) -> None:
    md = tmp_path / "book.md"
    md.write_text(
        "# Title\n"
        "\n"
        "Some **bold** text and a [link](http://example.com).\n"
        "\n"
        "- item one\n"
        "- item two\n"
        "\n"
        "```python\n"
        "code fence content\n"
        "```\n"
        "\n"
        "> A quoted line\n"
        "\n"
        "Final `inline` paragraph.\n",
        encoding="utf-8",
    )

    result = extract_md_text(md)

    assert result == (
        "Title Some bold text and a link. item one item two "
        "A quoted line Final inline paragraph."
    )
    # No leftover markdown syntax.
    assert "#" not in result
    assert "*" not in result
    assert "`" not in result
    assert "code fence content" not in result
