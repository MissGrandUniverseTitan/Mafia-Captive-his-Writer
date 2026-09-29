#!/usr/bin/env python3
"""ทดสอบ character LoRA บน Qwen-Image ผ่าน ComfyUI API — ไม่ต้องต่อเส้นใน UI

สร้างภาพคู่ (มี LoRA / ไม่มี LoRA) ด้วย seed เดียวกัน เพื่อเทียบว่า LoRA จำหน้าได้ไหม
ผลลัพธ์: /workspace/ComfyUI/output/lora_test/

ตัวอย่าง:
  python3 lora_test.py kairo_qwen_lora_000002000.safetensors
  python3 lora_test.py kairo_qwen_lora_000002000.safetensors --prompt "k41ro man close-up portrait, smiling"
  python3 lora_test.py kairo_qwen_lora_000001500.safetensors --strength 0.8 --count 3
"""

import argparse
import random
from pathlib import Path

import render_shots as rs

DEFAULT_PROMPT = ("k41ro man standing in a dark rainy alley at night, black three-piece suit, dark red tie, "
                  "looking at the camera, cinematic neo-noir lighting, photorealistic")
NEGATIVE = "low quality, blurry, bad anatomy, extra fingers, deformed face, cartoon, text, watermark"


def pick_unet():
    models = rs.COMFY_DIR / "models" / "diffusion_models"
    for name in ("qwen_image_fp8_e4m3fn.safetensors", "qwen_image_edit_2509_fp8_e4m3fn.safetensors"):
        f = models / name
        if f.exists() and f.stat().st_size > 19 * 1024**3:  # ต้องโหลดครบ (~20GB)
            return name
    raise SystemExit("ไม่เจอโมเดล Qwen-Image หรือ Qwen Image Edit ที่โหลดครบใน models/diffusion_models")


def build(unet, lora, strength, prompt, seed, steps, cfg, width, height, prefix):
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "3": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.1}},
        "4": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                                                    "type": "qwen_image", "device": "default"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": prompt}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": NEGATIVE}},
        "7": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "8": {"class_type": "KSampler", "inputs": {
            "model": ["3", 0], "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0],
            "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["9", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": prefix}},
    }
    if lora:
        wf["2"] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"model": ["1", 0], "lora_name": lora, "strength_model": strength}}
        wf["3"]["inputs"]["model"] = ["2", 0]
    return wf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lora", help="ชื่อไฟล์ใน models/loras เช่น kairo_qwen_lora_000002000.safetensors")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--count", type=int, default=1, help="จำนวนคู่ภาพ (seed ต่างกัน)")
    ap.add_argument("--seed", type=int, help="ใช้ seed นี้ (ล็อกผล) แทนการสุ่ม")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--cfg", type=float, default=2.5)
    ap.add_argument("--size", default="832x1216", help="กว้างxสูง")
    args = ap.parse_args()

    if not (rs.COMFY_DIR / "models" / "loras" / args.lora).exists():
        raise SystemExit(f"ไม่เจอ models/loras/{args.lora}")
    unet = pick_unet()
    width, height = (int(v) for v in args.size.lower().split("x"))
    tag = Path(args.lora).stem
    print(f"โมเดล: {unet}\nLoRA: {args.lora} (strength {args.strength})")
    if "edit" in unet:
        print("  (ยังไม่มี Qwen-Image ตัวเต็ม ใช้ Qwen Image Edit แทน — ผลอาจด้อยกว่าเล็กน้อย)")

    seeds = [args.seed] if args.seed else [random.randint(1, 2**48) for _ in range(args.count)]
    for seed in seeds:
        for use_lora in (True, False):
            label = "with_lora" if use_lora else "no_lora"
            prefix = f"lora_test/{tag}_seed{seed}_{label}"
            wf = build(unet, args.lora if use_lora else None, args.strength, args.prompt, seed,
                       args.steps, args.cfg, width, height, prefix)
            rs.wait(rs.queue(wf), f"seed {seed} {label}")
            print(f"    -> {rs.newest(f'output/{prefix}*.png')}")
    print(f"\nเสร็จ! เปิดดูใน Jupyter: {rs.COMFY_DIR}/output/lora_test/  (เทียบไฟล์ with_lora กับ no_lora ที่ seed เดียวกัน)")


if __name__ == "__main__":
    main()
