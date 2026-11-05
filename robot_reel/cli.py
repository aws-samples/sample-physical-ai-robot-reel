"""Command line entry point: `robot-reel lerobot SOURCE [options]`."""
import sys


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if args[:1] == ["lerobot"]:
        from .lerobot import main as lerobot_main
        return lerobot_main(args[1:])
    print("usage: robot-reel lerobot SOURCE [options]\nRun `robot-reel lerobot --help` for the options.", file=sys.stderr)
    return 2
