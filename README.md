# Image Metadata Viewer & Scrubber (Python)

A Python utility built with **Pillow (PIL)** that inspects image dimensions, formats, file sizes, EXIF tags, and embedded GPS IFD blocks, and creates scrubbed copies with metadata removed.

## Overview

Photos taken on phones and digital cameras routinely embed device serial numbers, timestamps, software strings, and GPS coordinates in EXIF headers. `image-metadata-viewer` separates inspection from non-destructive scrubbing:
- **Inspection (`inspect_image`):** Reads image dimensions, colour mode, format, file size, decoded `ExifTags.TAGS`, and nested `GPSTAGS` (IFD `34853`) without treating missing EXIF blocks as an error.
- **Non-Destructive Metadata Removal (`strip_metadata_to_copy`):** Writes pixel data to a separate output file without copying EXIF or GPS blocks, and explicitly refuses to overwrite the source file path so original images are never lost by accident.

## Running Tests & Linter

```bash
ruff check .
pytest -v
```
