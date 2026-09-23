"""Regression tests for PDF document header logo resolution."""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.platypus import Image, Spacer, Table

from app.pdf.pdf_company import CompanyProfile
from app.pdf.pdf_header import build_header
from app.pdf.pdf_images import (
    bundled_logo_path,
    heal_logo_path,
    pdf_image,
    resolve_pdf_logo_path,
)
from app.utils.flags import parse_bool


def _tiny_png(path: Path) -> Path:
    """Write a small valid PNG that ReportLab can load."""
    from PIL import Image as PILImage
    from PIL import ImageDraw

    path.parent.mkdir(parents=True, exist_ok=True)
    img = PILImage.new("RGB", (120, 48), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((4, 4, 116, 44), fill=(5, 150, 105))
    draw.rectangle((20, 14, 100, 34), fill=(15, 23, 42))
    img.save(path, format="PNG")
    return path


def _header_body_table(company, options):
    header = build_header(company, options)
    return next(f for f in header if isinstance(f, Table) and len(f._cellvalues[0]) == 2)


def _header_logo_cell(company, options):
    cell = _header_body_table(company, options)._cellvalues[0][0]
    # Logo may be wrapped with the brand tagline in a nested table.
    if isinstance(cell, Table):
        inner = cell._cellvalues[0][0]
        return inner
    return cell


def _header_logo_image(company, options):
    cell = _header_logo_cell(company, options)
    if isinstance(cell, Image):
        return cell
    if isinstance(cell, Table):
        return cell._cellvalues[0][0]
    return cell


def test_company_info_block_is_right_aligned(tmp_path):
    from reportlab.lib.enums import TA_RIGHT

    logo = _tiny_png(tmp_path / "company.png")
    company = CompanyProfile(
        name="JU-TAN studio, Tanja Hrup s.p.",
        address="Turšičeva ulica 7",
        postal_code="1380",
        city="Cerknica",
        country="Slovenija",
        phone="+386 69 983 936",
        email="info@ju-tan.com",
        tax_number="17113130",
        registration_number="7575556000",
        iban="SI56 0237 9205 8132 832",
        bank="Nlb d.o.o.",
        logo=str(logo),
    )
    body = _header_body_table(company, {"show_logo": True})
    logo_cell, info_cell = body._cellStyles[0]
    assert logo_cell.alignment == "LEFT"
    assert info_cell.alignment == "RIGHT"
    info_block = body._cellvalues[0][1]
    assert isinstance(info_block, Table)
    assert all(cs.alignment == "RIGHT" for row in info_block._cellStyles for cs in row)
    for row in info_block._cellvalues:
        cell = row[0]
        if hasattr(cell, "style") and hasattr(cell.style, "alignment"):
            assert cell.style.alignment == TA_RIGHT


def test_parse_bool_rejects_false_strings():
    assert parse_bool("false", default=True) is False
    assert parse_bool("FALSE") is False
    assert parse_bool("ne") is False
    assert parse_bool("0") is False
    assert parse_bool(0) is False
    assert parse_bool(False) is False
    assert parse_bool("true") is True
    assert parse_bool("DA") is True
    assert parse_bool(1) is True
    assert parse_bool(True) is True
    assert parse_bool(None, default=True) is True
    assert parse_bool("", default=False) is False
    # The classic pitfall — must NOT treat non-empty "false" as True.
    assert bool("false") is True
    assert parse_bool("false") is False


def test_valid_company_logo_used_in_header(tmp_path):
    logo = _tiny_png(tmp_path / "company.png")
    company = CompanyProfile(name="Test", logo=str(logo))
    cell = _header_logo_image(company, {"show_logo": True})
    assert isinstance(cell, Image)
    assert cell.imageWidth > 1
    assert cell.imageHeight > 1
    assert cell.drawWidth > 0
    assert cell.drawHeight > 0
    assert Path(cell.filename).resolve() == logo.resolve()


def test_missing_company_logo_uses_bundled_fallback():
    bundled = bundled_logo_path()
    assert bundled is not None and bundled.is_file()
    company = CompanyProfile(name="Test", logo="")
    cell = _header_logo_image(company, {"show_logo": True})
    assert isinstance(cell, Image)
    assert Path(cell.filename).resolve() == bundled.resolve()
    # Bundled fallback must be the full horizontal mark (wide aspect).
    assert cell.imageWidth > cell.imageHeight


def test_stale_absolute_path_recovers_from_branding(tmp_path, monkeypatch):
    import app.pdf.pdf_images as images

    data = tmp_path / "data"
    branding = data / "branding"
    archived = _tiny_png(branding / "company_logo.png")
    monkeypatch.setattr(images, "DATA_DIR", data)

    stale = r"C:\OldInstall\JU-TAN Office\Data\branding\company_logo.png"
    assert not Path(stale).exists()
    healed = heal_logo_path(stale)
    assert Path(healed).resolve() == archived.resolve()

    resolved = resolve_pdf_logo_path(stale)
    assert resolved is not None
    assert resolved.resolve() == archived.resolve()

    company = CompanyProfile(name="Test", logo=stale)
    # heal happens in load_company; header also resolves via resolve_pdf_logo_path
    cell = _header_logo_image(company, {"show_logo": True})
    assert isinstance(cell, Image)
    assert Path(cell.filename).resolve() == archived.resolve()


def test_show_logo_false_places_spacer_not_image(tmp_path):
    logo = _tiny_png(tmp_path / "company.png")
    company = CompanyProfile(name="Test", logo=str(logo))
    cell = _header_logo_cell(company, {"show_logo": False})
    assert isinstance(cell, Spacer)
    assert not isinstance(cell, Image)


def test_show_logo_true_places_image(tmp_path):
    logo = _tiny_png(tmp_path / "company.png")
    company = CompanyProfile(name="Test", logo=str(logo))
    for truthy in (True, "true", "DA", 1, "1"):
        cell = _header_logo_image(company, {"show_logo": truthy})
        assert isinstance(cell, Image), f"failed for {truthy!r}"


def test_pdf_image_resources_logo_succeeds():
    image = pdf_image("resources/logo.png", 48, 22)
    assert image is not None
    assert image.imageWidth > 1
    assert image.imageHeight > 1
    assert image.drawWidth > 0
    assert image.drawHeight > 0
    assert getattr(image, "hAlign", None) == "LEFT"


def test_load_pdf_options_exposes_show_logo(monkeypatch):
    from app.modules.settings import settings_controller as sc
    from app.pdf import pdf_company

    extras = sc.default_settings()
    extras["pdf"]["logo"] = True

    monkeypatch.setattr(
        pdf_company.SettingsController,
        "load_extras",
        lambda self: extras,
    )
    monkeypatch.setattr(
        pdf_company,
        "load_company",
        lambda: CompanyProfile(name="X"),
    )
    options = pdf_company.load_pdf_options()
    assert "show_logo" in options
    assert options["show_logo"] is True

    extras["pdf"]["logo"] = "false"
    options = pdf_company.load_pdf_options()
    assert options["show_logo"] is False
