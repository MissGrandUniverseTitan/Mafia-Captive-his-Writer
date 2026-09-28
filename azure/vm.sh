#!/usr/bin/env bash
# เปิด/ปิด/ลบ VM   ใช้: ./vm.sh start|stop|status|delete
# stop = deallocate (หยุดคิดค่า GPU; ค่าดิสก์ยังคิดเล็กน้อย)
set -euo pipefail
RG="${RG:-wan-video-rg}"
VM="${VM:-wan-gpu}"
case "${1:-}" in
  start)  az vm start -g "$RG" -n "$VM" && az vm show -d -g "$RG" -n "$VM" --query publicIps -o tsv ;;
  stop)   az vm deallocate -g "$RG" -n "$VM" ;;
  status) az vm show -d -g "$RG" -n "$VM" --query "{state:powerState, ip:publicIps, size:hardwareProfile.vmSize}" -o table ;;
  delete) az group delete -n "$RG" --yes ;;
  *) echo "ใช้: $0 start|stop|status|delete"; exit 1 ;;
esac
