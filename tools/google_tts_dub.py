#!/usr/bin/env python3
"""Make a timed Thai dub track with Google Cloud Text-to-Speech.

Each line is synthesized separately, sped up if it runs past its shot,
placed at its start time, and everything is mixed into one audio file.

    export GOOGLE_TTS_API_KEY=...        # Cloud Console > APIs > Credentials
    python3 tools/google_tts_dub.py --out dub.wav
    python3 tools/google_tts_dub.py --list-voices   # Thai voices on the account

--dry-run uses tones instead of the API, to check timing and mixing.
Needs ffmpeg. Standard library only.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

API = "https://texttospeech.googleapis.com/v1"
RATE = 24000

# Chirp 3 HD male voices: Puck sounds younger (Lucas), Charon deeper (Gideon).
VOICES = {
    "lucas":  {"name": "th-TH-Chirp3-HD-Puck",   "speakingRate": 1.0},
    "gideon": {"name": "th-TH-Chirp3-HD-Charon", "speakingRate": 1.0},
}

# (start, end, speaker, text) — the 16 s Lucas/Gideon noodle-shop clip.
LINES = [
    (0.0,  2.5,  "lucas",  "ทำไมเช้านี้ไม่มีก๋วยเตี๋ยวเป็ด!"),
    (2.5,  5.9,  "gideon", "นายบ้าไปแล้วเหรอ! ร้านไหนมันเปิดหกโมงเช้าฮะ!"),
    (5.9,  8.8,  "lucas",  "มาเฟียประสาอะไร ก๋วยเตี๋ยวชามเดียวยังหาไม่ได้!"),
    (8.8,  12.1, "gideon", "จะให้ฉันเอาปืนไปจ่อหัวเฮียช้างรึไงฮะ!"),
    (12.1, 14.3, "gideon", "โอเคๆ ฉันยอม... พรุ่งนี้เซ้งร้านมาให้เลย"),
    (14.3, 16.1, "lucas",  "...ไม่ใส่ถั่วงอกนะ"),
]
TOTAL = 16.1
MAX_SPEEDUP = 1.35


def api(path, body=None):
    key = os.environ.get("GOOGLE_TTS_API_KEY")
    if not key:
        sys.exit("GOOGLE_TTS_API_KEY is not set")
    req = urllib.request.Request(
        f"{API}/{path}{'&' if '?' in path else '?'}key={key}",
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Google TTS {e.code}: {e.read().decode()}")


def synth(text, voice, path):
    body = {
        "input": {"text": text},
        "voice": {"languageCode": "th-TH", "name": voice["name"]},
        "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": RATE,
                        "speakingRate": voice["speakingRate"]},
    }
    with open(path, "wb") as f:
        f.write(base64.b64decode(api("text:synthesize", body)["audioContent"]))


def tone(seconds, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=f=440:d={seconds}:r={RATE}", path], check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="dub.wav")
    p.add_argument("--list-voices", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    if a.list_voices:
        for v in api("voices?languageCode=th-TH").get("voices", []):
            print(v["name"], v["ssmlGender"])
        return

    tmp = tempfile.mkdtemp()
    inputs, filters = [], []
    for i, (start, end, who, text) in enumerate(LINES):
        raw = os.path.join(tmp, f"{i}.wav")
        if a.dry_run:
            tone(min(len(text) * 0.08, 4), raw)
        else:
            synth(text, VOICES[who], raw)
        slot, dur = end - start, duration(raw)
        speed = min(max(dur / (slot - 0.1), 1.0), MAX_SPEEDUP)
        note = f" (sped up x{speed:.2f})" if speed > 1 else ""
        warn = "  !! still too long for the shot" if dur / speed > slot else ""
        print(f"{start:5.1f}-{end:4.1f}s {who:6} {dur:4.2f}s{note}{warn}  {text}")
        inputs += ["-i", raw]
        ms = int(start * 1000)
        filters.append(f"[{i}:a]atempo={speed:.3f},adelay={ms}|{ms}[a{i}]")

    mix = "".join(f"[a{i}]" for i in range(len(LINES)))
    filters.append(f"{mix}amix=inputs={len(LINES)}:normalize=0,apad=whole_dur={TOTAL},"
                   f"atrim=0:{TOTAL},loudnorm=I=-16:TP=-1.5[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs,
                    "-filter_complex", ";".join(filters), "-map", "[out]",
                    "-ar", "48000", a.out], check=True)
    print(f"wrote {a.out} ({duration(a.out):.2f}s)")


if __name__ == "__main__":
    main()
