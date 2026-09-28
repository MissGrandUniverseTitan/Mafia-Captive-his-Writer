# Seedance ผ่าน BytePlus ModelArk API (จ่ายตามใช้จริง)

สคริปต์นี้เรียก Seedance ผ่าน API แทนการใช้เครดิตบนเว็บ ai.byteplus.com
จ่ายตามจำนวน token ที่ใช้จริง และได้ token ฟรีตอนสมัคร

## ตั้งค่าครั้งแรก
1. เข้า BytePlus Console แล้วไปที่ **ModelArk**
2. ไปที่ **Model activation / Model management** แล้วกดเปิดใช้โมเดล Seedance ที่ต้องการ
   - จดชื่อ model ID ที่หน้า console แสดงไว้ เช่น `seedance-1-0-pro-250528`
   - ชื่อเปลี่ยนตามเวอร์ชัน ถ้าต่างจากค่าเริ่มต้นในสคริปต์ ให้ใส่ผ่าน `--model` หรือ `SEEDANCE_MODEL`
3. ไปที่ **API Keys** แล้วสร้าง key
4. ตั้งค่า:
   ```bash
   cp seedance/.env.example seedance/.env   # แล้วใส่ ARK_API_KEY
   set -a; source seedance/.env; set +a
   ```

ต้องใช้ Python 3.8 ขึ้นไป และไม่ต้องติดตั้งแพ็กเกจเพิ่ม

## การใช้งาน
```bash
# ดู token/ราคาโดยประมาณก่อน (ไม่เรียก API ไม่เสียเงิน)
python seedance/seedance.py "a cat surfing at sunset" --resolution 1080p --duration 10 --estimate

# โหมดร่างราคาถูก: โมเดล fast + 480p ใช้ลองพรอมต์
python seedance/seedance.py "a cat surfing at sunset" --draft

# ได้พรอมต์ที่ชอบแล้ว ใช้ seed เดิมทำตัวจริง
python seedance/seedance.py "a cat surfing at sunset" --resolution 1080p --seed 12345

# image-to-video จากภาพเฟรมแรก (ไฟล์ในเครื่องหรือ URL ก็ได้)
python seedance/seedance.py "slow dolly-in, soft light" --image product.png --ratio 9:16
```

วิดีโอจะถูกบันทึกไว้ใน `outputs/`
ทุกงานจะถูกบันทึกลง `seedance/usage_log.csv` พร้อมจำนวน token ที่ใช้จริง ใช้ติดตามค่าใช้จ่ายได้

## คิดราคายังไง
ราคา = token ÷ 1,000,000 × ราคาต่อล้าน token ของโมเดลนั้น

token ≈ กว้าง × สูง × fps × วินาที ÷ 1024 ตัวอย่างโดยประมาณ:

| ความละเอียด | 5 วินาที | 10 วินาที |
|---|---|---|
| 480p | ~49k | ~97k |
| 720p | ~108k | ~216k |
| 1080p | ~243k | ~486k |

1080p แพงกว่า 480p ประมาณ **5 เท่า** จึงควรร่างที่ 480p ก่อนเสมอ

ถ้าตั้ง `SEEDANCE_PRICE_PER_M_TOKENS` ตามหน้า Pricing ของ ModelArk สคริปต์จะแสดงราคาเป็น $ ให้ด้วย

## เคล็ดลับประหยัด
- ใช้ `--estimate` ดูราคาก่อนสั่งทุกครั้ง
- ใช้ `--draft` ลองพรอมต์ แล้วค่อยใช้ Pro 1080p กับตัวที่ใช้จริง
- ใส่ `--seed` เดิมเพื่อให้ผลใกล้กับตัวร่าง
- ใช้ `--image` เพื่อคุมองค์ประกอบภาพ จะสุ่มใหม่น้อยลง
- ตั้ง **budget alert** ใน BytePlus Billing จะได้ไม่เผลอใช้เกินงบ
