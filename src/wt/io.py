from datetime import timedelta
import webvtt
import json

def ts_srt(sec: float) -> str:
    td = timedelta(seconds=sec)
    s = str(td)
    return (s[:-3] if "." in s else f"{s},000").replace(".", ",")

def ts_vtt(sec: float) -> str:
    td = timedelta(seconds=sec)
    s = str(td)
    return s[:-3] if "." in s else f"{s}.000"

def write_txt(segments, path: str):
    text = " ".join(seg.text.strip() for seg in segments).strip()
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def write_srt(segments, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n{ts_srt(seg.start)} --> {ts_srt(seg.end)}\n{seg.text.strip()}\n\n")

def write_vtt(segments, path: str):
    vtt = webvtt.WebVTT()
    for seg in segments:
        vtt.captions.append(webvtt.Caption(ts_vtt(seg.start), ts_vtt(seg.end), seg.text.strip()))
    vtt.save(path)

def write_words_json(segments, path: str):
    data = []
    for seg in segments:
        item = {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        if seg.words:
            item["words"] = [{"word": w.word, "start": w.start, "end": w.end} for w in seg.words]
        data.append(item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"segments": data}, f, ensure_ascii=False, indent=2)

