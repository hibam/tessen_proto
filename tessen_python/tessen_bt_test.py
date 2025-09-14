#!/usr/bin/env python3
"""
TESSEN Tennis Sensor Bluetooth LE 테스트 프로그램
XIAO BLE nRF52840 + LSM6DSL 센서 데이터 수신
"""

import asyncio
import struct
import time
from datetime import datetime
from bleak import BleakClient, BleakScanner
import numpy as np

# TESSEN 센서 UUID 정보
TESSEN_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SENSOR_DATA_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
CONFIG_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"

# 센서 데이터 구조 (펌웨어에서 실제 사용하는 구조)
# int16_t data[7] = {
#     accel_x * 1000,    // m/s²
#     accel_y * 1000,    // m/s²
#     accel_z * 1000,    // m/s²
#     gyro_x * 1000,     // rad/s
#     gyro_y * 1000,     // rad/s
#     gyro_z * 1000,     // rad/s
#     temperature * 100  // °C
# };                     // 총 14 bytes (7 * int16)

class TessenSensor:
    def __init__(self):
        self.client = None
        self.device = None
        self.connected = False
        self.data_count = 0
        self.start_time = None

    async def scan_devices(self):
        """TESSEN 센서 디바이스 스캔"""
        print("🔍 TESSEN 센서 디바이스 스캔 중...")

        devices = await BleakScanner.discover(timeout=10.0)
        tessen_devices = []

        for device in devices:
            if device.name and "TESSEN" in device.name.upper():
                tessen_devices.append(device)
                print(f"✅ TESSEN 디바이스 발견: {device.name} ({device.address})")

        if not tessen_devices:
            print("❌ TESSEN 센서를 찾을 수 없습니다.")
            print("   - 센서가 켜져 있는지 확인하세요")
            print("   - Bluetooth가 활성화되어 있는지 확인하세요")
            return None

        return tessen_devices[0]  # 첫 번째 TESSEN 디바이스 반환

    async def connect(self, device):
        """TESSEN 센서에 연결"""
        print(f"🔗 TESSEN 센서 연결 시도: {device.name} ({device.address})")

        self.client = BleakClient(device.address)

        try:
            await self.client.connect()
            self.connected = True
            self.device = device
            self.start_time = time.time()
            print("✅ TESSEN 센서 연결 성공!")
            return True

        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False

    async def disconnect(self):
        """연결 해제"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            print("🔌 TESSEN 센서 연결 해제")

    def parse_sensor_data(self, data):
        """센서 데이터 파싱"""
        try:
            # 14바이트 데이터 구조 파싱 (7개 int16 값)
            # 64바이트 버퍼에서 실제 데이터는 14바이트
            if len(data) < 14:
                print(f"⚠️  데이터 크기 부족: {len(data)} bytes (최소: 14 bytes)")
                return None

            # 7개 int16 값 파싱 (처음 14바이트만 사용)
            values = struct.unpack('<7h', data[:14])

            # 스케일링 적용 (펌웨어에서 1000배, 100배로 전송)
            accel_x = values[0] / 1000.0  # m/s²
            accel_y = values[1] / 1000.0  # m/s²
            accel_z = values[2] / 1000.0  # m/s²
            gyro_x = values[3] / 1000.0   # rad/s
            gyro_y = values[4] / 1000.0   # rad/s
            gyro_z = values[5] / 1000.0   # rad/s
            temperature = values[6] / 100.0  # °C

            return {
                'accel': {'x': accel_x, 'y': accel_y, 'z': accel_z},
                'gyro': {'x': gyro_x, 'y': gyro_y, 'z': gyro_z},
                'temperature': temperature,
                'elapsed_time': time.time() - self.start_time if self.start_time else 0,
                'raw_data': values  # 디버깅용
            }

        except Exception as e:
            print(f"❌ 데이터 파싱 오류: {e}")
            return None

    def print_sensor_data(self, data):
        """센서 데이터 출력"""
        if not data:
            return

        self.data_count += 1

        # 매번 출력 (10Hz 전송)
        if True:  # 모든 데이터 출력
            # 가속도와 자이로 크기 계산
            accel_magnitude = (data['accel']['x']**2 + data['accel']['y']**2 + data['accel']['z']**2)**0.5
            gyro_magnitude = (data['gyro']['x']**2 + data['gyro']['y']**2 + data['gyro']['z']**2)**0.5

            print(f"\n 센서 데이터 #{self.data_count}")
            print(f"   시간: {data['elapsed_time']:.2f}s")
            print(f"   가속도: X={data['accel']['x']:7.3f}, Y={data['accel']['y']:7.3f}, Z={data['accel']['z']:7.3f} m/s² (크기: {accel_magnitude:5.2f})")
            print(f"   자이로:  X={data['gyro']['x']:7.3f}, Y={data['gyro']['y']:7.3f}, Z={data['gyro']['z']:7.3f} rad/s (크기: {gyro_magnitude:5.2f})")
            print(f"   온도: {data['temperature']:.2f}°C")
            print(f"   원시데이터: {data['raw_data']}")

    async def notification_handler(self, sender, data):
        """Bluetooth 알림 핸들러"""
        sensor_data = self.parse_sensor_data(data)
        self.print_sensor_data(sensor_data)

    async def start_data_stream(self):
        """센서 데이터 스트림 시작"""
        if not self.connected:
            print("❌ 센서가 연결되지 않았습니다.")
            return False

        try:
            # 알림 활성화
            await self.client.start_notify(SENSOR_DATA_CHAR_UUID, self.notification_handler)
            print("📡 센서 데이터 스트림 시작됨")
            print("   라켓을 움직여보세요!")
            print("   Ctrl+C로 종료하세요\n")
            return True

        except Exception as e:
            print(f"❌ 데이터 스트림 시작 실패: {e}")
            return False

    async def stop_data_stream(self):
        """센서 데이터 스트림 중지"""
        if self.client and self.connected:
            try:
                await self.client.stop_notify(SENSOR_DATA_CHAR_UUID)
                print("📡 센서 데이터 스트림 중지됨")
            except Exception as e:
                print(f"⚠️  스트림 중지 오류: {e}")

async def main():
    """메인 함수"""
    print("🎾 TESSEN Tennis Sensor 테스트 프로그램")
    print("=" * 50)

    sensor = TessenSensor()

    try:
        # 1. 디바이스 스캔
        device = await sensor.scan_devices()
        if not device:
            return

        # 2. 연결
        if not await sensor.connect(device):
            return

        # 3. 데이터 스트림 시작
        if not await sensor.start_data_stream():
            return

        # 4. 무한 루프 (Ctrl+C로 종료)
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 사용자에 의해 중단됨")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

    finally:
        # 5. 정리
        await sensor.stop_data_stream()
        await sensor.disconnect()

        if sensor.data_count > 0:
            print(f"\n📈 총 {sensor.data_count}개의 센서 데이터를 수신했습니다.")
            if sensor.start_time:
                duration = time.time() - sensor.start_time
                print(f"   수신 시간: {duration:.2f}초")
                print(f"   평균 수신률: {sensor.data_count/duration:.1f} Hz")

if __name__ == "__main__":
    asyncio.run(main())
