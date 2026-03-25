import sys


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        _print_help()
        sys.exit(0)

    command = sys.argv[1]
    sub_argv = sys.argv[2:]

    if command == 'sort':
        from .historian import sort_main
        sort_main([command] + sub_argv)
    elif command == 'compress':
        from .compress import compress_main
        compress_main([command] + sub_argv)
    else:
        print(f"Unknown command: {command}")
        _print_help()
        sys.exit(1)


def _print_help():
    print("historian - Media organization and compression toolkit.")
    print()
    print("Usage:")
    print("  historian sort <source> <dest>")
    print("  historian compress <folder>")
    print("  historian -h | --help")
    print()
    print("Commands:")
    print("  sort        Organize media files into date-sorted folders.")
    print("  compress    Recursively compress video files using H.265.")
