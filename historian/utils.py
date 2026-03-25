"""Shared utility functions for historian."""

import os


def safe_name(s: str) -> str:
    """Sanitize a string that may contain surrogate escapes for safe printing."""
    return s.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')


def find_files(directory, extensions):
    """Recursively find files with given extensions."""
    lower_exts = [ext.lower() for ext in extensions]
    matching_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            if os.path.islink(full_path):
                continue
            if any(file.lower().endswith(ext) for ext in lower_exts):
                matching_files.append(full_path)
    return matching_files
