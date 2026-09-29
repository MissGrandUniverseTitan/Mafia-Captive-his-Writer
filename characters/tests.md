# Character motion tests (Wan 2.2 I2V)

| ตัวละคร | ภาพต้นทาง | ขนาด | seed | หมายเหตุ |
|---|---|---|---|---|
| Damian | `damian_face_front.png` | 480×576 | `145727566222741` | ก้มหน้าเศร้า สีหน้าเป็นธรรมชาติ — พรอมต์แบบขยับน้อย (ชำเลือง/เอียงหัวเล็กน้อย) ไม่ทำให้คอบิด |

**บทเรียน:** อย่าสั่งให้หันหัวมาก ๆ จากภาพครอปแน่น (เคยได้คอบิด) — ให้ keyframe อยู่ในท่าใกล้ตอนจบการเคลื่อนไหวอยู่แล้ว

## LoRA tests (Qwen)

| LoRA | โมเดล | seed | ผล |
|---|---|---|---|
| `kairo_qwen_lora_000002000` strength 1.0 | Qwen Image Edit 2509 (ใช้แทน Qwen-Image ชั่วคราว) | `84894020179489` | ✅ มี LoRA = หน้า Kairo ตรง character sheet (ผมดำยุ่ง ผิวแทน กรามคม) · ไม่มี LoRA = ได้หน้าผู้ชายเอเชียทั่วไป → LoRA ทำงาน |

prompt: `k41ro man standing in a dark rainy alley at night, black three-piece suit, dark red tie, looking at the camera, cinematic neo-noir lighting, photorealistic` · 832×1216 · 20 steps · cfg 2.5
| `damian_qwen_lora_000002000` strength 1.0 | Qwen Image Edit 2509 | (สุ่ม) | ✅ ผมบลอนด์หยักศก ตาฟ้า หน้าอ่อน เทรนช์โค้ต+สเวตเตอร์ครีม ตรง character sheet |
