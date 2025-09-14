#!/usr/bin/env python3
"""
모든 Bluetooth LE 디바이스 스캔
"""

import asyncio
from bleak import BleakScanner

async def scan_all_devices():
    """모든 Bluetooth LE 디바이스 스캔"""
    print("🔍 모든 Bluetooth LE 디바이스 스캔 중...")
    print("=" * 60)

    devices = await BleakScanner.discover(timeout=15.0)

    if not devices:
        print("❌ Bluetooth LE 디바이스를 찾을 수 없습니다.")
        return

    print(f"✅ {len(devices)}개의 디바이스를 발견했습니다:\n")

    for i, device in enumerate(devices, 1):
        name = device.name if device.name else "Unknown"
        # RSSI는 advertisement_data에서 가져와야 함
        rssi = "N/A"
        if hasattr(device, 'rssi') and device.rssi is not None:
            rssi = device.rssi

        print(f"{i:2d}. {name}")
        print(f"    주소: {device.address}")
        print(f"    RSSI: {rssi} dBm")

        # TESSEN 관련 디바이스 강조
        if "TESSEN" in name.upper() or "TENNIS" in name.upper():
            print("    🎾 TESSEN 관련 디바이스!")

        print()

if __name__ == "__main__":
    asyncio.run(scan_all_devices())
