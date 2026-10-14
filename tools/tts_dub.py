#!/usr/bin/env python3
"""Make a timed Thai dub track with ElevenLabs v3 or Google Cloud TTS.

Each line is synthesized separately, sped up if it runs past its shot,
placed at its start time, and everything is mixed into one audio file.

    export ELEVENLABS_API_KEY=...        # elevenlabs.io > Developers > API keys
    python3 tools/tts_dub.py --engine elevenlabs --out dub.wav
    python3 tools/tts_dub.py --engine elevenlabs --list-voices

    export GOOGLE_TTS_API_KEY=...        # Cloud Console > APIs > Credentials
    python3 tools/tts_dub.py --out dub.wav

ElevenLabs v3 reads the emotion tags in LINES; Google ignores them.
Voices can be overridden with --lucas-voice / --gideon-voice.

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
ELEVEN_API = "https://api.elevenlabs.io/v1"
RATE = 24000

# Chirp 3 HD male voices: Puck sounds younger (Lucas), Charon deeper (Gideon).
VOICES = {
    "lucas":  {"name": "th-TH-Chirp3-HD-Puck",   "speakingRate": 1.0},
    "gideon": {"name": "th-TH-Chirp3-HD-Charon", "speakingRate": 1.0},
}

# ElevenLabs premade voices: Liam is young (Lucas), Brian is deep (Gideon).
ELEVEN_VOICES = {
    "lucas":  "TX3LPaxmHKxFdv7VOQHJ",
    "gideon": "nPczCjzI2devNBz1zQrb",
}

# (start, end, speaker, v3 emotion tags, text) — the 16 s Lucas/Gideon noodle-shop clip.
LINES = [
    (0.0,  2.5,  "lucas",  "[voice trembling][on the verge of tears]",
     "ทำไมเช้านี้ไม่มีก๋วยเตี๋ยวเป็ด!"),
    (2.5,  5.9,  "gideon", "[shouting][furious]",
     "นายบ้าไปแล้วเหรอ! ร้านไหนมันเปิดหกโมงเช้าฮะ!"),
    (5.9,  8.8,  "lucas",  "[sobbing][disappointed]",
     "มาเฟียประสาอะไร ก๋วยเตี๋ยวชามเดียวยังหาไม่ได้!"),
    (8.8,  12.1, "gideon", "[yelling]",
     "จะให้ฉันเอาปืนไปจ่อหัวเฮียช้างรึไงฮะ!"),
    (12.1, 14.3, "gideon", "[sighs][softly, deep voice, pleading]",
     "โอเคๆ ฉันยอม... พรุ่งนี้เซ้งร้านมาให้เลย"),
    (14.3, 16.1, "lucas",  "[whispers][sulky]",
     "...ไม่ใส่ถั่วงอกนะ"),
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


def eleven(path, body=None, out=None):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set")
    req = urllib.request.Request(
        f"{ELEVEN_API}/{path}", data=json.dumps(body).encode() if body else None,
        headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            if out:
                with open(out, "wb") as f:
                    f.write(r.read())
                return None
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code}: {e.read().decode()}")


def eleven_synth(text, voice_id, path):
    # v3 stability: 0.0 Creative (most expressive), 0.5 Natural, 1.0 Robust.
    body = {"text": text, "model_id": "eleven_v3",
            "voice_settings": {"stability": 0.0}}
    eleven(f"text-to-speech/{voice_id}?output_format=mp3_44100_128", body, out=path)


def tone(seconds, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    f"sine=f=440:d={seconds}:r={RATE}", path], check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--engine", choices=["google", "elevenlabs"], default="google")
    p.add_argument("--lucas-voice")
    p.add_argument("--gideon-voice")
    p.add_argument("--out", default="dub.wav")
    p.add_argument("--list-voices", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    if a.lucas_voice:
        VOICES["lucas"]["name"] = ELEVEN_VOICES["lucas"] = a.lucas_voice
    if a.gideon_voice:
        VOICES["gideon"]["name"] = ELEVEN_VOICES["gideon"] = a.gideon_voice

    if a.list_voices and a.engine == "elevenlabs":
        for v in eleven("voices")["voices"]:
            print(v["voice_id"], v["name"], v.get("labels", {}).get("gender", ""))
        return
    if a.list_voices:
        for v in api("voices?languageCode=th-TH").get("voices", []):
            print(v["name"], v["ssmlGender"])
        return

    tmp = tempfile.mkdtemp()
    inputs, filters = [], []
    for i, (start, end, who, tags, text) in enumerate(LINES):
        raw = os.path.join(tmp, f"{i}.wav")
        if a.dry_run:
            tone(min(len(text) * 0.08, 4), raw)
        elif a.engine == "elevenlabs":
            raw = os.path.join(tmp, f"{i}.mp3")
            eleven_synth(f"{tags} {text}", ELEVEN_VOICES[who], raw)
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
