import os
import argparse
from dotenv import load_dotenv
from tqdm import tqdm
from faster_whisper import WhisperModel

from .io import write_txt, write_srt, write_vtt, write_words_json

def add_args(parser: argparse.ArgumentParser):
    parser.add_argument("input_path", help="Path to media file (audio/video).")
    parser.add_argument("--output_dir", default=None, help="Output directory (default: alongside input).")
    parser.add_argument("--model", default=os.getenv("MODEL_SIZE", "medium"),
                        help="tiny | base | small | medium | large-v3")
    parser.add_argument("--language", default=os.getenv("LANGUAGE", "ru"),
                        help='Language (e.g., "ru"). Empty string for auto-detect.')
    parser.add_argument("--device", default=os.getenv("DEVICE", "cpu"), help="cpu | cuda")
    parser.add_argument("--beam_size", type=int, default=int(os.getenv("BEAM_SIZE", "5")))
    parser.add_argument("--vad_filter", action="store_true" if os.getenv("VAD_FILTER","false").lower()=="true" else "store_false")
    parser.add_argument("--word_timestamps", action="store_true", help="Emit per-word timestamps and save JSON.")
    return parser

def run(args: argparse.Namespace):

    in_path = os.path.expanduser(os.path.expandvars(args.input_path))
    if not os.path.exists(in_path):
        raise FileNotFoundError(in_path)

    base = os.path.splitext(os.path.basename(in_path))[0]
    out_dir_arg = args.output_dir or ""
    out_dir = os.path.expanduser(os.path.expandvars(out_dir_arg)) or os.path.dirname(os.path.abspath(in_path)) or "."
    os.makedirs(out_dir, exist_ok=True)

    print(f"[i] Loading model '{args.model}' on {args.device} …")
    model = WhisperModel(args.model, device=args.device)

    print(f"[i] Transcribing: {in_path}")
    segments_iter, info = model.transcribe(
        in_path,
        language=None if args.language.strip()=="" else args.language,
        beam_size=args.beam_size,
        vad_filter=args.vad_filter,
        word_timestamps=args.word_timestamps,
    )

    # Progress bar based on audio duration, updated by segment end time
    total = max(1.0, float(getattr(info, "duration", 0.0)))
    pbar = tqdm(total=total, unit="s", desc="Transcribing", leave=True)

    segs = []
    last = 0.0
    for seg in segments_iter:
        segs.append(seg)
        # advance progress to this segment's end
        cur = min(total, float(seg.end or 0.0))
        if cur > last:
            pbar.update(cur - last)
            last = cur
    if last < total:
        pbar.update(total - last)
    pbar.close()

    out_txt = os.path.join(out_dir, f"{base}.txt")
    out_srt = os.path.join(out_dir, f"{base}.srt")
    out_vtt = os.path.join(out_dir, f"{base}.vtt")
    write_txt(segs, out_txt)
    write_srt(segs, out_srt)
    write_vtt(segs, out_vtt)

    if args.word_timestamps:
        out_json = os.path.join(out_dir, f"{base}.json")
        write_words_json(segs, out_json)
        print(f"[→] {out_json}")

    print(f"[✓] Done. Detected language: {getattr(info,'language', '?')} | Duration: {getattr(info,'duration', 0):.1f}s")
    print(f"[→] {out_txt}\n[→] {out_srt}\n[→] {out_vtt}")

