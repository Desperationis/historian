# Bug Fix Checklist — 3 Rounds Complete

## historian/historian.py

### Round 1 (Bug Hunt)
- [x] [HIGH] Fix cross-device rename fallback inner `while` loop silent failure — added `else: raise OSError(...)` after inner loop
- [x] [MEDIUM] Fix empty exiftool output passed to LLM as metadata — guard with `"(no metadata available)"` sentinel

### Round 1 (Stress Tests)
- [x] [HIGH] Fix UnicodeEncodeError in error handler for surrogate filenames — added `_safe_name()` helper for all user-facing prints
- [x] [MEDIUM] Fix ollama connection failure not caught — added connectivity check at start of `sort_main`
- [x] [LOW] Fix `run_linux_command` crash on non-UTF-8 subprocess output — added `errors='replace'`
- [x] [LOW] Remove debug print statements left in `get_a_date`

### Round 2 (Stress Tests)
- [x] [MEDIUM] Fix `move_file_to_sorted_folder` no collision counter — files with same name+date permanently stuck; added collision counter loop
- [x] [MEDIUM] Fix orphaned zero-byte placeholder on interrupt — combined into single try/except with cleanup

### Round 3 (Bug Hunt)
- [x] [HIGH] Fix `extract_date` regex failing on double-counter filenames — changed `(?:_\d+)?` to `(?:_\d+)*`
- [x] [HIGH] Fix `move_file_to_sorted_folder` renaming files already at destination — added `abspath` equality guard

### Round 3 (Stress Tests)
- [x] [MEDIUM] Fix LLM prompt injection via crafted filenames — delimited user strings with triple backticks + explicit instructions to treat as literal

## historian/compress.py

### Round 1 (Bug Hunt)
- [x] [MEDIUM] Fix signal handler PID reuse race — added `proc.poll() is None` guard before kill
- [x] [LOW] Fix `except OSError` too broad in `compress_file` setsid fallback — narrowed to `errno.EPERM`/`errno.ENOSYS`
- [x] [LOW] Fix `has_been_compressed` multi-line exiftool output — split on first newline before colon

### Round 1 (Stress Tests)
- [x] [MEDIUM] Fix `os.waitpid` blocking indefinitely in signal handler — changed to `os.WNOHANG`
- [x] [LOW] Fix stale `_setsid_ok` race — reordered assignments so `_setsid_ok` is set before `_current_compress_proc`

### Round 2 (Bug Hunt)
- [x] [HIGH] Fix surrogate filename crash in compress.py — added `_safe_name()` to all `escape()` calls

### Round 2 (Stress Tests)
- [x] [HIGH] Fix ffmpeg silently dropping extra audio/subtitle/data streams — added `-map 0`
- [x] [HIGH] Fix no timeout on exiftool subprocesses — added `timeout=60` to `communicate()`
- [x] [MEDIUM] Fix `shutil.copystat` failure discarding valid compressed file — wrapped in try/except
- [x] [MEDIUM] Fix concurrent file modification causing data loss — added pre/post stat comparison

### Round 3 (Bug Hunt)
- [x] [LOW] Fix non-signal-safe Rich `print()` in signal handler — replaced with `sys.stderr.write()`

### Round 3 (Stress Tests)
- [x] [MEDIUM] Fix predictable temp filename enabling symlink attack — switched to `tempfile.mkstemp()`

## historian/utils.py

### Round 2 (Bug Hunt)
- [x] [REFACTOR] Moved `safe_name()` to utils.py — shared between historian.py and compress.py

### Round 3 (Stress Tests)
- [x] [MEDIUM] Fix symlink following in `find_files` — skip symlinked files with `os.path.islink()`

## install.bash

### Round 1 (Bug Hunt)
- [x] [MEDIUM] Fix unquoted path expansions in generated launcher script — added double quotes

### Round 1 (Stress Tests)
- [x] [HIGH] Fix `ollama pull` failure aborting entire install — added `|| echo` fallback
- [x] [HIGH] Fix launcher hardcoding user-specific `uv` path — launcher now resolves `uv` dynamically at runtime

### Round 2 (Stress Tests)
- [x] [MEDIUM] Fix launcher failing under sudo — added install-time uv path as fallback
- [x] [LOW] Fix `cp` fallback not recursively excluding `.venv`/`.git` — changed to `find` commands

## install_requirements.bash

### Round 1 (Stress Tests)
- [x] [HIGH] Fix `ollama pull` failure aborting script — added `|| echo` fallback
- [x] [MEDIUM] Fix missing root guard — added `id -u` check matching `install.bash`
