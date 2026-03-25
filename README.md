# historian

A media toolkit for organizing files into date-sorted folders and compressing videos.

## Commands

### `historian sort <source> <dest>`

Scans filenames and EXIF metadata using a local LLM (ollama) to extract dates, then moves files into a clean `YYYY_MM_month/` directory structure.

**Default model:** `dolphin-llama3` (requires ~8 GB VRAM)

#### Example

Given a messy folder:

```
my_folder/
    chinatown_2024/
        restaurant.png
        photo2.png
        recorded_2024_05.mp4
    20240508/
        IMG_2018_08_10.JPEG
    2022_04_12_29387462.jpg
    Screenshot of August 10th 2025.png
    VID_20240506_92837.MOV
```

Running `historian sort my_folder sorted/` produces:

```
sorted/
    2022_04_april/
        2022_04_12_d354a6759a82749d.jpg
    2024_05_may/
        2024_05_06_a3dfa327a7f729a9.mov
        2024_05_08_a01ba01a98d020e0.jpg
    2025_08_august/
        2025_08_10_198a9110a87e9020.png
```

Files that can't be dated are left untouched.

#### How It Works

For each media file in `<source>`:

1. **Filename check** — asks ollama whether the filename contains a date (year, month, day).
2. **EXIF fallback** — if the filename doesn't work, checks `exiftool` metadata.
3. **Skip** — if neither method finds a date, the file is left in place.

If a date is found, the file is renamed and moved to `<dest>`:

```
YYYY_MM_DD_<md5hash>.ext
```

The hash is derived from the original filename (without extension), so two files with the same name but different extensions get the same hash. Files already in this format are moved directly without re-analysis.

### `historian compress <folder>`

Recursively compresses video files (`.mp4`, `.mov`) using ffmpeg and H.265. Tracks which files have been processed via EXIF metadata so it's safe to run repeatedly.

- Only replaces the original if the compressed version is at least 20% smaller.
- Files already at optimal quality are marked and skipped on future runs.
- Safe to interrupt with Ctrl+C (partial files are cleaned up).

## Install

```bash
bash install.bash
```

This installs system deps (ffmpeg, exiftool), builds a Python venv via `uv`, copies the project to `/opt/historian`, and creates a global `historian` command. If ollama is installed it will also pull the `dolphin-llama3` model.

## Requirements

- Linux (Debian/Ubuntu)
- Python 3.11+
- ffmpeg (for compress)
- exiftool
- [ollama](https://ollama.com/download) with `dolphin-llama3` pulled (for sort)
- [uv](https://github.com/astral-sh/uv)

## Dev

```bash
bash install_requirements.bash          # deps only, no system install
uv run historian sort <source> <dest>   # sort from source
uv run historian compress <folder>      # compress from source
uv run pytest                           # tests
```

## Uninstall

```bash
sudo rm -rf /opt/historian /usr/local/bin/historian
```
