#!/usr/bin/env python3
"""
Test script for renamer.py
Tests single photo renaming as well as multi-second burst EXIF grouping.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from PIL import Image

from renamer import PhotoInfo, group_burst_photos, process_renaming

class TestPhotoRenamer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="renamer_test_"))
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_sample_jpg(self, filename: str, date_str: str | None = None) -> Path:
        """Create a minimal JPG image with optional EXIF DateTimeOriginal."""
        filepath = self.test_dir / filename
        img = Image.new("RGB", (100, 100), color="blue")
        
        if date_str:
            exif = img.getexif()
            exif[36867] = date_str  # DateTimeOriginal
            exif[306] = date_str    # DateTime
            img.save(filepath, exif=exif)
        else:
            img.save(filepath)
            
        return filepath

    def test_burst_grouping_multi_second(self):
        # Simulate burst sequence 1..3 spanning across 2 seconds
        p1 = PhotoInfo(self.create_sample_jpg("DSC0001.JPG", "2025:11:27 11:15:20"))
        p1.release_mode = "Continuous"
        p1.sequence_number = 1
        p1.is_burst = True

        p2 = PhotoInfo(self.create_sample_jpg("DSC0002.JPG", "2025:11:27 11:15:20"))
        p2.release_mode = "Continuous"
        p2.sequence_number = 2
        p2.is_burst = True

        p3 = PhotoInfo(self.create_sample_jpg("DSC0003.JPG", "2025:11:27 11:15:21"))
        p3.release_mode = "Continuous"
        p3.sequence_number = 3
        p3.is_burst = True

        plan = group_burst_photos([p1, p2, p3])
        
        # Verify all 3 photos inherit earliest base timestamp (11:15:20 -> 1764270920)
        dt_start = datetime(2025, 11, 27, 11, 15, 20)
        expected_ts = int(dt_start.timestamp())

        self.assertEqual(plan[0][1], f"2025-11-27-{expected_ts}_b01.jpg")
        self.assertEqual(plan[1][1], f"2025-11-27-{expected_ts}_b02.jpg")
        self.assertEqual(plan[2][1], f"2025-11-27-{expected_ts}_b03.jpg")

    def test_actual_renaming(self):
        date_str = "2024:01:01 10:00:00"
        jpg_path = self.create_sample_jpg("DSC_0002.JPG", date_str)
        dt = datetime(2024, 1, 1, 10, 0, 0)
        expected_name = f"2024-01-01-{int(dt.timestamp())}.jpg"
        
        process_renaming(self.test_dir, dry_run=False)
        
        self.assertFalse(jpg_path.exists())
        self.assertTrue((self.test_dir / expected_name).exists())

if __name__ == "__main__":
    unittest.main()
