#!/usr/bin/env bash
# รันบน VM: ติดตั้ง NVIDIA driver, ComfyUI และโมเดล Wan 2.2
# รันซ้ำได้ ถ้าเครื่องรีบูตหลังลง driver ให้ ssh กลับมารันคำสั่งเดิมอีกครั้ง
set -euo pipefail

if ! command -v nvidia-smi >/dev/null || ! nvidia-smi >/dev/null 2>&1; then
  echo ">> ติดตั้ง NVIDIA driver (เครื่องจะรีบูต แล้วให้รันสคริปต์นี้อีกครั้ง)"
  sudo apt-get update
  # เลือก server driver เวอร์ชันใหม่สุดที่มีใน repo
  ver=$(apt-cache search --names-only '^nvidia-driver-[0-9]+-server$' | grep -o '[0-9]\+' | sort -n | tail -1)
  sudo apt-get install -y "nvidia-driver-${ver}-server" "nvidia-utils-${ver}-server"
  sudo reboot
fi
nvidia-smi

sudo apt-get install -y git python3-venv python3-pip ffmpeg aria2

cd ~
[[ -d ComfyUI ]] || git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
[[ -d custom_nodes/ComfyUI-Manager ]] || git clone https://github.com/ltdrdata/ComfyUI-Manager.git custom_nodes/ComfyUI-Manager

# ---- โมเดล Wan 2.2 (ไฟล์ที่ Comfy-Org จัดแพ็กไว้ให้ ComfyUI) ----
HF=https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files
FILES=(
  "diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
  "diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
  "diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors"
  "diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"
  "text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
  "vae/wan_2.1_vae.safetensors"
  "loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
  "loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
)
failed=()
for f in "${FILES[@]}"; do
  dest="models/$f"
  [[ -s "$dest" ]] && { echo "มีแล้ว: $f"; continue; }
  mkdir -p "$(dirname "$dest")"
  echo ">> ดาวน์โหลด $f"
  aria2c -x 16 -s 16 -c -d "$(dirname "$dest")" -o "$(basename "$dest")" "$HF/$f" || failed+=("$f")
done
if (( ${#failed[@]} )); then
  echo "!! ดาวน์โหลดไม่สำเร็จ (ชื่อไฟล์อาจเปลี่ยน ให้หาใน https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged):"
  printf '   %s\n' "${failed[@]}"
fi

# ---- ให้ ComfyUI เปิดเองทุกครั้งที่เปิดเครื่อง ----
sudo tee /etc/systemd/system/comfyui.service >/dev/null <<UNIT
[Unit]
Description=ComfyUI
After=network.target
[Service]
User=$USER
WorkingDirectory=$HOME/ComfyUI
ExecStart=$HOME/ComfyUI/.venv/bin/python main.py --listen 127.0.0.1 --port 8188
Restart=always
[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now comfyui

echo
echo "เสร็จแล้ว! บนเครื่องคุณรัน:  ssh -L 8188:localhost:8188 azureuser@<IP>"
echo "แล้วเปิด http://localhost:8188"
