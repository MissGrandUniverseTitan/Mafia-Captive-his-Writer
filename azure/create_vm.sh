#!/usr/bin/env bash
# สร้าง GPU VM บน Azure สำหรับรัน ComfyUI + Wan 2.2
# ต้องมี Azure CLI และ login แล้ว (az login)
#
# ตัวอย่าง:
#   ./create_vm.sh                                  # A100 80GB แบบ Spot (ถูกสุด ถ้ามีโควตา)
#   SIZE=Standard_NC4as_T4_v3 PRIORITY=Regular ./create_vm.sh   # T4 16GB ถ้าได้โควตาแค่นี้
set -euo pipefail

RG="${RG:-wan-video-rg}"
VM="${VM:-wan-gpu}"
LOCATION="${LOCATION:-southeastasia}"
SIZE="${SIZE:-Standard_NC24ads_A100_v4}"
PRIORITY="${PRIORITY:-Spot}"            # Spot หรือ Regular
DISK_GB="${DISK_GB:-256}"
SHUTDOWN_UTC="${SHUTDOWN_UTC:-1700}"    # ปิดเครื่องอัตโนมัติทุกวัน 17:00 UTC = เที่ยงคืนเวลาไทย

az group create -n "$RG" -l "$LOCATION" -o none

spot_args=()
if [[ "$PRIORITY" == "Spot" ]]; then
  spot_args=(--priority Spot --eviction-policy Deallocate --max-price -1)
fi

az vm create -g "$RG" -n "$VM" \
  --image Ubuntu2204 \
  --size "$SIZE" \
  --security-type Standard \
  --os-disk-size-gb "$DISK_GB" \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard \
  ${spot_args[@]+"${spot_args[@]}"} \
  -o table

az vm auto-shutdown -g "$RG" -n "$VM" --time "$SHUTDOWN_UTC" -o none

IP=$(az vm show -d -g "$RG" -n "$VM" --query publicIps -o tsv)
cat <<MSG

สร้าง VM เสร็จแล้ว: $IP
ขั้นต่อไป:
  scp setup_comfyui.sh azureuser@$IP:~
  ssh azureuser@$IP 'bash setup_comfyui.sh'
MSG
