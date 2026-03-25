"""historian compress - Recursively compress video files using H.265.

Usage:
  historian compress <folder>
"""

import errno
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading

from docopt import docopt
from rich import print
from rich.markup import escape

from .utils import find_files, safe_name as _safe_name

COMPRESSED_COMMENT = "compressed"
FFMPEG_COMMAND = ["ffmpeg", "-y", "-i", None, "-map", "0", "-vcodec", "libx265", "-c:a", "copy", "-c:s", "copy", "-map_metadata", "0", "-crf", "24", None]

_lock = threading.RLock()
_current_compress_proc = None
_current_video_dst = None
_setsid_ok = False


def _handle_sigint(signum, frame):
    """Clean up partial files on interrupt."""
    with _lock:
        if _current_compress_proc is not None and _current_compress_proc.poll() is None:
            try:
                if _setsid_ok:
                    os.killpg(os.getpgid(_current_compress_proc.pid), signal.SIGKILL)
                else:
                    _current_compress_proc.kill()
                # Use os.waitpid with WNOHANG to avoid blocking on D-state processes
                try:
                    os.waitpid(_current_compress_proc.pid, os.WNOHANG)
                except ChildProcessError:
                    pass
            except (ProcessLookupError, OSError):
                pass
            try:
                if _current_video_dst and os.path.exists(_current_video_dst):
                    os.remove(_current_video_dst)
                    sys.stderr.write(f"Removed partially compressed {_current_video_dst}\n")
            except OSError:
                pass
    sys.exit(130)


def has_been_compressed(src) -> bool:
    """Check the Comment metadata tag to see if already compressed."""
    process = subprocess.Popen(
        ["exiftool", "-Comment", src],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, _ = process.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        return False
    raw_out = stdout.decode("utf-8", errors="replace")

    if len(raw_out) == 0:
        return False

    first_line = raw_out.strip().split("\n")[0]
    parts = first_line.split(":", 1)
    if len(parts) < 2:
        return False
    return parts[1].strip() == COMPRESSED_COMMENT


def mark_as_compressed(src) -> bool:
    """Write compression marker to file metadata. Returns True on success."""
    process = subprocess.Popen(
        ["exiftool", "-overwrite_original", f'-Comment={COMPRESSED_COMMENT}', src],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        process.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        print(f"[yellow]Warning: exiftool timed out marking {escape(_safe_name(src))} as compressed.[/yellow]")
        return False
    if process.returncode != 0:
        print(f"[yellow]Warning: failed to mark {escape(_safe_name(src))} as compressed.[/yellow]")
        return False
    return True


def compress_file(src, dst) -> int:
    """Run compression command. Returns the process return code."""
    global _current_video_dst
    global _current_compress_proc
    global _setsid_ok

    cmd = list(FFMPEG_COMMAND)
    cmd[3] = src
    cmd[-1] = dst

    try:
        with _lock:
            _current_video_dst = dst
            try:
                process = subprocess.Popen(cmd, preexec_fn=os.setsid, stdin=subprocess.DEVNULL)
                _setsid_ok = True
                _current_compress_proc = process
            except OSError as exc:
                if exc.errno not in (errno.EPERM, errno.ENOSYS):
                    raise
                process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL)
                _setsid_ok = False
                _current_compress_proc = process

        process.wait()
        with _lock:
            _current_video_dst = None
    finally:
        with _lock:
            _current_compress_proc = None
            _current_video_dst = None

    return process.returncode


def compress_main(argv=None):
    """Compress all video files in directory using H.265."""
    args = docopt(__doc__, argv=argv)
    directory = args["<folder>"]

    if not os.path.isdir(directory):
        print(f"[bold red]Error: '{escape(directory)}' is not a valid directory.[/bold red]")
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        print("[bold red]Error: ffmpeg is not installed. Install it with: sudo apt install ffmpeg[/bold red]")
        sys.exit(1)
    if not shutil.which("exiftool"):
        print("[bold red]Error: exiftool is not installed. Install it with: sudo apt install exiftool[/bold red]")
        sys.exit(1)

    previous_handler = signal.signal(signal.SIGINT, _handle_sigint)
    try:
        supported_extensions = [".mp4", ".mov"]
        supported_extensions += [ext.upper() for ext in supported_extensions]

        files = find_files(directory, supported_extensions)
        files = [f for f in files if not os.path.basename(f).startswith("tmp_compress_")]

        for file in files:
            tmp_path = None
            try:
                if has_been_compressed(file):
                    print(f"[bold green]{escape(_safe_name(file))} has already been compressed.[/bold green]")
                    continue

                og_stat = os.stat(file)
                og_size = og_stat.st_size
                if og_size == 0:
                    print(f"[bold cyan]{escape(_safe_name(file))} is empty, skipping.[/bold cyan]")
                    continue

                print(f"[cyan]{escape(_safe_name(file))} hasn't been compressed. Compressing...[/cyan]")

                _, ext = os.path.splitext(file)
                fd_tmp, tmp_path = tempfile.mkstemp(prefix='tmp_compress_', suffix=ext, dir=os.path.dirname(file))
                os.close(fd_tmp)
                returncode = compress_file(file, tmp_path)

                if returncode != 0:
                    print("[bold red]Compress failed.[/bold red]")
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    tmp_path = None
                    continue

                compressed_size = os.path.getsize(tmp_path)
                if compressed_size == 0:
                    print(f"[bold red]Compressed output is empty for {escape(_safe_name(file))}, keeping original.[/bold red]")
                    os.remove(tmp_path)
                    tmp_path = None
                    continue

                ratio = compressed_size / og_size

                if ratio > 0.8:
                    if not mark_as_compressed(file):
                        print(f"[yellow]Warning: could not mark {escape(_safe_name(file))} as already optimal; it will be re-checked next run.[/yellow]")
                    os.remove(tmp_path)
                    tmp_path = None
                    print(
                        f"[bold cyan]{escape(_safe_name(file))} is untouched, it's at optimal quality; "
                        f"Compressed version is {round(ratio * 100)}% the size.[/bold cyan]"
                    )
                    continue

                if not mark_as_compressed(tmp_path):
                    print(f"[yellow]Could not mark as compressed, keeping original to avoid re-compression loop.[/yellow]")
                    os.remove(tmp_path)
                    tmp_path = None
                    continue
                # Check if file was modified during compression
                cur_stat = os.stat(file)
                if cur_stat.st_size != og_stat.st_size or cur_stat.st_mtime_ns != og_stat.st_mtime_ns:
                    print(f"[yellow]Warning: {escape(_safe_name(file))} was modified during compression, skipping replace.[/yellow]")
                    os.remove(tmp_path)
                    tmp_path = None
                    continue
                try:
                    shutil.copystat(file, tmp_path)
                except OSError as e:
                    print(f"[yellow]Warning: could not copy file attributes: {escape(str(e))}[/yellow]")
                os.replace(tmp_path, file)
                tmp_path = None
                print(
                    f"[bold green]{escape(_safe_name(file))} has been compressed. "
                    f"It's {round(ratio * 100)}% the size.[/bold green]"
                )
            except BaseException as e:
                if not isinstance(e, SystemExit):
                    print(f"[bold red]Error processing {escape(_safe_name(file))}: {escape(str(e))}[/bold red]")
                # Clean up any leftover temp file
                try:
                    if tmp_path and os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except OSError:
                    pass
                if isinstance(e, (SystemExit, KeyboardInterrupt)):
                    raise
                continue
    finally:
        signal.signal(signal.SIGINT, previous_handler)
