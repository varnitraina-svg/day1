#!/usr/bin/env python3
"""Command-line tool to scan a folder and generate a summary report."""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime


def format_size(size_bytes):
    """Convert bytes to a human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def scan_folder(folder_path, filter_extensions=None):
    """Scan all files in the folder and return summary data."""
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    total_files = 0
    total_size = 0
    largest_file = None
    largest_size = 0
    file_types = defaultdict(lambda: {"count": 0, "size": 0})

    total_subfolders = 0

    for dirpath, dirnames, filenames in os.walk(folder_path):
        total_subfolders += len(dirnames)
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(filepath)
            except OSError:
                continue

            ext = os.path.splitext(filename)[1].lower()
            if filter_extensions and ext not in filter_extensions:
                continue

            total_files += 1
            total_size += size

            rel_path = os.path.relpath(filepath, folder_path)
            if size > largest_size:
                largest_size = size
                largest_file = rel_path

            if not ext:
                ext = "(no extension)"
            file_types[ext]["count"] += 1
            file_types[ext]["size"] += size

    return {
        "filter": filter_extensions,
        "folder": os.path.abspath(folder_path),
        "total_subfolders": total_subfolders,
        "total_files": total_files,
        "total_size": total_size,
        "largest_file": largest_file,
        "largest_size": largest_size,
        "file_types": dict(file_types),
    }


def build_report(data):
    """Build the report string from scan data."""
    lines = []
    lines.append("=" * 60)
    lines.append("FOLDER SCAN REPORT")
    lines.append("=" * 60)
    lines.append(f"Folder:        {data['folder']}")
    lines.append(f"Scanned at:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if data["filter"]:
        lines.append(f"Filter:        {', '.join(sorted(data['filter']))}")
    lines.append("-" * 60)
    lines.append(f"Subfolders:    {data['total_subfolders']}")
    lines.append(f"Total files:   {data['total_files']}")
    lines.append(f"Total size:    {format_size(data['total_size'])}")

    if data["largest_file"]:
        lines.append(
            f"Largest file:  {data['largest_file']} ({format_size(data['largest_size'])})"
        )
    else:
        lines.append("Largest file:  (none — folder has no files)")

    lines.append("-" * 60)
    lines.append("FILE TYPES BREAKDOWN")
    lines.append(f"  {'Extension':<20} {'Count':>6}   {'Size':>12}")
    lines.append(f"  {'-'*20} {'-'*6}   {'-'*12}")

    sorted_types = sorted(
        data["file_types"].items(), key=lambda x: x[1]["size"], reverse=True
    )
    for ext, info in sorted_types:
        lines.append(
            f"  {ext:<20} {info['count']:>6}   {format_size(info['size']):>12}"
        )

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Scan a folder and generate a file summary report."
    )
    parser.add_argument("folder", help="Path to the folder to scan")
    parser.add_argument(
        "-o",
        "--output",
        default="folder_report.txt",
        help="Output report file path (default: folder_report.txt)",
    )
    parser.add_argument(
        "--ext",
        nargs="+",
        help="Filter by file extensions (e.g., --ext .py .txt .json)",
    )
    args = parser.parse_args()

    filter_extensions = None
    if args.ext:
        filter_extensions = {e if e.startswith(".") else f".{e}" for e in args.ext}

    data = scan_folder(args.folder, filter_extensions)
    report = build_report(data)

    print(report)

    with open(args.output, "w") as f:
        f.write(report + "\n")

    print(f"\nReport saved to: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
