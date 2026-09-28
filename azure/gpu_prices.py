#!/usr/bin/env python3
"""ดูราคา GPU VM (Linux) บน Azure แบบปกติและแบบ Spot เรียงจากถูกไปแพง

ใช้ Azure Retail Prices API (สาธารณะ ไม่ต้อง login) รันใน Cloud Shell ได้เลย
    python3 gpu_prices.py                       # southeastasia, eastus, westus2
    python3 gpu_prices.py japaneast koreacentral
"""

import json
import sys
import urllib.parse
import urllib.request

# VRAM ต่อเครื่อง และรันงาน Drama studio (Wan 2.2 14B) ได้ไหม
GPU_INFO = {
    "Standard_NC4as_T4_v3": ("T4 16GB", "RAM 28GB ไม่พอ 14B / ใช้ Wan 5B ทดลองได้"),
    "Standard_NC8as_T4_v3": ("T4 16GB", "14B ได้แบบ GGUF+offload ช้ามาก"),
    "Standard_NC16as_T4_v3": ("T4 16GB", "14B ได้แบบ GGUF+offload ช้ามาก"),
    "Standard_NV36ads_A10_v5": ("A10 24GB", "✅ ขั้นต่ำที่ใช้งานจริงได้ (fp8+offload)"),
    "Standard_NV72ads_A10_v5": ("2x A10 24GB", "✅ ได้ (ใช้ได้ทีละ GPU)"),
    "Standard_NC24ads_A100_v4": ("A100 80GB", "✅✅ แนะนำ เร็ว ไม่ต้อง offload"),
    "Standard_NC48ads_A100_v4": ("2x A100 80GB", "✅✅ เกินจำเป็น"),
    "Standard_NC40ads_H100_v5": ("H100 94GB", "✅✅ เร็วสุด แพง"),
    "Standard_NC6s_v3": ("V100 16GB", "14B ได้แบบ offload ช้า"),
}

API = "https://prices.azure.com/api/retail/prices"


def fetch(region):
    flt = (
        "serviceName eq 'Virtual Machines' and priceType eq 'Consumption' "
        f"and armRegionName eq '{region}'"
    )
    url = f"{API}?{urllib.parse.urlencode({'$filter': flt})}"
    while url:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.load(resp)
        yield from data["Items"]
        url = data.get("NextPageLink")


def main():
    regions = sys.argv[1:] or ["southeastasia", "eastus", "westus2"]
    rows = {}
    for region in regions:
        print(f"กำลังดึงราคา {region} ...", file=sys.stderr)
        for item in fetch(region):
            sku = item["armSkuName"]
            if sku not in GPU_INFO or "Windows" in item["productName"] or "Low Priority" in item["skuName"]:
                continue
            kind = "spot" if "Spot" in item["skuName"] else "regular"
            rows.setdefault((region, sku), {})[kind] = item["retailPrice"]

    def sort_key(entry):
        prices = entry[1]
        return prices.get("spot", prices.get("regular", 1e9))

    print(f"\n{'region':<14} {'VM':<26} {'GPU':<13} {'ปกติ $/ชม.':>11} {'Spot $/ชม.':>11}  Wan 2.2 14B")
    for (region, sku), prices in sorted(rows.items(), key=sort_key):
        gpu, note = GPU_INFO[sku]
        reg = f"{prices['regular']:.2f}" if "regular" in prices else "-"
        spot = f"{prices['spot']:.2f}" if "spot" in prices else "-"
        print(f"{region:<14} {sku:<26} {gpu:<13} {reg:>11} {spot:>11}  {note}")


if __name__ == "__main__":
    main()
