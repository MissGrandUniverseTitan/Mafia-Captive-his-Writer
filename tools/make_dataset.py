#!/usr/bin/env python3
"""สร้างชุดภาพเทรน character LoRA จากภาพอ้างอิง ด้วย Qwen Image Edit 2509 (ผ่าน ComfyUI API)

ได้ภาพหลายมุม/อารมณ์/แสง/ขนาดช็อต + ไฟล์ caption (.txt) คู่กันทุกภาพ
พร้อมใช้กับ ai-toolkit / kohya

ใช้ (บน RunPod ข้างไฟล์ render_shots.py):
  python3 make_dataset.py kairo             # ~24 ภาพ -> /workspace/datasets/kairo/
  python3 make_dataset.py damian --per 2    # 2 ภาพต่อแบบ (seed ต่างกัน) คัดทิ้งทีหลังได้
แล้วเปิดโฟลเดอร์ดู ลบภาพที่หน้า/ผมไม่เหมือนทิ้ง (ทั้ง .png และ .txt)
"""

import argparse
import random
import shutil
from pathlib import Path

import render_shots as rs

DATASET_DIR = Path("/workspace/datasets")

CHARACTERS = {
    "kairo": {
        "trigger": "k41ro man",
        "refs": ["kairo_face_front.png", "kairo_full_front.png"],
        "look": "messy jet-black hair swept back with loose strands falling over his forehead, warm tan olive skin, "
                "thick dark eyebrows, sharp jawline, intense dark eyes",
        "outfit": "black three-piece suit, black shirt, dark red tie",
        "extra_refs": ["kairo_face_front.png", "kairo_face_profile.png", "kairo_full_front.png"],
    },
    "damian": {
        "trigger": "d4mian man",
        "refs": ["damian_face_front.png", "damian_full_front.png"],
        "look": "voluminous tousled wavy dirty-blond hair, ear-length messy curls, fair skin, blue eyes, soft youthful face",
        "outfit": "beige trench coat, cream knit sweater, dark jeans",
        "extra_refs": ["damian_face_front.png", "damian_face_profile.png", "damian_full_front.png"],
    },
}

# (caption ส่วนที่ "เปลี่ยน" ในแต่ละภาพ, คำสั่งให้ Qwen)  — ไม่ใส่ลักษณะหน้า/ผมใน caption เพื่อให้ LoRA จำเอง
VARIATIONS = [
    ("close-up portrait, front view, neutral expression, soft studio light, plain grey background",
     "close-up portrait facing the camera, neutral expression, soft studio lighting, plain grey background"),
    ("close-up portrait, three-quarter left view, slight smile, window light",
     "close-up portrait turned three-quarters to the left, slight smile, soft window light, blurred apartment background"),
    ("close-up portrait, three-quarter right view, serious expression, night street neon light",
     "close-up portrait turned three-quarters to the right, serious expression, lit by red and blue neon at night, blurred city street"),
    ("side profile, looking left, calm expression, dramatic rim light, dark background",
     "side profile looking left, calm expression, dramatic rim lighting, dark background"),
    ("side profile, looking right, overcast daylight, outdoor",
     "side profile looking right, overcast daylight, outdoors near a brick wall"),
    ("close-up, looking up, surprised expression, warm indoor light",
     "close-up looking upward, surprised expression, warm tungsten indoor lighting"),
    ("close-up, looking down, sad expression, rain, night",
     "close-up looking down, sad expression, rain drops on his face, night, cold blue light"),
    ("close-up, angry expression, harsh top light",
     "close-up, angry intense expression, harsh overhead light, dark background"),
    ("close-up, laughing, golden hour sunlight",
     "close-up, laughing naturally, golden hour sunlight, outdoor park background"),
    ("close-up, whispering, low-key lighting",
     "close-up, whispering with lips slightly parted, low-key cinematic lighting"),
    ("medium shot, front view, arms crossed, office background",
     "medium shot from the waist up, arms crossed, modern office background, daylight"),
    ("medium shot, sitting at a table, cafe, daylight",
     "medium shot sitting at a wooden cafe table, relaxed, daylight"),
    ("medium shot, walking, city street, night",
     "medium shot walking along a city street at night, streetlights and bokeh"),
    ("medium shot, leaning against a wall, alley, night neon",
     "medium shot leaning against a brick wall in a dark alley at night, neon light"),
    ("medium shot, three-quarter back view, looking over shoulder",
     "medium shot from behind at three-quarter angle, looking back over his shoulder"),
    ("medium shot, inside a car, night",
     "medium shot sitting in the driver's seat of a car at night, dashboard glow"),
    ("full body, standing, front view, plain white background",
     "full body standing facing the camera, plain white studio background"),
    ("full body, walking, side view, street, daytime",
     "full body walking, side view, city sidewalk in daytime"),
    ("full body, standing in the rain, night",
     "full body standing in the rain at night, wet street reflections"),
    ("full body, sitting on stairs, indoor",
     "full body sitting on stairs inside an old building, soft light"),
    ("close-up, casual white t-shirt, daylight",
     "close-up wearing a plain white t-shirt instead of his usual outfit, natural daylight, home interior"),
    ("medium shot, casual black hoodie, night",
     "medium shot wearing a black hoodie instead of his usual outfit, night street"),
    ("extreme close-up, eyes and face, cinematic lighting",
     "extreme close-up of his face and eyes, cinematic lighting, shallow depth of field"),
    ("medium shot, reading a book, library, warm light",
     "medium shot reading a book in a quiet library, warm light"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("character", choices=CHARACTERS)
    ap.add_argument("--per", type=int, default=1, help="จำนวนภาพต่อแบบ (seed ต่างกัน)")
    args = ap.parse_args()

    ch = CHARACTERS[args.character]
    out_dir = DATASET_DIR / args.character
    out_dir.mkdir(parents=True, exist_ok=True)
    qwen = rs.load_workflow("qwen_edit_api.json", "TextEncodeQwenImageEditPlus")
    input_dir = rs.COMFY_DIR / "input"

    # ภาพอ้างอิงต้นฉบับใส่ในชุดเทรนด้วย
    for name in ch["extra_refs"]:
        dst = out_dir / f"ref_{name}"
        shutil.copy(input_dir / name, dst)
        view = name.split("_", 1)[1].rsplit(".", 1)[0].replace("_", " ")
        dst.with_suffix(".txt").write_text(f"{ch['trigger']}, {view}, plain white background")

    total = len(VARIATIONS) * args.per
    n = 0
    for i, (caption, instruction) in enumerate(VARIATIONS, 1):
        for k in range(args.per):
            n += 1
            shot = {
                "id": f"{args.character}_{i:02d}_{k}",
                "refs": ch["refs"],
                "keyframe_prompt": (
                    f"The same man from image 1 ({ch['look']}), wearing {ch['outfit']} as in image 2 unless stated otherwise, "
                    f"{instruction}. Keep his face and hairstyle exactly the same as image 1. Only one person in the image"
                ),
            }
            wf = rs.build_keyframe(qwen, shot, "photorealistic, high detail, sharp focus", random.randint(1, 2**48))
            prefix = f"dataset/{args.character}/{shot['id']}"
            rs.set_output_prefix(wf, prefix)
            rs.wait(rs.queue(wf), f"[{n}/{total}] {shot['id']}")
            src = rs.newest(f"output/{prefix}*.png")
            dst = out_dir / f"{shot['id']}.png"
            shutil.copy(src, dst)
            dst.with_suffix(".txt").write_text(f"{ch['trigger']}, {caption}")

    print(f"\nเสร็จ! {out_dir}  — เปิดดูแล้วลบภาพที่ไม่เหมือน (ลบ .png กับ .txt คู่กัน) ให้เหลือ 20–40 ภาพ")


if __name__ == "__main__":
    main()
