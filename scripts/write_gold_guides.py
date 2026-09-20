"""Iz USER_GUIDE.md in ADMIN_GUIDE.md naredi PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def _pdf(source: Path, dest: Path) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(dest),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=source.stem,
        author="JU-TAN Studio",
    )
    story = []
    for line in source.read_text(encoding="utf-8").splitlines():
        text = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        if text.startswith("# "):
            story.append(Paragraph(text[2:], styles["Title"]))
        elif text.startswith("## "):
            story.append(Paragraph(text[3:], styles["Heading2"]))
        elif text.startswith("|") or text.startswith("```") or text.startswith("---"):
            story.append(Paragraph(f"<font face='Courier' size='8'>{text}</font>", styles["Code"]))
        elif text.strip():
            story.append(Paragraph(text, styles["BodyText"]))
        story.append(Spacer(1, 4))
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)


def main() -> None:
    _pdf(DOCS / "USER_GUIDE.md", DOCS / "USER_GUIDE.pdf")
    _pdf(DOCS / "ADMIN_GUIDE.md", DOCS / "ADMIN_GUIDE.pdf")
    print("Guides written.")


if __name__ == "__main__":
    main()
