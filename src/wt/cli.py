# src/wt/cli.py

import argparse, os
from dotenv import load_dotenv, find_dotenv

# Load .env no matter the CWD
load_dotenv(find_dotenv())

from . import transcribe as T


def main():
    parser = argparse.ArgumentParser(
        prog="wt", description="Whisper Transcriber toolkit"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- Transcribe ---
    p1 = sub.add_parser("transcribe", help="Transcribe media with Faster-Whisper")
    T.add_args(p1)

    # --- Diarize ---
    p2 = sub.add_parser("diarize", help="Diarize audio and merge with word timings")
    p2.add_argument("--output_dir", default=None)
    p2.add_argument("input_path")
    p2.add_argument("--hf_token", default=None)
    p2.add_argument("--num_speakers", type=int, default=None)
    p2.add_argument("--min_speakers", type=int, default=None)
    p2.add_argument("--max_speakers", type=int, default=None)

    args = parser.parse_args()

    if args.cmd == "transcribe":
        T.run(args)
    elif args.cmd == "diarize":
        from . import diarize as D

        # if not provided, fallback to env (thanks to load_dotenv())
        if not args.hf_token:
            args.hf_token = os.environ.get("HUGGINGFACE_TOKEN", "")
        D.run(args)


if __name__ == "__main__":
    main()
