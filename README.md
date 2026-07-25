# Photo EXIF Renamer (JPG & ARW)

A Python tool designed to standardize photo filenames (`.jpg`, `.jpeg`, `.arw`) according to their EXIF creation date metadata into the format:

`YYYY-MM-DD-unixtimestamp.<ext>`

Example: `DSC01234.ARW` ➔ `2024-05-15-1715788800.arw`

---

## Features

- **EXIF Extraction**: Reads `DateTimeOriginal`, `DateTimeDigitized`, or `DateTime` tags from JPEG and Sony RAW (`.ARW`) image headers.
- **Timestamp Fallback**: Falls back gracefully to file creation/modification date if EXIF metadata is missing.
- **Collision Protection**: Automatically appends `_1`, `_2`, etc., if multiple photos were shot during the exact same second timestamp.
- **Dry-Run Mode**: Preview proposed file name changes safely before modifying files.
- **Recursive Scan**: Option to scan subdirectories (`-r`).
- **GUI & CLI Support**: Run from command line or launch the graphical user interface.

---

## Quick Start

### 1. Command Line Interface (CLI)

```bash
# Preview changes in current folder (Dry Run)
python renamer.py -n

# Rename photos in a specific folder
python renamer.py "C:\Users\Username\Pictures\Photos"

# Recursively rename photos in folder and subfolders
python renamer.py "C:\Users\Username\Pictures\Photos" -r
```

#### CLI Options:
| Flag | Description |
|---|---|
| `directory` | Target directory path (default is `.`) |
| `-n`, `--dry-run` | Preview renaming actions without renaming any files |
| `-r`, `--recursive` | Process subdirectories recursively |
| `-v`, `--verbose` | Show detailed output for skipped files |

---

## 2. Graphical User Interface (GUI)

Launch the desktop GUI app:

```bash
python gui.py
```

- Select your photo folder using **Browse...**
- Toggle **Dry Run** preview or **Include Subdirectories**
- Click **Preview (Dry Run)** to see proposed name changes, or **Execute Rename** to perform actual renaming.

---

## Requirements

Python 3.10+ with standard dependencies (`exifread` and `Pillow`).

Run tests:
```bash
python test_renamer.py
```
