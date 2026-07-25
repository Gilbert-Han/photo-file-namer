#!/usr/bin/env python3
"""
Photo Renamer Tool
------------------
High-performance multithreaded tool to rename or copy JPG and Sony RAW (.ARW) photos
based on EXIF metadata creation timestamp and Sony burst sequence detection.

Output formats:
- Single photos: YYYY-MM-DD-unixtimestamp.<ext>
- Burst photos: YYYY-MM-DD-unixtimestamp_b01.<ext>, YYYY-MM-DD-unixtimestamp_b02.<ext>
"""

import os
import sys
import time
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import exifread
from PIL import Image

# Suppress exifread warnings/corrupted tag log noise
logging.getLogger("exifread").setLevel(logging.ERROR)

VALID_EXTENSIONS = {".jpg", ".jpeg", ".arw"}

class PhotoInfo:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.dt: datetime = datetime.fromtimestamp(filepath.stat().st_mtime)
        self.source: str = "File mtime (Fallback)"
        self.release_mode: str = ""
        self.sequence_number: int | None = None
        self.is_burst: bool = False
        
        self._extract_metadata()

    def _extract_metadata(self):
        """Extract EXIF datetime, release mode, and sequence number via fast seeking."""
        try:
            with open(self.filepath, "rb") as f:
                # Silence C-level warnings from exifread parser
                old_stderr = sys.stderr
                sys.stderr = open(os.devnull, "w")
                try:
                    # Use details=False for 220x faster EXIF seeking
                    tags = exifread.process_file(f, details=False, stop_tag="EXIF DateTimeOriginal")
                finally:
                    sys.stderr.close()
                    sys.stderr = old_stderr
                
                # Date extraction
                for tag in ["EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"]:
                    if tag in tags:
                        val = str(tags[tag]).strip()
                        try:
                            self.dt = datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
                            self.source = "EXIF (exifread)"
                            break
                        except ValueError:
                            pass
                
                # Release mode & Sequence Number
                if "MakerNote ReleaseMode" in tags:
                    self.release_mode = str(tags["MakerNote ReleaseMode"]).strip()
                    
                if "MakerNote SequenceNumber" in tags:
                    try:
                        self.sequence_number = int(str(tags["MakerNote SequenceNumber"]).strip())
                    except ValueError:
                        pass
        except Exception:
            pass

        # Fallback date via Pillow if exifread failed to parse date
        if self.source.startswith("File mtime"):
            try:
                with Image.open(self.filepath) as img:
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id in (36867, 36868, 306):
                            if tag_id in exif_data:
                                val = str(exif_data[tag_id]).strip()
                                try:
                                    self.dt = datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
                                    self.source = "EXIF (Pillow)"
                                    break
                                except ValueError:
                                    pass
            except Exception:
                pass

        if "Continuous" in self.release_mode or (self.sequence_number is not None and self.sequence_number > 0):
            self.is_burst = True

def group_burst_photos(photos: list[PhotoInfo], dest_dir: Path | None = None) -> list[tuple[PhotoInfo, str]]:
    """
    Groups burst photos and assigns target filenames.
    Multi-second bursts are all grouped to the earliest image's base timestamp.
    Checks destination disk to ensure pre-existing files are never overwritten.
    Returns list of (PhotoInfo, target_filename).
    """
    # Sort chronologically by datetime, sequence number, and filename
    sorted_photos = sorted(
        photos, 
        key=lambda p: (p.dt, p.sequence_number if p.sequence_number is not None else 0, p.filepath.name)
    )

    results: list[tuple[PhotoInfo, str]] = []
    
    # Process into burst groups
    i = 0
    n = len(sorted_photos)
    
    while i < n:
        photo = sorted_photos[i]
        
        # Check if this photo starts a burst sequence
        if photo.is_burst:
            burst_group: list[PhotoInfo] = []
            
            start_photo = photo
            burst_group.append(photo)
            i += 1
            
            while i < n:
                next_photo = sorted_photos[i]
                time_delta = (next_photo.dt - burst_group[-1].dt).total_seconds()
                
                # Same burst if explicitly continuous and sequence_number > 1 or captured within 2.5 seconds
                if next_photo.is_burst:
                    if next_photo.sequence_number is not None and next_photo.sequence_number == 1 and len(burst_group) > 1:
                        # New burst started
                        break
                    if time_delta <= 2.5:
                        burst_group.append(next_photo)
                        i += 1
                    else:
                        break
                else:
                    break
            
            # Base timestamp from the FIRST image in the burst
            base_dt = start_photo.dt
            date_prefix = base_dt.strftime("%Y-%m-%d")
            unix_ts = int(base_dt.timestamp())
            base_name = f"{date_prefix}-{unix_ts}"
            
            # Determine padding format (_b01 vs _b001)
            pad = 3 if len(burst_group) >= 100 else 2

            # Track frame indices for RAW+JPEG pairs sharing the same sequence index
            for idx, p in enumerate(burst_group, start=1):
                frame_num = p.sequence_number if p.sequence_number is not None else idx
                ext = p.filepath.suffix.lower()
                target_filename = f"{base_name}_b{frame_num:0{pad}d}{ext}"
                results.append((p, target_filename))
        else:
            # Single non-burst photo
            ext = photo.filepath.suffix.lower()
            date_prefix = photo.dt.strftime("%Y-%m-%d")
            unix_ts = int(photo.dt.timestamp())
            target_filename = f"{date_prefix}-{unix_ts}{ext}"
            results.append((photo, target_filename))
            i += 1

    # Collision check against assigned batch names AND existing disk files
    final_results: list[tuple[PhotoInfo, str]] = []
    used_names: set[str] = set()

    for photo, target in results:
        ext = photo.filepath.suffix.lower()
        candidate = target
        
        counter = 1
        stem = Path(target).stem
        target_folder = dest_dir if dest_dir else photo.filepath.parent
        
        def is_taken(name: str) -> bool:
            if name.lower() in used_names:
                return True
            check_path = target_folder / name
            if check_path.exists() and check_path.resolve() != photo.filepath.resolve():
                return True
            return False

        while is_taken(candidate):
            candidate = f"{stem}_{counter}{ext}"
            counter += 1
            
        used_names.add(candidate.lower())
        final_results.append((photo, candidate))

    return final_results

def process_renaming(
    directory: Path, 
    output_dir: Path | None = None,
    dry_run: bool = False, 
    recursive: bool = False, 
    verbose: bool = False
):
    """Scan directory and rename or copy valid JPG/ARW files using high-concurrency parallel workers."""
    start_time = time.time()

    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory '{directory}' does not exist or is not a directory.", file=sys.stderr)
        return

    pattern = "**/*" if recursive else "*"
    file_paths = [p for p in directory.glob(pattern) if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS]
    
    if not file_paths:
        print(f"No matching photo files ({', '.join(VALID_EXTENSIONS)}) found in '{directory}'.")
        return

    max_workers = min(128, max(32, (os.cpu_count() or 4) * 8))
    print(f"\nScanning EXIF metadata for {len(file_paths)} photo file(s) across {max_workers} parallel workers...")
    
    scan_start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        photos = list(executor.map(PhotoInfo, file_paths))
    scan_elapsed = time.time() - scan_start

    resolved_output_dir = Path(output_dir).resolve() if output_dir else None

    # Generate grouped target filenames with disk collision protection
    photo_plan = group_burst_photos(photos, dest_dir=resolved_output_dir)

    if resolved_output_dir:
        if not dry_run:
            resolved_output_dir.mkdir(parents=True, exist_ok=True)
        operation_mode = f"COPY to '{resolved_output_dir}'"
    else:
        operation_mode = "RENAME in-place"

    if dry_run:
        print(f"=== DRY RUN MODE (Preview {operation_mode}) ===\n")
    else:
        print(f"=== EXECUTING {operation_mode.upper()} ===\n")

    renamed_count = 0
    skipped_count = 0

    # Sort output log display by target filename
    for photo, target_filename in sorted(photo_plan, key=lambda pair: pair[1]):
        filepath = photo.filepath
        
        if resolved_output_dir:
            target_path = resolved_output_dir / target_filename
        else:
            target_path = filepath.parent / target_filename

        if not resolved_output_dir and filepath.name.lower() == target_filename.lower():
            if verbose:
                print(f"[SKIP] {filepath.name} is already correctly named.")
            skipped_count += 1
            continue

        action_label = "[DRY-RUN]" if dry_run else ("[COPY]" if resolved_output_dir else "[RENAME]")
        burst_info = f" (Burst Frame {photo.sequence_number})" if photo.sequence_number else ""
        print(f"{action_label} {filepath.name:45s} -> {target_filename} ({photo.source}{burst_info})")

        if not dry_run:
            try:
                if resolved_output_dir:
                    shutil.copy2(filepath, target_path)
                else:
                    filepath.rename(target_path)
                renamed_count += 1
            except Exception as e:
                print(f"  [ERROR] Could not process {filepath.name}: {e}", file=sys.stderr)
        else:
            renamed_count += 1

    total_elapsed = time.time() - start_time

    print("\nSummary:")
    print(f"  Total files evaluated: {len(file_paths)}")
    print(f"  Files {'proposed to process' if dry_run else ('copied' if resolved_output_dir else 'renamed')}: {renamed_count}")
    print(f"  Files skipped: {skipped_count}")
    print(f"  EXIF metadata scan time: {scan_elapsed:.3f} seconds ({len(file_paths)/scan_elapsed:.1f} files/sec)")
    print(f"  Total execution time: {total_elapsed:.3f} seconds ({len(file_paths)/total_elapsed:.1f} files/sec)")

def main():
    parser = argparse.ArgumentParser(
        description="Rename JPG and ARW photos based on EXIF metadata & burst grouping."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Path to folder containing photos (defaults to current directory)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=None,
        help="Output directory to save processed files (instead of renaming in-place)."
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Preview renaming actions without renaming any files."
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process subdirectories recursively."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output for skipped files."
    )

    args = parser.parse_args()
    target_dir = Path(args.directory).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    
    process_renaming(
        directory=target_dir,
        output_dir=output_dir,
        dry_run=args.dry_run,
        recursive=args.recursive,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()
