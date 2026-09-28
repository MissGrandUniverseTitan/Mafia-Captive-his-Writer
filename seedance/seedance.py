#!/usr/bin/env python3
"""สร้างวิดีโอด้วย Seedance ผ่าน BytePlus ModelArk API (จ่ายตามใช้จริง)

ใช้แค่ Python standard library ไม่ต้องติดตั้งอะไรเพิ่ม

ตัวอย่าง:
    export ARK_API_KEY=xxxx
    python seedance.py "a cat surfing a wave at sunset" --draft
    python seedance.py "slow dolly-in on the product" --image first_frame.png --resolution 1080p
    python seedance.py "..." --estimate          # ดูจำนวน token/ค่าใช้จ่ายโดยประมาณ ไม่เสียเงิน
"""

import argparse
import base64
import csv
import datetime as dt
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
TASKS_PATH = "/contents/generations/tasks"

# model ID เปลี่ยนตามเวอร์ชัน ให้เช็กชื่อล่าสุดที่เปิดใช้ได้ในหน้า ModelArk console แล้ว override ผ่าน env/--model
DEFAULT_MODEL = os.environ.get("SEEDANCE_MODEL", "seedance-1-0-pro-250528")
DRAFT_MODEL = os.environ.get("SEEDANCE_DRAFT_MODEL", "seedance-1-0-pro-fast-251015")

# ขนาดเฟรมโดยประมาณ (อัตราส่วน 16:9) ใช้คำนวณ token ล่วงหน้าเท่านั้น ค่าจริงดูจาก usage ใน response
FRAME_SIZES = {"480p": (864, 480), "720p": (1280, 720), "1080p": (1920, 1080)}
FPS = 24

LOG_FILE = Path(__file__).with_name("usage_log.csv")


def estimate_tokens(resolution, duration):
    w, h = FRAME_SIZES[resolution]
    return int(w * h * FPS * duration / 1024)


def price_per_million():
    value = os.environ.get("SEEDANCE_PRICE_PER_M_TOKENS")
    return float(value) if value else None


def format_cost(tokens):
    price = price_per_million()
    if price is None:
        return "(ตั้ง SEEDANCE_PRICE_PER_M_TOKENS เพื่อดูราคาเป็น $)"
    return f"≈ ${tokens / 1_000_000 * price:.3f}"


def image_to_data_url(path_or_url):
    if path_or_url.startswith(("http://", "https://", "data:")):
        return path_or_url
    path = Path(path_or_url)
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def api_request(method, url, api_key, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode(errors='replace')}")


def build_payload(args):
    flags = (
        f" --resolution {args.resolution} --duration {args.duration}"
        f" --ratio {args.ratio} --camerafixed {str(args.camera_fixed).lower()}"
        f" --watermark false --seed {args.seed}"
    )
    content = [{"type": "text", "text": args.prompt + flags}]
    if args.image:
        content.append({"type": "image_url", "image_url": {"url": image_to_data_url(args.image)}})
    return {"model": args.model, "content": content}


def wait_for_task(base_url, api_key, task_id, poll_interval):
    started = time.time()
    while True:
        task = api_request("GET", f"{base_url}{TASKS_PATH}/{task_id}", api_key)
        status = task.get("status")
        print(f"\r  สถานะ: {status:<10} ({int(time.time() - started)}s)", end="", flush=True)
        if status in ("succeeded", "failed", "cancelled", "expired"):
            print()
            return task
        time.sleep(poll_interval)


def download(url, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as resp, open(out_path, "wb") as f:
        f.write(resp.read())


def log_usage(row):
    new_file = not LOG_FILE.exists()
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def parse_args():
    p = argparse.ArgumentParser(description="Seedance video generation via BytePlus ModelArk")
    p.add_argument("prompt", help="คำอธิบายวิดีโอ")
    p.add_argument("--image", help="ไฟล์ภาพหรือ URL สำหรับเฟรมแรก (image-to-video)")
    p.add_argument("--model", default=None, help=f"model ID (ค่าเริ่มต้น {DEFAULT_MODEL})")
    p.add_argument("--resolution", choices=FRAME_SIZES, default=None)
    p.add_argument("--duration", type=int, default=5, help="ความยาว (วินาที)")
    p.add_argument("--ratio", default="16:9", help="เช่น 16:9, 9:16, 1:1, adaptive")
    p.add_argument("--seed", type=int, default=-1, help="-1 = สุ่ม, ใส่เลขเดิมเพื่อให้ได้ผลใกล้เดิม")
    p.add_argument("--camera-fixed", action="store_true", help="ล็อกกล้องไม่ให้ขยับ")
    p.add_argument("--draft", action="store_true", help="โหมดร่างราคาถูก: โมเดล fast + 480p")
    p.add_argument("--estimate", action="store_true", help="แสดง token/ราคาโดยประมาณ แล้วจบ (ไม่เรียก API)")
    p.add_argument("--out", default="outputs", help="โฟลเดอร์เก็บวิดีโอ")
    p.add_argument("--poll-interval", type=float, default=5)
    args = p.parse_args()
    args.model = args.model or (DRAFT_MODEL if args.draft else DEFAULT_MODEL)
    args.resolution = args.resolution or ("480p" if args.draft else "720p")
    return args


def main():
    args = parse_args()
    est = estimate_tokens(args.resolution, args.duration)
    print(f"โมเดล: {args.model} | {args.resolution} {args.duration}s {args.ratio}")
    print(f"token โดยประมาณ: {est:,} {format_cost(est)}")
    if args.estimate:
        return

    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        sys.exit("ยังไม่ได้ตั้ง ARK_API_KEY (สร้างได้ที่ ModelArk console > API Keys)")
    base_url = os.environ.get("ARK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    created = api_request("POST", f"{base_url}{TASKS_PATH}", api_key, build_payload(args))
    task_id = created["id"]
    print(f"สร้างงานแล้ว: {task_id}")

    task = wait_for_task(base_url, api_key, task_id, args.poll_interval)
    tokens = (task.get("usage") or {}).get("completion_tokens", 0)
    row = {
        "time": dt.datetime.now().isoformat(timespec="seconds"),
        "task_id": task_id,
        "model": args.model,
        "resolution": args.resolution,
        "duration": args.duration,
        "status": task.get("status"),
        "tokens": tokens,
        "prompt": args.prompt,
    }
    log_usage(row)

    if task.get("status") != "succeeded":
        sys.exit(f"งานไม่สำเร็จ: {json.dumps(task.get('error'), ensure_ascii=False)}")

    out_path = Path(args.out) / f"{dt.datetime.now():%Y%m%d-%H%M%S}-{task_id}.mp4"
    download(task["content"]["video_url"], out_path)
    print(f"บันทึกวิดีโอ: {out_path}")
    print(f"token ที่ใช้จริง: {tokens:,} {format_cost(tokens)}")


if __name__ == "__main__":
    main()
