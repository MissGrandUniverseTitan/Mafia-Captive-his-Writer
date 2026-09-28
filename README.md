# Mafia Captive his Writer

ซีรีส์ BL แนว neo-noir ที่ผลิตด้วย AI (ตัวละคร: **Kairo** มาเฟีย / **Damian** นักเขียนนิยายระทึกขวัญ)

## โครงสร้าง
| โฟลเดอร์ | เนื้อหา |
|---|---|
| `characters/` | ภาพอ้างอิงตัวละคร (หน้าตรง/ด้านข้าง/เต็มตัว) ตัดจาก character sheet |
| `episodes/` | Shot list รายตอน — พรอมต์ keyframe (Qwen Image Edit) + motion (Wan 2.2) |
| `runpod/` | สคริปต์ติดตั้ง ComfyUI + Wan 2.2 (+ Qwen Image Edit) บน RunPod |
| `azure/` | สคริปต์สร้าง GPU VM บน Azure (ทางเลือก) |
| `seedance/` | CLI เรียก Seedance ผ่าน BytePlus ModelArk API (จ่ายตามใช้จริง) |

## Pipeline
1. ภาพอ้างอิงตัวละคร → **Qwen Image Edit 2509** → keyframe ของแต่ละช็อต
2. keyframe → **Wan 2.2 14B I2V** → วิดีโอช็อตละ ~5 วินาที
3. เสียงพากย์ (TTS) + lip-sync → ตัดต่อ / VFX / ซับ ใน DaVinci Resolve

เริ่มที่ [`runpod/setup_runpod.sh`](runpod/setup_runpod.sh) และ [`episodes/ep01_shotlist.md`](episodes/ep01_shotlist.md)
