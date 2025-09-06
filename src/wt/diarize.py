import os
import sys
import json
import subprocess
import argparse
from datetime import timedelta

import soundfile as sf  # ensures libsndfile present
from pyannote.audio import Pipeline

from .io import ts_srt

def extract_wav(input_path: str, wav_path: str):
    if os.path.exists(wav_path): return
    cmd = ["ffmpeg","-y","-i",input_path,"-ac","1","-ar","16000",wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def load_words_json(json_path: str):
    if not os.path.exists(json_path): return None
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            words.append({"text": w["word"], "start": w["start"], "end": w["end"]})
    return words or None

def diarize_audio(wav_path: str, token: str, *,
                  num_speakers=None, min_speakers=None, max_speakers=None):
    from pyannote.audio import Pipeline
    if not token:
        raise RuntimeError("Missing Hugging Face token. Export HUGGINGFACE_TOKEN or pass --hf_token.")

    try:
        pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
    except Exception as e:
        raise RuntimeError(
            "Could not load 'pyannote/speaker-diarization-3.1'. "
            "Accept terms and ensure token access:\n"
            "  https://huggingface.co/pyannote/speaker-diarization-3.1\n"
            "Also accept:\n"
            "  https://huggingface.co/pyannote/segmentation-3.0"
        ) from e

    # Decide strategy
    kwargs = {}
    if num_speakers is not None:
        # exact number takes precedence
        kwargs["num_speakers"] = int(num_speakers)
        print(f"[i] Diarization: locking to num_speakers={kwargs['num_speakers']}")
    elif (min_speakers is not None) or (max_speakers is not None):
        if (min_speakers is not None) and (max_speakers is not None) and (min_speakers > max_speakers):
            raise ValueError("min_speakers cannot be greater than max_speakers.")
        if min_speakers is not None:
            kwargs["min_speakers"] = int(min_speakers)
        if max_speakers is not None:
            kwargs["max_speakers"] = int(max_speakers)
        print(f"[i] Diarization: bounding speakers with {kwargs}")
    else:
        # auto-estimate (default)
        print("[i] Diarization: auto-estimating number of speakers")

    return pipe(wav_path, **kwargs)

def add_args(parser: argparse.ArgumentParser):
    parser.add_argument("input_path", help="Original media file (we'll extract WAV).")
    parser.add_argument("--hf_token", default=os.environ.get("HUGGINGFACE_TOKEN",""), help="Hugging Face token.")
    parser.add_argument("--num_speakers", type=int, default=None, help="Exact number of speakers (overrides min/max).")
    parser.add_argument("--min_speakers", type=int, default=None, help="Lower bound on speakers.")
    parser.add_argument("--max_speakers", type=int, default=None, help="Upper bound on speakers.")
    return parser

def run(args: argparse.Namespace):
    if not args.hf_token:
        args.hf_token = os.environ.get("HUGGINGFACE_TOKEN","")
    if not args.hf_token:
        raise RuntimeError("Set --hf_token or export HUGGINGFACE_TOKEN before running diarize.")

    # expand ~ and env vars
    in_path = os.path.expanduser(os.path.expandvars(args.input_path))
    if not os.path.exists(in_path):
        raise FileNotFoundError(in_path)

    folder = os.path.dirname(os.path.abspath(in_path)) or "."
    base = os.path.splitext(os.path.basename(in_path))[0]
    wav_path = os.path.join(folder, f"{base}.diar.wav")
    json_path = os.path.join(folder, f"{base}.json")
    out_srt = os.path.join(folder, f"{base}.diarized.srt")
    out_txt = os.path.join(folder, f"{base}.diarized.txt")

    extract_wav(in_path, wav_path)
    print("[i] Running diarization …")
    diar = diarize_audio(
        wav_path,
        args.hf_token,
        num_speakers=args.num_speakers,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
    )

    words = load_words_json(json_path)
    if not words:
        print("[!] No word-level JSON found. For best results, run transcribe with --word_timestamps.")

    chunks = chunks_from_words(words or [], diar)
    write_diarized_srt(chunks, out_srt)
    write_diarized_txt(chunks, out_txt)
    print(f"[✓] Diarization written:\n[→] {out_srt}\n[→] {out_txt}")

def chunks_from_words(words, diarization):
    chunks = []
    idx = 1
    for segment, _, label in diarization.itertracks(yield_label=True):
        s, e = segment.start, segment.end
        text = " ".join(w["text"] for w in words if w["start"] >= s and w["end"] <= e).strip()
        if not text: continue
        chunks.append({"idx": idx, "start": s, "end": e, "speaker": label.replace("SPEAKER_", "Speaker "), "text": text})
        idx += 1
    return chunks

def write_diarized_srt(chunks, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(f"{c['idx']}\n{ts_srt(c['start'])} --> {ts_srt(c['end'])}\n{c['speaker']}: {c['text']}\n\n")

def write_diarized_txt(chunks, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(f"{c['speaker']}: {c['text']}\n")

def add_args(parser):
    parser.add_argument("input_path", help="Original media file (we'll extract WAV).")
    parser.add_argument("--hf_token", default=os.environ.get("HUGGINGFACE_TOKEN",""), help="Hugging Face token.")
    parser.add_argument("--num_speakers", type=int, default=None)
    parser.add_argument("--min_speakers", type=int, default=None)
    parser.add_argument("--max_speakers", type=int, default=None)
    parser.add_argument("--output_dir", default=None, help="Where to write outputs (default: alongside input).")
    return parser

def run(args: argparse.Namespace):
    if not args.hf_token:
        sys.exit("Set --hf_token or export HUGGINGFACE_TOKEN")
    in_path = args.input_path
    if not os.path.exists(in_path):
        raise FileNotFoundError(in_path)
    out_dir_arg = args.output_dir or ""
    out_dir = os.path.expanduser(os.path.expandvars(out_dir_arg)) or os.path.dirname(os.path.abspath(in_path)) or "."
    os.makedirs(out_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(in_path))[0]

    # put all artifacts in out_dir
    wav_path = os.path.join(out_dir, f"{base}.diar.wav")
    out_srt  = os.path.join(out_dir, f"{base}.diarized.srt")
    out_txt  = os.path.join(out_dir, f"{base}.diarized.txt")

    # the word-timestamp JSON is produced by transcribe; prefer out_dir
    json_path = os.path.join(out_dir, f"{base}.json")
    if not os.path.exists(json_path):
        # fallback to the input folder if user ran transcribe without output_dir
        fallback = os.path.join(os.path.dirname(os.path.abspath(in_path)), f"{base}.json")
        if os.path.exists(fallback):
            json_path = fallback

    extract_wav(in_path, wav_path)
    print("[i] Running diarization …")
    diar = diarize_audio(
        wav_path,
        args.hf_token,
        num_speakers=args.num_speakers,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
    )

    words = load_words_json(json_path)
    if not words:
        print("[!] No word-level JSON found. For best results, run transcribe with --word_timestamps.")

    chunks = chunks_from_words(words or [], diar) if words else chunks_from_turns_only(diar)
    write_diarized_srt(chunks, out_srt)
    write_diarized_txt(chunks, out_txt)
    print(f"[✓] Diarization written:\n[→] {out_srt}\n[→] {out_txt}")

