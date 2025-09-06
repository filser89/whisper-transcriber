# Whisper Transcriber Toolkit

A Python-based CLI for **speech-to-text transcription** and **speaker diarization** of meeting recordings (e.g. Google Meet, Zoom, Teams).
Built on [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) for transcription and [pyannote.audio](https://github.com/pyannote/pyannote-audio) for diarization.

Outputs include:

- **Transcript** in `.txt`, `.srt`, `.vtt`
- **Word-level JSON** with timestamps
- **Diarized transcripts** with `Speaker 1`, `Speaker 2`, … in `.srt` and `.txt`

---

## 🔧 Installation

### Requirements

- macOS / Linux
- Python **3.12+** (venv recommended)
- [ffmpeg](https://ffmpeg.org/download.html) (must be in PATH)
- Hugging Face account + access token (for diarization)

### Setup

```bash
# clone the repo
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber

# create virtual environment
make venv

# install dependencies
make install

# copy environment template
cp .env.example .env
# then edit .env and set your Hugging Face token + options

# (optional) upgrade deps
make update
```

### Hugging Face token

1. Go to [Hugging Face tokens](https://huggingface.co/settings/tokens).
2. Create a new **Access Token**.
3. Accept access for both gated models:

   - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

4. Save your token in a `.env` file in the project root:

   ```env
   HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx
   ```

### Optional defaults via `.env`

You can also define default transcription settings in `.env`. CLI flags always override these values, but if you don’t provide flags, the following env vars are used:

```env
MODEL_SIZE=medium         # tiny | base | small | medium | large-v3
LANGUAGE=ru               # e.g. 'ru' for Russian, leave empty for auto-detect
DEVICE=cpu                # cpu | cuda
BEAM_SIZE=5               # decoding beam size (higher = better, slower)
VAD_FILTER=true           # true | false
```

---

## 🚀 Usage

All commands are run with `make` from the project root.
Input files can be `.mp4`, `.m4a`, `.wav`, etc.

### Transcribe

```bash
make transcribe INPUT=/path/to/file.mp4 ARGS="--word_timestamps" OUTDIR=~/transcripts
```

Outputs:

- `.txt`, `.srt`, `.vtt`, `.json` in OUTDIR.

### Diarize

```bash
make diarize INPUT=/path/to/file.mp4 ARGS="--num_speakers 2" OUTDIR=~/transcripts
```

Outputs:

- `.diarized.srt`, `.diarized.txt` in OUTDIR.
- Temporary `.diar.wav` (auto-extracted audio).

### Full pipeline

```bash
make full INPUT=/path/to/file.mp4 OUTDIR=~/transcripts ARGS="--num_speakers 2"
```

Runs transcription **with word timestamps** and then diarization.

- `ARGS` are forwarded to diarization.
- `OUTDIR` applies to both steps.

Outputs: transcript + diarized transcript in OUTDIR.

---

## 📂 Example

```bash
make full INPUT=~/Downloads/meeting.mp4 OUTDIR=~/Downloads/transcripts ARGS="--min_speakers 2 --max_speakers 4"
```

Produces:

```
meeting.txt
meeting.srt
meeting.vtt
meeting.json
meeting.diarized.srt
meeting.diarized.txt
meeting.diar.wav
```

---

## ⚡ Tips

- For long meetings, cut a 1-minute sample with ffmpeg to test:

  ```bash
  ffmpeg -ss 0 -t 60 -i input.mp4 -c copy sample.mp4
  ```

- Default behavior = outputs next to the input file. Use `OUTDIR` to keep transcripts organized.
- Always run `make` from the repo root so `.env` is found.

---

## 📑 CLI Arguments Cheat Sheet

| Command        | Argument            | Default                           | Description                                                           |
| -------------- | ------------------- | --------------------------------- | --------------------------------------------------------------------- |
| **General**    | `INPUT`             | — (required)                      | Path to input media file (.mp4, .m4a, .wav, …)                        |
|                | `OUTDIR`            | Same dir as input                 | Output directory for all artifacts                                    |
|                | `ARGS`              | —                                 | Extra arguments forwarded to transcribe/diarize                       |
| **Transcribe** | `--model`           | from `.env` (`MODEL_SIZE=medium`) | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`)    |
|                | `--language`        | from `.env` (`LANGUAGE=ru`)       | Language code, empty for auto-detect                                  |
|                | `--device`          | from `.env` (`DEVICE=cpu`)        | Compute device (`cpu`, `cuda`)                                        |
|                | `--beam_size`       | from `.env` (`BEAM_SIZE=5`)       | Beam search width: higher = better accuracy, slower                   |
|                | `--vad_filter`      | from `.env` (`VAD_FILTER=false`)  | Apply simple voice activity detection before transcription            |
|                | `--word_timestamps` | off                               | Emit per-word timestamps and save JSON                                |
| **Diarize**    | `--hf_token`        | from `.env` (`HUGGINGFACE_TOKEN`) | Hugging Face token (overrides env var)                                |
|                | `--num_speakers`    | auto                              | Lock diarization to exactly N speakers                                |
|                | `--min_speakers`    | auto                              | Lower bound on number of speakers                                     |
|                | `--max_speakers`    | auto                              | Upper bound on number of speakers                                     |
| **Full**       | (all of above)      | —                                 | Runs transcription (always with `--word_timestamps`) then diarization |

---
