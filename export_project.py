"""
SatyaDrishti - Project ZIP Export Utility
Packages the entire project into a clean, standalone ZIP distribution file
excluding heavy temporary folders (node_modules, caches, logs).
"""

import os
import sys
import zipfile
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, "SatyaDrishti_Project_Distribution.zip")

EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".system_generated",
    ".vscode",
    ".idea"
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".log",
    ".tmp"
}

def export_zip(output_path=OUTPUT_ZIP):
    print("=" * 60)
    print("Packaging SatyaDrishti Project into Standalone ZIP Archive...")
    print("=" * 60)

    total_files = 0
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue
                if file.endswith(".zip"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)

                zipf.write(full_path, rel_path)
                total_files += 1

    zip_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[OK] Successfully archived {total_files} files.")
    print(f"[OK] Output ZIP created at: {output_path} ({zip_size_mb:.2f} MB)")
    print("=" * 60)
    return output_path

if __name__ == "__main__":
    export_zip()
