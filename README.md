# Photo EXIF Renamer (JPG & ARW)

A Python command-line tool designed to standardize photo filenames (`.jpg`, `.jpeg`, `.arw`) according to their EXIF creation date metadata into the format:

`YYYY-MM-DD-unixtimestamp.<ext>`

Example: `DSC01234.ARW` ➔ `2024-05-15-1715788800.arw`

---

## Features

- **EXIF Extraction**: Reads `DateTimeOriginal`, `DateTimeDigitized`, or `DateTime` tags from JPEG and Sony RAW (`.ARW`) image headers.
- **Burst Sequence Grouping**: Reads EXIF MakerNote continuous shooting metadata to group burst photos under the earliest image's base timestamp (`_b01`, `_b02`, etc.).
- **Timestamp Fallback**: Falls back gracefully to file creation/modification date if EXIF metadata is missing.
- **Collision Protection**: Automatically appends `_1`, `_2`, etc., if multiple photos share the exact same Unix timestamp.
- **Dry-Run Mode**: Preview proposed file name changes safely before modifying files.
- **Output Directory Option**: Option to copy renamed files to a target destination folder without modifying source photos.
- **Recursive Scan**: Option to scan subdirectories (`-r`).

---

## Usage

```bash
# Preview changes in current folder (Dry Run)
python renamer.py -n

# Rename photos in a specific folder
python renamer.py "C:\Users\Username\Pictures\Photos"

# Copy renamed photos to an output folder (keeps original photos untouched)
python renamer.py "C:\Users\Username\Pictures\Photos" -o "C:\Users\Username\Pictures\Renamed"

# Recursively process photos in folder and subfolders
python renamer.py "C:\Users\Username\Pictures\Photos" -r
```

### Command Line Options:
| Flag | Description |
|---|---|
| `directory` | Target directory path (default is `.`) |
| `-o`, `--output-dir` | Target output directory (copies files instead of in-place rename) |
| `-n`, `--dry-run` | Preview renaming actions without renaming any files |
| `-r`, `--recursive` | Process subdirectories recursively |
| `-v`, `--verbose` | Show detailed output for skipped files |

---

## Requirements

Python 3.10+ with standard dependencies (`exifread` and `Pillow`).

Run automated unit tests:
```bash
python test_renamer.py
```
