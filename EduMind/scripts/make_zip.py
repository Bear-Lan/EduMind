"""
EduMind V1.0 Package Automation Script
Zips the project clean directory while excluding large binary virtual environments (venv, node_modules).
"""

import os
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = PROJECT_DIR.parent / "EduMind_V1.0_Release.zip"

EXCLUDE_DIRS = {
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".idea",
    ".vscode",
    "dist"
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".log",
    ".tmp"
}

def create_project_zip():
    print(f"==================================================")
    print(f"Creating EduMind V1.0 Release Archive...")
    print(f"Project Folder: {PROJECT_DIR}")
    print(f"Target Archive: {OUTPUT_ZIP}")
    print(f"==================================================")

    count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in EXCLUDE_EXTENSIONS:
                    continue

                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(PROJECT_DIR.parent)
                
                try:
                    zipf.write(abs_path, rel_path)
                    count += 1
                except PermissionError:
                    print(f"[SKIP] File locked by running process: {file}")
                except Exception as e:
                    print(f"[WARNING] Could not zip {file}: {e}")

    file_size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"==================================================")
    print(f"✓ Archive created successfully!")
    print(f"✓ Total files included: {count}")
    print(f"✓ Archive Size: {file_size_mb:.2f} MB")
    print(f"Archive Path: {OUTPUT_ZIP}")
    print(f"==================================================")

if __name__ == "__main__":
    create_project_zip()
