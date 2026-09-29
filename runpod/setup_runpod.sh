#!/usr/bin/env bash
# ติดตั้ง ComfyUI + Wan 2.2 บน RunPod Pod (template "RunPod PyTorch")
# ติดตั้งไว้ใน /workspace (Volume) ปิด/เปิด Pod ใหม่ไม่ต้องโหลดซ้ำ
#
# ใช้ (ใน Web Terminal ของ Pod):
#   curl -fsSL <URL ของไฟล์นี้> -o setup_runpod.sh   # หรือ copy-paste
#   bash setup_runpod.sh           # ติดตั้ง + เปิด ComfyUI
#   bash setup_runpod.sh start     # เปิด ComfyUI อย่างเดียว (หลัง restart Pod)
set -euo pipefail

WS=/workspace
APP=$WS/ComfyUI
PORT=8188

start_comfy() {
  cd "$APP"
  source .venv/bin/activate
  pkill -f "main.py --listen" 2>/dev/null || true
  nohup python main.py --listen 0.0.0.0 --port $PORT > $WS/comfyui.log 2>&1 &
  echo ">> ComfyUI กำลังเปิด (log: $WS/comfyui.log)"
  echo ">> ไปที่หน้า Pod > Connect > HTTP Service [Port $PORT]"
}

if [[ "${1:-}" == "start" ]]; then start_comfy; exit 0; fi

nvidia-smi
apt-get update -qq && apt-get install -y -qq git ffmpeg aria2 python3-venv >/dev/null

cd $WS
# ซ่อมหลังย้าย Pod: ถ้าโค้ด ComfyUI ไม่ครบ ให้ clone ใหม่โดยเก็บ models/input/output/user ไว้
if [[ -d ComfyUI && ! -f ComfyUI/comfy/options.py ]]; then
  echo ">> โค้ด ComfyUI ไม่ครบ (อาจเกิดจากการย้าย Pod) — ติดตั้งโค้ดใหม่ เก็บงานเดิมไว้"
  mkdir -p $WS/_keep
  for d in models input output user; do [[ -d ComfyUI/$d ]] && mv ComfyUI/$d $WS/_keep/$d; done
  rm -rf ComfyUI
  git clone https://github.com/comfyanonymous/ComfyUI.git
  for d in models input output user; do
    [[ -d $WS/_keep/$d ]] && { rm -rf ComfyUI/$d; mv $WS/_keep/$d ComfyUI/$d; }
  done
  rmdir $WS/_keep 2>/dev/null || true
fi
[[ -d ComfyUI ]] || git clone https://github.com/comfyanonymous/ComfyUI.git
cd "$APP"
# ซ่อม venv ที่พัง (import torch ไม่ได้) ด้วยการสร้างใหม่
if [[ -d .venv ]] && ! .venv/bin/python -c "import torch" 2>/dev/null; then
  echo ">> Python environment เสีย — สร้างใหม่"
  rm -rf .venv
fi
[[ -d .venv ]] || python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -q -r requirements.txt
[[ -d custom_nodes/ComfyUI-Manager ]] || git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager

HF=https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files
FILES=(
  "diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
  "diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
  "text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
  "vae/wan_2.1_vae.safetensors"
  "loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
  "loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
)
# text-to-video (+28GB) โหลดเฉพาะเมื่อสั่ง WITH_T2V=1 bash setup_runpod.sh
if [[ "${WITH_T2V:-0}" == "1" ]]; then
  FILES+=(
    "diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors"
    "diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"
  )
fi
URLS=()
for f in "${FILES[@]}"; do URLS+=("$f|$HF/$f"); done

# Qwen Image Edit 2509 (+~30GB) สำหรับสร้าง keyframe จากภาพอ้างอิงตัวละคร: WITH_QWEN_EDIT=1 bash setup_runpod.sh
if [[ "${WITH_QWEN_EDIT:-0}" == "1" ]]; then
  QHF=https://huggingface.co/Comfy-Org
  URLS+=(
    "diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors|$QHF/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors"
    "text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors|$QHF/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"
    "vae/qwen_image_vae.safetensors|$QHF/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"
    "loras/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors|https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors"
  )
fi

# Qwen-Image (text-to-image, +~20GB) สำหรับใช้คู่กับ character LoRA: WITH_QWEN_IMAGE=1 bash setup_runpod.sh
if [[ "${WITH_QWEN_IMAGE:-0}" == "1" ]]; then
  QHF=https://huggingface.co/Comfy-Org
  URLS+=(
    "diffusion_models/qwen_image_fp8_e4m3fn.safetensors|$QHF/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors"
    "text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors|$QHF/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"
    "vae/qwen_image_vae.safetensors|$QHF/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"
    "loras/Qwen-Image-Lightning-8steps-V1.1.safetensors|https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-8steps-V1.1.safetensors"
  )
fi

failed=()
for entry in "${URLS[@]}"; do
  f="${entry%%|*}"; url="${entry#*|}"
  dest="models/$f"
  mkdir -p "$(dirname "$dest")"
  # -c: ไฟล์ที่ครบแล้วจะข้ามทันที ไฟล์ที่ขาดหาย/ไม่ครบ (เช่นหลังย้าย Pod) จะโหลดต่อให้
  echo ">> ตรวจ/ดาวน์โหลด $f"
  aria2c -q -x 16 -s 16 -c -d "$(dirname "$dest")" -o "$(basename "$dest")" "$url" || failed+=("$f")
done
if (( ${#failed[@]} )); then
  echo "!! ดาวน์โหลดไม่สำเร็จ (ชื่อไฟล์อาจเปลี่ยน ให้หาในหน้า Hugging Face ของ Comfy-Org):"
  printf '   %s\n' "${failed[@]}"
fi

start_comfy
