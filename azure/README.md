# รัน Wan 2.2 บน Azure GPU (ใช้ Free Credit $200)

สคริปต์ชุดนี้สร้าง GPU VM บน Azure แล้วติดตั้ง ComfyUI + Wan 2.2 (14B, image-to-video / text-to-video) + LightX2V LoRA ที่ลดเหลือ 4 step
ไม่มีตัวกรองเนื้อหาจากผู้ให้บริการ

## ⚠️ ต้องทำก่อน (สำคัญที่สุด)
บัญชี Azure Free Trial มี **โควตา GPU = 0** ต้องทำ 2 ข้อนี้ก่อน ไม่งั้นสร้าง VM ไม่ได้:

1. **อัปเกรดเป็น Pay-As-You-Go**
   - ไปที่ Portal > Subscriptions > Upgrade
   - เครดิต $200 ที่เหลือยังใช้ได้ต่อ และจะตัดเงินจริงก็ต่อเมื่อเครดิตหมด
   - เครดิต Free Trial มีอายุ 30 วัน ให้เช็กวันหมดอายุด้วย
2. **ขอเพิ่มโควตา GPU**
   - ไปที่ Portal > Quotas > Compute แล้วเลือก region `Southeast Asia` (หรือ `East US` ซึ่งมักมีเครื่องว่างมากกว่า)
   - ขอตามรุ่นเครื่องในตารางข้างล่าง:

| VM | GPU | ราคาโดยประมาณ* | โควตาที่ต้องขอ |
|---|---|---|---|
| **Standard_NC24ads_A100_v4** (แนะนำ) | A100 80GB | ~$3.7/ชม. ปกติ, Spot ถูกกว่ามาก | *Standard NCADS_A100_v4 Family* = 24 vCPU (ถ้าใช้ Spot ขอ *Spot vCPUs* = 24 ด้วย) |
| Standard_NV36ads_A10_v5 | A10 24GB | ~$3.2/ชม. | *NVADSA10v5 Family* = 36 |
| Standard_NC4as_T4_v3 | T4 16GB | ~$0.5/ชม. | *NCASv3_T4 Family* = 4 (ช้ามากกับ 14B ใช้ทดลองได้) |

\*ราคาเปลี่ยนตาม region ให้เช็กที่ [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)

บัญชีใหม่อาจถูกปฏิเสธโควตา A100 ให้ลองขอ T4 ก่อนเพื่อสร้างประวัติการใช้งาน หรือเขียนเหตุผลว่าใช้ทำ "AI video generation research"

3. **ตั้ง Budget alert** ที่ Cost Management > Budgets เช่น แจ้งเตือนเมื่อใช้ถึง $150

## เช็กราคาและโควตา GPU
```bash
python3 azure/gpu_prices.py southeastasia eastus   # ราคาปกติ/Spot เรียงจากถูกสุด
az vm list-usage -l southeastasia -o table | grep -iE "NCADS|NVADS|NCAS|Spot"   # โควตาที่มี
```

## ติดตั้ง
ติดตั้ง [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) บนเครื่องคุณก่อน หรือใช้ **Cloud Shell** ใน Portal ได้เลย

```bash
az login
cd azure
./create_vm.sh                                   # A100 Spot
# หรือ: SIZE=Standard_NC4as_T4_v3 PRIORITY=Regular ./create_vm.sh

scp setup_comfyui.sh azureuser@<IP>:~
ssh azureuser@<IP> 'bash setup_comfyui.sh'       # รอบแรกลง driver แล้วรีบูต
ssh azureuser@<IP> 'bash setup_comfyui.sh'       # รอบสองลง ComfyUI + โหลดโมเดล (~40GB)
```

## ใช้งาน
```bash
ssh -L 8188:localhost:8188 azureuser@<IP>
```
เปิด http://localhost:8188 แล้วไปที่เมนู **Workflow > Browse Templates > Video**
เลือก **Wan 2.2 14B Image to Video** โดยใช้แบบที่มี LightX2V 4-step

ComfyUI เปิดเฉพาะผ่าน SSH tunnel จึงไม่เปิดพอร์ตให้คนอื่นเข้ามาได้

## 💸 ประหยัดเครดิต
```bash
./vm.sh stop     # เลิกใช้เมื่อไหร่ต้องสั่งทุกครั้ง (deallocate = หยุดคิดค่า GPU)
./vm.sh start    # เปิดใหม่ ไม่ต้องติดตั้งซ้ำ (IP อาจเปลี่ยน)
./vm.sh delete   # ลบทุกอย่างเมื่อเลิกใช้ถาวร
```
- **การ Shutdown ใน Ubuntu ไม่หยุดคิดเงิน** ต้องสั่ง `./vm.sh stop` หรือกด Stop ใน Portal เท่านั้น
- ตั้งปิดเครื่องอัตโนมัติไว้ทุกเที่ยงคืนเวลาไทย เผื่อลืม
- **Spot VM** ถูกกว่ามาก แต่ Azure อาจดึงเครื่องคืนกลางทาง ไฟล์ในดิสก์ไม่หาย ให้สั่ง start ใหม่ได้
- ร่างที่ 480p ก่อน แล้วค่อยเรนเดอร์ 720p เฉพาะช็อตที่ใช้จริง

ประมาณการ: A100 แบบปกติ $200 ≈ 50 ชั่วโมง ถ้าช็อตละ 5 วินาทีใช้เวลาเรนเดอร์ไม่กี่นาที จะได้หลายร้อยช็อตหรือมากกว่า
