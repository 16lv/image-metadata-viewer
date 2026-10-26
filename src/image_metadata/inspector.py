from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image, UnidentifiedImageError

GPS_TAG_ID = 34853


@dataclass(frozen=True)
class ImageInspectionReport:
    file_path: str
    file_size_bytes: int
    format: str
    mode: str
    width: int
    height: int
    has_exif: bool
    exif_fields: dict[str, str]
    has_gps_info: bool
    gps_summary: dict[str, str]


def inspect_image(path: Path) -> ImageInspectionReport:
    """
    Opens a supported image file, extracts dimensions, format, file size,
    decoded EXIF tags, and any embedded GPS metadata dictionary without modifying the file.
    """
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")

    size_bytes = path.stat().st_size
    try:
        with Image.open(path) as img:
            img_format = img.format or "UNKNOWN"
            mode = img.mode
            width, height = img.size

            exif_data = img.getexif()
            exif_fields: dict[str, str] = {}
            gps_summary: dict[str, str] = {}

            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = str(ExifTags.TAGS.get(tag_id, tag_id))
                    if tag_id == GPS_TAG_ID:
                        continue
                    exif_fields[tag_name] = str(value)

                gps_ifd = exif_data.get_ifd(GPS_TAG_ID)
                if gps_ifd:
                    for gps_id, gps_val in gps_ifd.items():
                        gps_name = str(ExifTags.GPSTAGS.get(gps_id, gps_id))
                        gps_summary[gps_name] = str(gps_val)

            return ImageInspectionReport(
                file_path=str(path),
                file_size_bytes=size_bytes,
                format=img_format,
                mode=mode,
                width=width,
                height=height,
                has_exif=bool(exif_fields or gps_summary),
                exif_fields=exif_fields,
                has_gps_info=bool(gps_summary),
                gps_summary=gps_summary,
            )
    except UnidentifiedImageError as exc:
        raise ValueError(f"Unsupported or corrupt image file: {path}") from exc


def strip_metadata_to_copy(source_path: Path, output_path: Path) -> dict[str, Any]:
    """
    Writes a clean copy of the image to output_path with EXIF and ancillary metadata
    removed. Refuses to overwrite source_path to keep the original image intact by default.
    """
    if source_path.resolve() == output_path.resolve():
        raise ValueError(
            "output_path must be distinct from source_path to preserve the original image"
        )

    before = inspect_image(source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as img:
        clean_img = Image.new(img.mode, img.size)
        clean_img.paste(img)
        clean_img.save(output_path, format=img.format or "JPEG")

    after = inspect_image(output_path)
    return {
        "source_path": str(source_path),
        "output_path": str(output_path),
        "removed_exif_field_count": len(before.exif_fields),
        "removed_gps_data": before.has_gps_info,
        "output_has_exif": after.has_exif,
    }
