# MIGRATION

## compress -> historian (merged)

The `historian compress` subcommand was migrated from the standalone `compress` project.

- **Source:** `/home/adhoc/Desktop/compress/`
- **Repository:** https://github.com/Desperationis/compress
- **Author:** Diego Contreras
- **License:** MIT

### What was migrated

| Original file | Destination | Notes |
|---|---|---|
| `compress/compress.py` | `historian/compress.py` | All logic; SIGINT handler deferred to runtime; `command.txt` inlined as constant; `find_files()` moved to `utils.py` |
| `command.txt` | (inlined) | ffmpeg command is now the constant `FFMPEG_COMMAND` in `compress.py` |

### Changes from original

1. **CLI routing**: `compress <folder>` is now `historian compress <folder>`.
2. **command.txt eliminated**: The ffmpeg command template is a Python constant instead of a separate file. The original loaded it relative to CWD which was fragile.
3. **SIGINT handler**: No longer registered at module import time. Registered only during compress operations and restored afterward.
4. **Temp files**: Written to the source file's directory as `tmp_compress.<ext>` instead of CWD as `tmp.<ext>`.
5. **Shared `find_files()`**: Extracted to `historian/utils.py`, shared with the sort command.
6. **No new Python dependencies**: `rich` and `docopt` were already in historian's dependency list.
7. **System dependency**: `ffmpeg` added to `install.bash` and `install_requirements.bash`.
