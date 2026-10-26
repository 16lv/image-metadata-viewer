from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.image_metadata.inspector import inspect_image, strip_metadata_to_copy


def test_inspect_and_strip_exif_metadata_preserves_original_file(tmp_path: Path) -> None:
    img_path = tmp_path / "sample_with_exif.jpg"
    clean_path = tmp_path / "sample_cleaned.jpg"

    img = Image.new("RGB", (64, 48), color=(30, 60, 90))
    exif = img.getexif()
    exif[271] = "CardiffTestCamera"  # Make
    exif[272] = "Model-X1"  # Model
    exif[305] = "shss7-test-suite"  # Software
    img.save(img_path, format="JPEG", exif=exif.tobytes())

    report = inspect_image(img_path)
    assert report.width == 64
    assert report.height == 48
    assert report.format == "JPEG"
    assert report.has_exif is True
    assert report.exif_fields.get("Make") == "CardiffTestCamera"
    assert report.exif_fields.get("Model") == "Model-X1"

    summary = strip_metadata_to_copy(img_path, clean_path)
    assert summary["removed_exif_field_count"] >= 3
    assert summary["output_has_exif"] is False

    # Verify original image still has its EXIF metadata intact
    original_after = inspect_image(img_path)
    assert original_after.has_exif is True

    # Verify cleaned copy has no EXIF metadata
    cleaned_report = inspect_image(clean_path)
    assert cleaned_report.has_exif is False
    assert cleaned_report.exif_fields == {}


def test_inspect_image_without_exif_and_reject_corrupt_files(tmp_path: Path) -> None:
    png_path = tmp_path / "plain.png"
    Image.new("RGB", (32, 32), color=(10, 20, 30)).save(png_path, format="PNG")

    rep = inspect_image(png_path)
    assert rep.format == "PNG"
    assert rep.has_exif is False
    assert rep.has_gps_info is False

    corrupt = tmp_path / "corrupt.jpg"
    corrupt.write_bytes(b"not-a-valid-image-header")
    with pytest.raises(ValueError, match="Unsupported or corrupt image file"):
        inspect_image(corrupt)

    with pytest.raises(ValueError, match="output_path must be distinct"):
        strip_metadata_to_copy(png_path, png_path)
