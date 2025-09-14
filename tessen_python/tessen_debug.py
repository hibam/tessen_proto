#!/usr/bin/env python3
"""
TESSEN 센서 디버깅 프로그램
GATT 서비스와 특성 확인
"""

import asyncio
import struct
from bleak import BleakClient, BleakScanner

# TESSEN 센서 UUID 정보
TESSEN_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SENSOR_DATA_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
CONFIG_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"

async def debug_tessen_sensor():
    """TESSEN 센서 디버깅"""
    print("🔍 TESSEN 센서 디버깅 시작...")
    print("=" * 50)

    # 1. 디바이스 스캔
    print("1. 디바이스 스캔 중...")
    devices = await BleakScanner.discover(timeout=10.0)
    tessen_device = None

    for device in devices:
        if device.name and "TESSEN" in device.name.upper():
            tessen_device = device
            print(f"✅ TESSEN 디바이스 발견: {device.name} ({device.address})")
            break

    if not tessen_device:
        print("❌ TESSEN 센서를 찾을 수 없습니다.")
        return

    # 2. 연결
    print("\n2. 연결 시도...")
    client = BleakClient(tessen_device.address)

    try:
        await client.connect()
        print("✅ 연결 성공!")

        # 3. GATT 서비스 확인
        print("\n3. GATT 서비스 확인...")
        services = client.services

        print(f"📋 서비스 발견:")
        for service in services:
            print(f"   서비스: {service.uuid}")
            print(f"   특성 개수: {len(service.characteristics)}")

            for char in service.characteristics:
                print(f"     특성: {char.uuid}")
                print(f"     속성: {char.properties}")
                print(f"     설명: {char.description}")
                print()

        # 4. TESSEN 서비스 확인
        print("4. TESSEN 서비스 확인...")
        tessen_service = None
        for service in services:
            if service.uuid.lower() == TESSEN_SERVICE_UUID.lower():
                tessen_service = service
                print(f"✅ TESSEN 서비스 발견: {service.uuid}")
                break

        if not tessen_service:
            print("❌ TESSEN 서비스를 찾을 수 없습니다.")
            print("   사용 가능한 서비스:")
            for service in services:
                print(f"   - {service.uuid}")
            return

        # 5. 센서 데이터 특성 확인
        print("\n5. 센서 데이터 특성 확인...")
        sensor_char = None
        for char in tessen_service.characteristics:
            if char.uuid.lower() == SENSOR_DATA_CHAR_UUID.lower():
                sensor_char = char
                print(f"✅ 센서 데이터 특성 발견: {char.uuid}")
                print(f"   속성: {char.properties}")
                break

        if not sensor_char:
            print("❌ 센서 데이터 특성을 찾을 수 없습니다.")
            print("   사용 가능한 특성:")
            for char in tessen_service.characteristics:
                print(f"   - {char.uuid} (속성: {char.properties})")
            return

        # 6. 알림 설정 시도
        print("\n6. 알림 설정 시도...")
        try:
            print(f"   알림 설정 대상: {SENSOR_DATA_CHAR_UUID}")
            print(f"   핸들러 함수: {notification_handler}")

            await client.start_notify(SENSOR_DATA_CHAR_UUID, notification_handler)
            print("✅ 알림 설정 성공!")

            print("\n📡 센서 데이터 수신 대기 중... (30초)")
            print("   라켓을 움직여보세요!")
            print("   notification_handler가 호출되면 데이터가 출력됩니다!")

            # 30초 대기
            await asyncio.sleep(30)

            await client.stop_notify(SENSOR_DATA_CHAR_UUID)
            print("📡 알림 중지")

        except Exception as e:
            print(f"❌ 알림 설정 실패: {e}")

    except Exception as e:
        print(f"❌ 연결 실패: {e}")

    finally:
        if client.is_connected:
            await client.disconnect()
            print("🔌 연결 해제")

def notification_handler(sender, data):
    """알림 핸들러"""
    print(f"🎯 notification_handler 호출됨!")
    print(f"📊 데이터 수신: {len(data)} bytes")
    print(f"   데이터: {data.hex()}")
    print(f"   발신자: {sender}")

    # 14바이트 데이터인지 확인 (64바이트 버퍼에서 실제 데이터는 14바이트)
    if len(data) >= 14:
        print("   ✅ 충분한 데이터 크기 (14+ bytes)")
        try:
            # 7개 int16 값 파싱 (처음 14바이트만 사용)
            values = struct.unpack('<7h', data[:14])
            print(f"   파싱된 값: {values}")
            print(f"   가속도: X={values[0]/1000.0:.3f}, Y={values[1]/1000.0:.3f}, Z={values[2]/1000.0:.3f} m/s²")
            print(f"   자이로:  X={values[3]/1000.0:.3f}, Y={values[4]/1000.0:.3f}, Z={values[5]/1000.0:.3f} rad/s")
            print(f"   온도: {values[6]/100.0:.2f}°C")
        except Exception as e:
            print(f"   ❌ 데이터 파싱 오류: {e}")
    else:
        print(f"   ⚠️  데이터 크기 부족 (예상: 14+ bytes)")

if __name__ == "__main__":
    asyncio.run(debug_tessen_sensor())
