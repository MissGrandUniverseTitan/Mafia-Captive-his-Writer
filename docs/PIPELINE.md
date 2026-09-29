# คู่มือผลิตซีรีส์ด้วย AI — Mafia Captive his Writer

> สรุปทุกขั้นตอนที่ทำจริงในโปรเจคนี้ + บทเรียน/ปัญหาที่เจอ อัปเดตต่อเนื่องจนจบโปรเจค
> อัปเดตล่าสุด: 2026-09-29

---

## 0. ภาพรวม

```
Character sheet ──► ตัดภาพอ้างอิง (characters/)
        │
        ├─► Qwen Image Edit 2509 ──► keyframe ของแต่ละช็อต ──► Wan 2.2 I2V ──► วิดีโอช็อตละ ~5 วิ
        │                                   ▲
        └─► ชุดภาพเทรน ──► Character LoRA ──┘ (Qwen-Image + LoRA = หน้าตัวละครนิ่งทุกช็อต)
                                                           │
                                   เสียงพากย์ (TTS) + lip-sync ──► ตัดต่อ/VFX/ซับ ──► เผยแพร่
```

| ทำไมไม่ใช้ Seedance (BytePlus) | ทางที่ใช้แทน |
|---|---|
| แพง (~$4.6/คลิป 10 วิ บนเว็บ) | รันโมเดล open-weight เองบน GPU เช่า ~$0.74/ชม. |
| guardrail บล็อกฉากแรง/เลือด ("sensitive information") | Wan 2.2 / Qwen ไม่มีตัวกรองในตัว |
| คุมหน้าตัวละครข้ามช็อตยาก | Character LoRA |

---

## 1. เครื่องมือและค่าใช้จ่าย

| ส่วน | ใช้อะไร | ราคา (ประมาณ) |
|---|---|---|
| GPU ทำงานหลัก | RunPod · RTX 4090 24GB · template **RunPod PyTorch 2.8 (CUDA 12.8)** | $0.74–0.76/ชม. |
| GPU เทรน LoRA | RunPod · **L40 48GB / A100 80GB** · template **AI Toolkit (ostris)** | $0.82–1.62/ชม. |
| พื้นที่เก็บ | Volume ของ Pod (แนะนำเปลี่ยนเป็น Network Volume) | ~$0.03–0.04/ชม. ตอนปิด |
| UI สร้างภาพ/วิดีโอ | ComfyUI (เปิดผ่าน port 8188) | ฟรี |
| สคริปต์/ไฟล์ทั้งหมด | repo นี้ | ฟรี |

ต้นทุนจริงที่ผ่านมา: คลิปทดสอบ + keyframe + วิดีโอ Scene 1 ใช้ GPU ไม่กี่ชั่วโมง, เทรน LoRA Kairo ~1.5 ชม. บน A100

> ⚠️ RunPod เป็นระบบเติมเงิน — เงินหมด Pod จะถูกหยุด และถ้าติดลบนาน Volume อาจถูกลบ → เติมเงินก่อนเริ่มงานทุกครั้ง

---

## 2. ติดตั้ง Pod หลัก (ComfyUI + Wan 2.2 + Qwen)

1. RunPod → Deploy → GPU **RTX 4090** → template **RunPod PyTorch 2.8**
2. **Container Disk 30GB, Volume ≥150GB** (100GB ไม่พอเมื่อมีทั้ง Wan + Qwen Edit + Qwen-Image)
3. Edit template → Exposed HTTP ports: `8888,8188`
4. เปิด Jupyter (port 8888) → Terminal:

```bash
cd /workspace && \
curl -fsSLO https://raw.githubusercontent.com/MissGrandUniverseTitan/Mafia-Captive-his-Writer/main/runpod/setup_runpod.sh && \
WITH_QWEN_EDIT=1 WITH_QWEN_IMAGE=1 bash setup_runpod.sh
```

| ตัวเลือก | ได้อะไร | ขนาด |
|---|---|---|
| (พื้นฐาน) | ComfyUI + Wan 2.2 14B I2V + LightX2V 4-step | ~36GB + venv ~12GB |
| `WITH_QWEN_EDIT=1` | Qwen Image Edit 2509 + Lightning 4-step | +~30GB |
| `WITH_QWEN_IMAGE=1` | Qwen-Image (text-to-image) + Lightning 8-step — ใช้คู่ LoRA | +~21GB |
| `WITH_T2V=1` | Wan 2.2 text-to-video | +~28GB |

5. เปิด ComfyUI: Connect → HTTP Service [8188]
6. ครั้งต่อไปหลัง Start Pod: `bash /workspace/setup_runpod.sh start`

สคริปต์รันซ้ำได้ และ **ซ่อมตัวเองหลังย้าย Pod** (โค้ด ComfyUI ไม่ครบ / venv เสีย / ไฟล์โมเดลไม่ครบ → โหลดต่อให้)

---

### 2.1 แนะนำ: ใช้ Network Volume (แก้ปัญหาย้าย Pod / พื้นที่เต็ม)

1. Storage → Network Volumes → New: เลือก **datacenter ที่มีทั้ง RTX 4090 และ L40/A100** · 150GB · ชื่อ `mafia-vol` (~$0.07/GB/เดือน)
2. Deploy → เลือก Network Volume `mafia-vol` → GPU 4090 → template PyTorch 2.8 → Container 30GB → ports `8888,8188` → mount `/workspace`
3. รัน `setup_runpod.sh` ตามข้อ 2
4. ย้ายงานจาก Pod เดิม: `tar czf carry.tgz datasets workflows ComfyUI/input ComfyUI/output ep01_scene1.json && runpodctl send carry.tgz` → Pod ใหม่ `runpodctl receive <code> && tar xzf carry.tgz`
5. Pod เทรน LoRA ต่อ Network Volume เดียวกันได้ → ชุดภาพ/LoRA อยู่ที่เดียวกัน ไม่ต้องส่งไฟล์ไปมา

> ส่งไฟล์ใหญ่ (LoRA 576MB) ใช้ `runpodctl send/receive` ดีกว่าอัปโหลดผ่าน Jupyter และเช็กขนาดไฟล์ทุกครั้ง (`ls -l`) — เคยได้ไฟล์ 0 byte เพราะอัปโหลดตอน Volume เต็ม

## 3. ตัวละคร

1. ตัด character sheet เป็นภาพแยก → `characters/` (หน้าตรง, หน้าด้านข้าง, เต็มตัว หน้า/ข้าง/หลัง) — ตัดตัวหนังสือ/แถบสี/ลายน้ำออก
2. โหลดเข้า ComfyUI:

```bash
cd /workspace/ComfyUI/input && for n in damian kairo; do for v in full_front full_side full_back face_front face_profile; do curl -fsSLO https://raw.githubusercontent.com/MissGrandUniverseTitan/Mafia-Captive-his-Writer/main/characters/${n}_${v}.png; done; done
```

| ตัวละคร | คำบรรยายที่ใช้ในพรอมต์ |
|---|---|
| **Kairo** | messy jet-black hair swept back with loose strands falling over his forehead, warm tan olive skin, thick dark eyebrows, sharp jawline, intense dark eyes · black three-piece suit, black shirt, dark red tie |
| **Damian** | voluminous tousled wavy dirty-blond hair, ear-length messy curls, fair skin, blue eyes · beige trench coat, cream knit sweater, dark jeans |

---

## 4. แปลงพรอมต์ Seedance → Shot list

พรอมต์แบบ Seedance (หลายช็อต + บทพูดในคลิปเดียว) ใช้กับ Wan ตรง ๆ ไม่ได้ → แตกเป็น **ช็อตละ 1 คลิป ~5 วิ** แต่ละช็อตมี:

- **keyframe prompt** → Qwen Image Edit (ใส่ภาพอ้างอิงเป็น image 1/2/3)
- **motion prompt** → Wan 2.2 I2V
- **บทพูด 🎙** → ทำเสียงทีหลัง

ไฟล์: [`episodes/ep01_shotlist.md`](../episodes/ep01_shotlist.md) (อ่าน) และ [`episodes/ep01_scene1.json`](../episodes/ep01_scene1.json) (ให้สคริปต์ใช้)

มาตรฐานที่ตกลงกัน:
- สัดส่วน **9:16 → Wan 480×832** (Wan ครอปกึ่งกลาง keyframe ให้เอง)
- ต่อท้าย keyframe ทุกช็อต: `vertical composition, subject centered, dark cinematic realism, neo-noir, moody low-key lighting, high contrast, deep shadows, photorealistic`
- ใช้ `S1-2_keyframe.png` เป็น **ภาพอ้างอิงสถานที่** ทุกช็อตในตรอก → ฉากต่อเนื่องกัน

---

## 5. เรนเดอร์ทีละหลายช็อต (คำสั่งเดียว)

```bash
cd /workspace && \
curl -fsSLO https://raw.githubusercontent.com/MissGrandUniverseTitan/Mafia-Captive-his-Writer/main/tools/render_shots.py && \
curl -fsSLO https://raw.githubusercontent.com/MissGrandUniverseTitan/Mafia-Captive-his-Writer/main/episodes/ep01_scene1.json

python3 render_shots.py ep01_scene1.json --stage keyframe            # 1) ทำ keyframe ทุกช็อต → เปิดดู
python3 render_shots.py ep01_scene1.json --stage keyframe --only S1-3 --redo-keyframes   # ทำใหม่เฉพาะช็อต
python3 render_shots.py ep01_scene1.json --stage video --seeds 2      # 2) วิดีโอ ช็อตละ 2 seed
```

- ครั้งแรกต้อง **กด Run workflow Qwen Edit และ Wan ใน ComfyUI อย่างละ 1 ครั้ง** → สคริปต์ดึง workflow จากประวัติมาเก็บที่ `/workspace/workflows/` (ประวัติหายเมื่อ ComfyUI restart)
- ผลลัพธ์: `ComfyUI/input/S1-x_keyframe.png`, `ComfyUI/output/ep01/S1-x_seed<seed>_*.mp4`, log seed ที่ `ComfyUI/output/ep01/render_log.csv`

---

## 6. Character LoRA

### 6.1 สร้างชุดภาพเทรน (บน Pod หลัก)
```bash
cd /workspace && curl -fsSLO https://raw.githubusercontent.com/MissGrandUniverseTitan/Mafia-Captive-his-Writer/main/tools/make_dataset.py
python3 make_dataset.py kairo --per 2 && python3 make_dataset.py damian --per 2
```
- ได้ 24 แบบ × 2 (มุม/อารมณ์/แสง/ขนาดช็อต/ชุดลำลอง) + ภาพ character sheet พร้อมไฟล์ caption `.txt`
- **คัดภาพที่หน้า/ผมไม่เหมือนทิ้ง** (ลบ .png + .txt คู่กัน) ให้เหลือ 20–40 ภาพ
- trigger word: Kairo = `k41ro man`, Damian = `d4mian man`

### 6.2 เทรน (Pod แยก)
1. Deploy: **L40 48GB** (RAM 250GB) หรือ A100 · template **AI Toolkit** · Container 60GB · Volume 20GB (mount ที่ `/mnt`)
   - ❌ หลีกเลี่ยง A40/A6000 (RAM 50GB อาจไม่พอโหลดโมเดล) และการ์ด 24–32GB
2. เปิด AI Toolkit (port 8675) → Datasets → อัปโหลดภาพ + .txt
3. New Job:

| ช่อง | ค่า |
|---|---|
| Model Architecture | **Qwen-Image** |
| Trigger Word | `k41ro man` / `d4mian man` |
| Steps | **2000** (หน้าเหมือนแล้วตั้งแต่ ~1500–2000) |
| Save Every | 500 |
| Quantize | qfloat8 (ค่าเริ่มต้น) |
| Linear Rank / LR | 32 / 0.0001 (ค่าเริ่มต้น) |
| Resolution | 768 + 1024 |
| Show Advanced → `training_folder` | `/mnt/output` (ไม่งั้นไฟล์อยู่ใน `/app/...` จะหายเมื่อ Pod หยุด) |

4. รัน **ทีละ Job** · ดาวน์โหลด checkpoint ระหว่างทาง
5. เสร็จแล้ว **Terminate** (ไม่ใช่ Stop)

### 6.3 ใช้งาน
- วาง `.safetensors` ที่ `/workspace/ComfyUI/models/loras/`
- ComfyUI: template **Qwen-Image** → เพิ่ม **LoraLoaderModelOnly** ต่อระหว่าง Load Diffusion Model กับกล่องถัดไป → strength 1.0 → พรอมต์ขึ้นต้นด้วย trigger word
- ส่งไฟล์ระหว่าง Pod/เครื่อง: `runpodctl send <file>` → อีกฝั่ง `runpodctl receive <code>`

สถานะ: Kairo ✅ (step 500–2000) · Damian ⏳

---

## 7. Seed & การบันทึก

- `noise_seed` = จุดตั้งต้นการสุ่ม · seed เดิม + ค่าเดิม = คลิปเดิม
- ใน template Wan แบบ subgraph เลขในแผง Parameters คือเลขที่ใช้จริงและไม่เปลี่ยนเอง
- ถ้าไม่แน่ใจ: ลากไฟล์ผลลัพธ์ (png/mp4) กลับเข้า ComfyUI จะได้ workflow + seed ที่ใช้จริง
- บันทึกไว้ที่ `episodes/ep01_shotlist.md` และ `characters/tests.md`

---

## 8. บทเรียน / ปัญหาที่เจอ

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| คอตัวละครบิด | สั่งหันหัวมาก จากภาพครอปแน่น + turbo | ขยับน้อยลง, keyframe อยู่ในท่าใกล้ตอนจบ, เปลี่ยน seed, ปิด turbo ตอนเรนเดอร์จริง |
| พื้นหลังขาวตาม character sheet | I2V ใช้ภาพที่ใส่เป็นเฟรมแรก | ทำ keyframe ฉากจริงด้วย Qwen Edit ก่อน |
| หน้า/ผมเพี้ยนใน keyframe | ภาพอ้างอิงหน้าเล็ก (ภาพเต็มตัว/ด้านหลัง) | ใช้ภาพหน้าเป็น image 1, ภาพชุดเป็น image 3, บรรยายผมชัด ๆ, ต่อท้าย "Keep his face and hairstyle exactly the same as image 1" → ระยะยาวใช้ LoRA |
| negative prompt ไม่มีผล | turbo/LightX2V ใช้ CFG 1 | แก้ที่ positive prompt / seed หรือปิด turbo |
| Start Pod แล้ว "GPUs no longer available" | GPU ถูกคนอื่นเช่าตอน Pod ปิด | Migrate แล้ว **รอจนแถบย้ายหาย** ค่อยรันสคริปต์ → ระยะยาวใช้ **Network Volume** |
| หลังย้าย Pod ไฟล์หาย (`No module named comfy.options`, venv เล็ก) | ย้ายข้อมูลไม่ครบ | `setup_runpod.sh` เวอร์ชันใหม่ซ่อมให้อัตโนมัติ |
| ดาวน์โหลดโมเดลไม่สำเร็จ / ComfyUI ไม่ตอบ | Volume 100GB เต็ม (`df` ไม่โชว์โควตาจริง) | ขยาย Volume ≥150GB, ลบ `/workspace/.cache/pip` |
| GPU 48GB เต็ม | คนใช้เยอะ | ลอง Secure/Community, รุ่นอื่น (L40, RTX 6000 Ada, A100) |
| LoRA หายตอน Pod เทรนหยุด | AI Toolkit เก็บไว้ใน `/app` (ดิสก์เครื่อง) | ตั้ง `training_folder: /mnt/output` หรือคัดลอกไป `/mnt` |
| LoRA ขึ้น "safetensors header is incomplete" | อัปโหลดตอน Volume เต็ม ได้ไฟล์ 0 byte | เช็ก `ls -l` ให้ ~576MB, ส่งใหม่ด้วย `runpodctl` |
| ช่องเลือกไฟล์ใน Load Image ไม่อัปเดต | ComfyUI ไม่ refresh เอง | กด `R` หรือ F5 |

---

## 9. ขั้นต่อไป (TODO)

- [ ] เทรน LoRA Damian
- [ ] ขยาย Volume / ย้ายไป Network Volume แล้วติดตั้ง Qwen-Image
- [ ] ทดสอบ LoRA → ปรับ `render_shots.py` ให้สร้าง keyframe ด้วย Qwen-Image + LoRA
- [ ] เรนเดอร์วิดีโอ Scene 1 (480×832) + เลือก seed
- [ ] Scene 2–3 (ช็อตสองคนในเฟรมเดียว: ใช้ Qwen Edit ช่วย)
- [ ] เสียงพากย์ (IndexTTS2 / CosyVoice) + lip-sync (Wan S2V / InfiniteTalk)
- [ ] Upscale (SeedVR2) + เพิ่ม fps (RIFE) + ตัดต่อ/VFX/ซับ ใน DaVinci Resolve
