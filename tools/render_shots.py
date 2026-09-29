#!/usr/bin/env python3
"""เรนเดอร์หลายช็อตรวดเดียวผ่าน ComfyUI API: keyframe (Qwen Image Edit) -> วิดีโอ (Wan 2.2 I2V)

รันบน RunPod (เครื่องเดียวกับ ComfyUI) ใช้แค่ Python standard library

เตรียมครั้งแรก: กด Run workflow Qwen Image Edit 2509 และ Wan 2.2 I2V ใน ComfyUI อย่างละ 1 ครั้ง
สคริปต์จะดึง workflow จากประวัติงานมาเก็บไว้ที่ /workspace/workflows/ ให้เอง
(หรือ export เองด้วย Export (API) แล้ววางไว้ที่ qwen_edit_api.json / wan_i2v_api.json)

ตัวอย่าง:
  python3 render_shots.py ../episodes/ep01_scene1.json                 # keyframe + วิดีโอ ทุกช็อต
  python3 render_shots.py ../episodes/ep01_scene1.json --only S1-3     # เฉพาะบางช็อต
  python3 render_shots.py ../episodes/ep01_scene1.json --stage keyframe # ทำแค่ keyframe (ไว้คัดก่อน)
  python3 render_shots.py ../episodes/ep01_scene1.json --stage video --seeds 3
"""

import argparse
import copy
import csv
import datetime as dt
import json
import random
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

COMFY = "http://127.0.0.1:8188"
COMFY_DIR = Path("/workspace/ComfyUI")
WORKFLOW_DIR = Path("/workspace/workflows")


# ---------- ComfyUI API ----------

def queue(workflow):
    req = urllib.request.Request(
        f"{COMFY}/prompt",
        data=json.dumps({"prompt": workflow}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)["prompt_id"]
    except urllib.error.HTTPError as e:
        sys.exit(f"ComfyUI ปฏิเสธงาน: {e.read().decode(errors='replace')}")


def wait(prompt_id, label):
    start = time.time()
    while True:
        with urllib.request.urlopen(f"{COMFY}/history/{prompt_id}") as resp:
            hist = json.load(resp).get(prompt_id)
        if hist:
            status = hist.get("status", {})
            print(f"\r  {label}: เสร็จ ({int(time.time() - start)}s)          ")
            if status.get("status_str") == "error":
                msgs = [m for m in status.get("messages", []) if m[0] == "execution_error"]
                sys.exit(f"  เรนเดอร์ล้มเหลว: {json.dumps(msgs, ensure_ascii=False)[:800]}")
            return
        print(f"\r  {label}: กำลังเรนเดอร์... {int(time.time() - start)}s", end="", flush=True)
        time.sleep(3)


def load_workflow(filename, marker):
    """โหลด workflow แบบ API จากไฟล์ ถ้าไม่มีให้ดึงจากประวัติงานล่าสุดของ ComfyUI ที่มี node `marker`"""
    path = WORKFLOW_DIR / filename
    if path.exists():
        return json.loads(path.read_text())
    with urllib.request.urlopen(f"{COMFY}/history?max_items=500") as resp:
        hist = json.load(resp)
    for entry in reversed(list(hist.values())):
        wf = entry["prompt"][2]
        if any(n.get("class_type") == marker for n in wf.values()):
            WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(wf, indent=1))
            print(f"  ดึง workflow จากประวัติ ComfyUI -> {path}")
            return wf
    if marker == "WanImageToVideo":
        print("  ไม่เจอ workflow Wan ในประวัติ — ใช้ workflow Wan 2.2 I2V + LightX2V 4-step ที่ติดมากับสคริปต์")
        return default_wan_workflow()
    sys.exit(f"ไม่มี {path} และไม่เจองาน {marker} ในประวัติ — กด Run workflow นั้นใน ComfyUI สัก 1 ครั้งก่อน")


WAN_NEGATIVE = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，"
                "多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走, "
                "twisted neck, distorted neck, deformed face")


def default_wan_workflow():
    """Wan 2.2 14B I2V แบบ 2 expert (high/low noise) + LightX2V 4-step — ตามโครง template ทางการของ ComfyUI"""
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "strength_model": 1.0,
              "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "strength_model": 1.0,
              "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"}},
        "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 5.0}},
        "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 5.0}},
        "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": ""}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": WAN_NEGATIVE}},
        "10": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "11": {"class_type": "LoadImage", "inputs": {"image": "S1-2_keyframe.png"}},
        "12": {"class_type": "WanImageToVideo", "inputs": {"positive": ["8", 0], "negative": ["9", 0], "vae": ["10", 0],
               "start_image": ["11", 0], "width": 480, "height": 832, "length": 81, "batch_size": 1}},
        "13": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["5", 0], "positive": ["12", 0], "negative": ["12", 1],
               "latent_image": ["12", 2], "add_noise": "enable", "noise_seed": 1, "steps": 4, "cfg": 1.0,
               "sampler_name": "euler", "scheduler": "simple", "start_at_step": 0, "end_at_step": 2,
               "return_with_leftover_noise": "enable"}},
        "14": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["6", 0], "positive": ["12", 0], "negative": ["12", 1],
               "latent_image": ["13", 0], "add_noise": "disable", "noise_seed": 0, "steps": 4, "cfg": 1.0,
               "sampler_name": "euler", "scheduler": "simple", "start_at_step": 2, "end_at_step": 10000,
               "return_with_leftover_noise": "disable"}},
        "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["10", 0]}},
        "16": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 16}},
        "17": {"class_type": "SaveVideo", "inputs": {"video": ["16", 0], "filename_prefix": "video/wan", "format": "auto", "codec": "auto"}},
    }


# ---------- ค้นหา node ใน workflow แบบ API ----------

def nodes_of(wf, *class_types):
    return [nid for nid, n in wf.items() if n.get("class_type") in class_types]


def upstream(wf, link, target_types, depth=6):
    """ไล่สายย้อนกลับจาก input link จนเจอ node ชนิดที่ต้องการ"""
    if not isinstance(link, list) or depth == 0:
        return None
    nid = str(link[0])
    node = wf.get(nid)
    if node is None:
        return None
    if node["class_type"] in target_types:
        return nid
    for v in node["inputs"].values():
        found = upstream(wf, v, target_types, depth - 1)
        if found:
            return found
    return None


def consumers(wf, nid):
    return [(cid, key) for cid, n in wf.items() for key, v in n["inputs"].items()
            if isinstance(v, list) and str(v[0]) == str(nid)]


def set_output_prefix(wf, prefix):
    outs = [nid for nid, n in wf.items() if "filename_prefix" in n.get("inputs", {})]
    if not outs:
        sys.exit("ไม่เจอ node สำหรับบันทึกผลลัพธ์ใน workflow")
    for nid in outs:
        wf[nid]["inputs"]["filename_prefix"] = prefix


# ---------- keyframe (Qwen Image Edit 2509) ----------

def build_keyframe(base, shot, style, seed):
    wf = copy.deepcopy(base)
    enc = nodes_of(wf, "TextEncodeQwenImageEditPlus")
    if not enc:
        sys.exit("qwen_edit_api.json ไม่มี TextEncodeQwenImageEditPlus — export ถูก workflow ไหม?")
    # positive = ตัวที่ต่อเข้าช่อง positive ของ KSampler
    ks = nodes_of(wf, "KSampler")
    pos_id = str(wf[ks[0]]["inputs"]["positive"][0]) if ks else enc[0]
    pos = upstream(wf, [pos_id, 0], {"TextEncodeQwenImageEditPlus"}) or enc[0]

    refs = shot["refs"]
    for enc_id in enc:
        inputs = wf[enc_id]["inputs"]
        for i in range(1, 4):
            key = f"image{i}"
            if key not in inputs:
                continue
            if i > len(refs):
                del inputs[key]  # ช่องภาพที่ไม่ได้ใช้
                continue
            loader = upstream(wf, inputs[key], {"LoadImage"})
            if not loader:
                sys.exit(f"หา LoadImage ของ {key} ไม่เจอ")
            wf[loader]["inputs"]["image"] = refs[i - 1]
    wf[pos]["inputs"]["prompt"] = f"{shot['keyframe_prompt']}, {style}"
    for k in ks:
        wf[k]["inputs"]["seed"] = seed
    for i, lora in enumerate(shot.get("loras", [])):
        add_lora(wf, f"char_lora_{i}", lora)
    set_output_prefix(wf, f"keyframes/{shot['id']}")
    return wf


def add_lora(wf, node_id, lora):
    """แทรก LoraLoaderModelOnly ต่อจาก UNETLoader (ทุกอย่างที่เคยรับ MODEL จาก UNET จะรับจาก LoRA แทน)"""
    unet = nodes_of(wf, "UNETLoader")
    if not unet:
        sys.exit("ไม่เจอ UNETLoader ใน workflow — ใส่ LoRA ไม่ได้")
    src = unet[0]
    for cid, key in consumers(wf, src):
        wf[cid]["inputs"][key] = [node_id, 0]
    name, _, strength = lora.partition(":")
    wf[node_id] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"model": [src, 0], "lora_name": name, "strength_model": float(strength or 1.0)}}


# ---------- วิดีโอ (Wan 2.2 I2V) ----------

def build_video(base, shot, keyframe_name, seed, size, length):
    wf = copy.deepcopy(base)
    i2v = nodes_of(wf, "WanImageToVideo")
    if not i2v:
        sys.exit("wan_i2v_api.json ไม่มี WanImageToVideo — export ถูก workflow ไหม?")
    node = wf[i2v[0]]["inputs"]
    node["width"], node["height"] = size
    node["length"] = length
    loader = upstream(wf, node["start_image"], {"LoadImage"})
    wf[loader]["inputs"]["image"] = keyframe_name
    pos = upstream(wf, node["positive"], {"CLIPTextEncode"})
    wf[pos]["inputs"]["text"] = shot["motion_prompt"]
    for k in nodes_of(wf, "KSamplerAdvanced"):
        if wf[k]["inputs"].get("add_noise") == "enable":
            wf[k]["inputs"]["noise_seed"] = seed
    for k in nodes_of(wf, "KSampler"):
        wf[k]["inputs"]["seed"] = seed
    set_output_prefix(wf, f"{shot['episode']}/{shot['id']}_seed{seed}")
    return wf


# ---------- main ----------

def newest(pattern):
    files = sorted(COMFY_DIR.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", help="ไฟล์ JSON ของช็อต เช่น episodes/ep01_scene1.json")
    ap.add_argument("--only", nargs="*", help="เลือกเฉพาะช็อต เช่น S1-1 S1-3")
    ap.add_argument("--stage", choices=["all", "keyframe", "video"], default="all")
    ap.add_argument("--seeds", type=int, default=1, help="จำนวน seed ต่อช็อต (ไว้เลือกคลิปที่ดีที่สุด)")
    ap.add_argument("--redo-keyframes", action="store_true", help="สร้าง keyframe ใหม่แม้มีอยู่แล้ว")
    args = ap.parse_args()

    spec = json.loads(Path(args.shots).read_text(encoding="utf-8"))
    shots = [s for s in spec["shots"] if not args.only or s["id"] in args.only]
    for s in shots:
        s["episode"] = spec["episode"]
    size = tuple(spec.get("size", [480, 832]))
    length = spec.get("length", 81)
    input_dir = COMFY_DIR / "input"
    log_path = COMFY_DIR / "output" / spec["episode"] / "render_log.csv"

    if args.stage in ("all", "keyframe"):
        qwen = load_workflow("qwen_edit_api.json", "TextEncodeQwenImageEditPlus")
        print("== Keyframes (Qwen Image Edit) ==")
        for s in shots:
            name = f"{s['id']}_keyframe.png"
            if s.get("keyframe") or ((input_dir / name).exists() and not args.redo_keyframes):
                print(f"  {s['id']}: มี keyframe แล้ว ข้าม")
                continue
            pid = queue(build_keyframe(qwen, s, spec["style"], random.randint(1, 2**48)))
            wait(pid, s["id"])
            out = newest(f"output/keyframes/{s['id']}*.png")
            shutil.copy(out, input_dir / name)
            print(f"    -> input/{name}")

    if args.stage in ("all", "video"):
        wan = load_workflow("wan_i2v_api.json", "WanImageToVideo")
        print("== Videos (Wan 2.2 I2V) ==")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        new_log = not log_path.exists()
        with open(log_path, "a", newline="") as f:
            log = csv.writer(f)
            if new_log:
                log.writerow(["time", "shot", "seed", "file"])
            for s in shots:
                kf = s.get("keyframe") or f"{s['id']}_keyframe.png"
                if not (input_dir / kf).exists():
                    print(f"  {s['id']}: ไม่มี {kf} ข้าม (รัน --stage keyframe ก่อน)")
                    continue
                seeds = s.get("seeds") or [random.randint(1, 2**48) for _ in range(args.seeds)]
                for seed in seeds:
                    pid = queue(build_video(wan, s, kf, seed, size, length))
                    wait(pid, f"{s['id']} seed {seed}")
                    out = newest(f"output/{spec['episode']}/{s['id']}_seed{seed}*")
                    log.writerow([dt.datetime.now().isoformat(timespec="seconds"), s["id"], seed, out])
                    f.flush()
                    print(f"    -> {out}")
        print(f"\nเสร็จ! วิดีโออยู่ที่ {COMFY_DIR}/output/{spec['episode']}/  (log: {log_path})")


if __name__ == "__main__":
    main()
