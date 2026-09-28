# EP01 — Shot list สำหรับ Wan 2.2 (แปลงจากพรอมต์ Seedance)

Wan 2.2 ทำได้ **ครั้งละ 1 ช็อต (~5 วินาที) และไม่มีเสียง** จึงแตกแต่ละ Scene เป็นช็อตย่อย
ทุกช็อตทำ 2 ขั้น:

1. **Keyframe** — สร้างภาพเฟรมแรกด้วย *Qwen Image Edit 2509* โดยใส่ภาพอ้างอิงตัวละคร (image 1 / image 2)
2. **Motion** — เอา keyframe เข้า *Wan 2.2 14B Image to Video* พร้อมพรอมต์การเคลื่อนไหว

บทพูด (`🎙`) ทำทีหลังด้วย TTS + lip-sync — ช็อตที่มีบทพูดให้เรนเดอร์ภาพที่ปากขยับเล็กน้อยไว้ก่อน

## ค่าคงที่ (ใส่ทุกช็อตให้ภาพต่อเนื่อง)

- **ขนาด (Wan):** 480×832 (9:16 แนวตั้ง) — Wan จะครอปกึ่งกลาง keyframe ให้เป็นสัดส่วนนี้เอง จึงควรให้ตัวละครอยู่กลางภาพ
- **ความต่อเนื่องของฉาก:** ใส่ `S1-2_keyframe.png` เป็นภาพอ้างอิงสถานที่ (image 2 หรือ 3) ทุกช็อตที่อยู่ในตรอก แล้วเขียนว่า `in the alley from image N` — ตรอกจะหน้าตาเดียวกันทุกช็อต
- **ต่อท้าย keyframe prompt ทุกช็อต (STYLE):**
  `vertical composition, subject centered, dark cinematic realism, neo-noir, moody low-key lighting, high contrast, deep shadows, rich textures, shot on 35mm film, photorealistic`
- **สถานที่ (ALLEY):** `a narrow dark alley at night, wet asphalt reflecting cold blue and faint red neon light, grimy brick walls, a green metal dumpster, steam rising from a vent`
- **Damian:** `the young man from image 1 (wavy blond hair, blue eyes, beige trench coat, cream knit sweater, dark jeans)`
- **Kairo:** `the man from image 2 (messy jet-black hair swept back with loose strands falling over his forehead, warm tan olive skin, thick dark eyebrows, sharp jawline, intense dark eyes, black three-piece suit, black shirt, dark red tie)`
- **Negative (Wan):** `bright lighting, daytime, cartoon, text, subtitles, watermark, split screen, collage, blurry face, distorted hands, extra limbs`

ภาพอ้างอิงที่ใช้: `damian_full_front.png` / `damian_face_front.png` = image 1, `kairo_full_front.png` / `kairo_face_front.png` = image 2

---

## Scene 1 — Damian แอบตามเก็บข้อมูล

### S1-1 · Tracking shot
- **Refs:** image 1 = damian_full_front
- **Keyframe:** `Damian walks cautiously through ALLEY, body slightly hunched, glancing over his shoulder, medium-wide shot from behind at shoulder height. STYLE`
- **Motion:** `The young man sneaks forward along the wet alley, looking around cautiously, the camera tracks smoothly behind him, steam drifts, puddles ripple under his boots`

### S1-2 · Static shot 🎙
- **Refs:** image 1 = damian_face_front
- **Keyframe:** `Damian crouches behind the green dumpster in ALLEY, peeking out with excited eyes, holding a small notebook, medium shot from the side. STYLE`
- **Motion:** `Static camera. The young man hides behind the dumpster, peeks out and whispers to himself with a small excited smile, his breath visible in the cold air`
- **🎙 Damian (กระซิบ):** "This is perfect for my book."
- ✅ **Rendered** — keyframe: `S1-2_keyframe.png` (Qwen Image Edit 2509, 944×1104) · Wan 2.2 I2V 480×560, 5.0s, turbo on · **noise_seed `358075559139979`**
  - Motion prompt ที่ใช้จริง: `Static camera. The young man hides behind the dumpster, peeks out and thinking to himself with a very small excited smile (keep this secret with himself) Just smil not push any action only stare in his front, his breath visible in the cold air, steam drifts slowly`

### S1-3 · Static shot
- **Refs:** image 1 = kairo_face_front, image 2 = S1-2_keyframe (ตรอก), image 3 = kairo_full_front (ชุด)
- **Keyframe:** `Kairo stands alone in the middle of ALLEY under a single flickering light, hands in pockets, calm and dangerous, full-body wide shot, slight low angle. STYLE`
- **Motion:** `Static camera. The man in the black suit stands still, slowly raises his head, the overhead light flickers, steam drifts around his legs`

### S1-4 · Push in 🎙
- **Refs:** image 1 = damian_face_front
- **Keyframe:** `Close-up of Damian behind the dumpster writing quickly in a small notebook with a pen, eyes focused, face lit by faint neon. STYLE`
- **Motion:** `Slow push in toward his face. The young man scribbles notes quickly, glances up then back down, murmuring to himself`
- **🎙 Damian:** "I need to capture every detail."

### S1-5 · Pan shot
- **Refs:** — (ไม่มีตัวละคร: ใส่ภาพใดก็ได้แล้วขึ้นต้นพรอมต์ด้วย `Replace the entire image with:` หรือใช้ Wan T2V)
- **Keyframe:** `Empty ALLEY, wet gritty ground, trash bags, rusted fire escape, puddles reflecting neon, wide shot. STYLE`
- **Motion:** `Slow horizontal pan from left to right across the wet gritty alley, water drips from a pipe, steam rises, neon reflections shimmer in puddles`

---

## Scene 2 — Damian รับมีดแทน Kairo

### S2-1 · Fast push in
- **Refs:** image 2 = kairo_full_side
- **Keyframe:** `A rough gang member in a dark hoodie charges from the shadows toward Kairo in ALLEY, gripping a tactical knife, Kairo seen from behind in the foreground, wide shot. STYLE`
- **Motion:** `Fast push in. The gang member sprints toward the man in the black suit, raising the knife, splashing through puddles`

### S2-2 · Close-up static 🎙
- **Refs:** image 1 = damian_face_front
- **Keyframe:** `Extreme close-up of Damian behind the dumpster, eyes wide in shock, mouth open mid-gasp. STYLE`
- **Motion:** `Static camera. The young man gasps in shock, his eyes widen, he shouts a warning`
- **🎙 Damian (ตะโกน):** "Look out!"

### S2-3 · Tracking shot
- **Refs:** image 1 = damian_full_side
- **Keyframe:** `Damian leaps out from behind the dumpster into ALLEY, trench coat flaring, running toward the camera, dynamic medium shot. STYLE`
- **Motion:** `The camera tracks as the young man bursts out from his hiding spot and runs forward, his trench coat flaring, splashing through puddles`

### S2-4 · Static shot
- **Refs:** image 1 = damian_full_front, image 2 = kairo_full_back
- **Keyframe:** `Damian throws himself in front of Kairo, arms spread to shield him, the attacker's knife swinging toward Damian's arm, Kairo behind them turning in surprise, medium-wide shot. STYLE`
- **Motion:** `Static camera. The young man steps in front of the man in the black suit, the attacker slashes, the young man flinches and clutches his arm, staggering back`

### S2-5 · Close-up static
- **Refs:** —
- **Keyframe:** `Close-up of a blood-stained tactical knife lying on wet asphalt, puddle reflecting neon, shallow depth of field. STYLE`
- **Motion:** `Static camera. The knife clatters onto the wet ground and settles, a drop of blood spreads in the puddle, rain ripples the surface`

---

## Scene 3 — Kairo จำได้

### S3-1 · Tracking shot
- **Refs:** image 2 = kairo_full_front
- **Keyframe:** `Kairo strikes the remaining gang member with a swift precise punch in ALLEY, the attacker falling backward, dynamic medium shot. STYLE`
- **Motion:** `The camera tracks as the man in the black suit effortlessly knocks out the attacker with one swift strike, the attacker collapses onto the wet ground`

### S3-2 · Static shot
- **Refs:** image 1 = damian_full_side, image 2 = kairo_full_side
- **Keyframe:** `Kairo kneels on the wet ground beside Damian, who lies unconscious with eyes closed and an injured arm, Kairo looking down at his face, medium shot. STYLE`
- **Motion:** `Static camera. The man in the black suit kneels slowly and reaches out to gently turn the young man's face toward the light`

### S3-3 · Push in 🎙
- **Refs:** image 2 = kairo_face_front
- **Keyframe:** `Extreme close-up of Kairo's face, intense dark eyes filled with recognition and longing, faint neon light on his cheekbones. STYLE`
- **Motion:** `Slow push in toward his eyes. The man's expression shifts from cold to stunned recognition, he whispers softly`
- **🎙 Kairo (เสียงต่ำ กระซิบ):** "It is you... after all these years."

### S3-4 · Pull out
- **Refs:** image 1 = damian_full_front, image 2 = kairo_full_front
- **Keyframe:** `Kairo stands in ALLEY carefully carrying the unconscious Damian in his arms, Damian's head resting against his chest, medium shot. STYLE`
- **Motion:** `Slow pull out. The man in the black suit carries the young man protectively and walks toward the alley exit, steam drifting around them`

### S3-5 · Tracking shot
- **Refs:** —
- **Keyframe:** `A sleek black luxury sedan on a dark wet city street at night, red taillights glowing, rear three-quarter view. STYLE`
- **Motion:** `The camera tracks as the black car pulls away and drives into the dark night, taillights streaking across the wet road`
