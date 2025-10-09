#!/usr/bin/env python3
"""
TESSEN Tennis Sensor Bluetooth LE 테스트 프로그램 (멀티스레드 GUI)
Matplotlib GUI(메인 스레드)와 BLE 통신(별도 스레드)을 분리하여 안정성을 확보한 버전.
"""

# ----------------------------------------------------------------------------
# 라이브러리 임포트
# ----------------------------------------------------------------------------
import asyncio
import struct
import time
import threading
import queue

from bleak import BleakClient, BleakScanner
from collections import deque

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# 상수 및 전역 변수 정의
# ----------------------------------------------------------------------------
TESSEN_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SENSOR_DATA_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

MAX_DATA_POINTS = 100  # 그래프에 표시할 최대 데이터 포인트 수

# ----------------------------------------------------------------------------
# BLE 통신 클래스 (Asyncio 기반)
# ----------------------------------------------------------------------------
class TessenSensor:
    def __init__(self, data_queue):
        self.client = None
        self.device = None
        self.connected = False
        self.data_count = 0
        self.start_time = None
        self.data_queue = data_queue

    def notification_handler(self, sender, data):
        """BLE 알림 콜백 (데이터 생산자)."""
        try:
            if len(data) < 14:
                return

            values = struct.unpack('<7h', data[:14])
            parsed_data = {
                'ax': values[0] / 1000.0, 'ay': values[1] / 1000.0, 'az': values[2] / 1000.0,
                'gx': values[3] / 1000.0, 'gy': values[4] / 1000.0, 'gz': values[5] / 1000.0,
                'time': time.time()
            }
            self.data_count += 1
            self.data_queue.put_nowait(parsed_data)
        except Exception as e:
            print(f"[BLE Thread] 데이터 처리 오류: {e}")

    async def scan_devices(self):
        print("TESSEN 센서 디바이스 스캔 중...")
        devices = await BleakScanner.discover(timeout=15.0)
        tessen_devices = [d for d in devices if d.name and "TESSEN" in d.name.upper()]
        if not tessen_devices:
            print("TESSEN 센서를 찾을 수 없습니다.")
            return None
        print(f"TESSEN 디바이스 발견: {tessen_devices[0].name} ({tessen_devices[0].address})")
        return tessen_devices[0]

    async def connect(self, device):
        print(f"TESSEN 센서 연결 시도: {device.name} ({device.address})")
        self.client = BleakClient(device.address)
        try:
            await self.client.connect()
            self.connected = True
            self.device = device
            self.start_time = time.time()
            print("TESSEN 센서 연결 성공!")
            return True
        except Exception as e:
            print(f"연결 실패: {e}")
            return False

    async def disconnect(self):
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            print("TESSEN 센서 연결 해제")

    async def start_data_stream(self):
        if not self.connected:
            print("센서가 연결되지 않았습니다.")
            return
        try:
            await self.client.start_notify(SENSOR_DATA_CHAR_UUID, self.notification_handler)
            print("센서 데이터 스트림 시작됨.")
        except Exception as e:
            print(f"데이터 스트림 시작 실패: {e}")

    async def stop_data_stream(self):
        if self.client and self.connected:
            try: await self.client.stop_notify(SENSOR_DATA_CHAR_UUID)
            except Exception: pass

# ----------------------------------------------------------------------------
# 블루투스 통신 스레드
# ----------------------------------------------------------------------------
class BluetoothThread(threading.Thread):
    def __init__(self, data_queue, stop_event):
        super().__init__()
        self.data_queue = data_queue
        self.stop_event = stop_event
        self.sensor = TessenSensor(data_queue)
        self.loop = None

    def run(self):
        """스레드의 메인 실행 루프. asyncio 이벤트 루프를 설정하고 실행합니다."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.bluetooth_main())
        self.loop.close()

    async def bluetooth_main(self):
        """실제 블루투스 로직을 처리하는 async 함수."""
        try:
            device = await self.sensor.scan_devices()
            if not device: return

            if not await self.sensor.connect(device): return

            await self.sensor.start_data_stream()
            print("\n데이터 수신 및 그래프 출력 중... (그래프 창을 닫으면 종료됩니다)")

            while not self.stop_event.is_set():
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"\n[Bluetooth Thread] 오류 발생: {e}")
        finally:
            print("[Bluetooth Thread] 종료 중...")
            await self.sensor.stop_data_stream()
            await self.sensor.disconnect()
            if self.sensor.data_count > 0 and self.sensor.start_time:
                duration = time.time() - self.sensor.start_time
                if duration > 0:
                    print(f"   총 {self.sensor.data_count}개 데이터 수신 ({duration:.2f}초 동안, 평균 {self.sensor.data_count/duration:.1f} Hz)")


# ----------------------------------------------------------------------------
# 메인 실행 함수 (GUI)
# ----------------------------------------------------------------------------
def main():
    """메인 실행 함수 - GUI를 담당합니다."""
    print("TESSEN Tennis Sensor 테스트 프로그램 (멀티스레드 GUI)")
    print("=" * 60)

    data_queue = queue.Queue()
    stop_event = threading.Event()

    # 블루투스 스레드 시작
    bt_thread = BluetoothThread(data_queue, stop_event)
    bt_thread.start()

    # --- Matplotlib GUI 설정 (메인 스레드) ---
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle('TESSEN Sensor Real-time Data', fontsize=16)

    # 데이터 저장을 위한 deque
    timestamps = deque(maxlen=MAX_DATA_POINTS)
    accel_x, accel_y, accel_z = deque(maxlen=MAX_DATA_POINTS), deque(maxlen=MAX_DATA_POINTS), deque(maxlen=MAX_DATA_POINTS)
    gyro_x, gyro_y, gyro_z = deque(maxlen=MAX_DATA_POINTS), deque(maxlen=MAX_DATA_POINTS), deque(maxlen=MAX_DATA_POINTS)

    # 가속도계 그래프
    ax1.set_title('Accelerometer')
    ax1.set_ylabel('Acceleration (g)')
    ax1.set_ylim(-25, 25)
    line_ax, = ax1.plot([], [], 'r-', label='X')
    line_ay, = ax1.plot([], [], 'g-', label='Y')
    line_az, = ax1.plot([], [], 'b-', label='Z')
    ax1.legend(loc='center right')
    ax1.grid(True)

    # 자이로스코프 그래프
    ax2.set_title('Gyroscope')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Angular Velocity (dps)')
    ax2.set_ylim(-3, 3)
    line_gx, = ax2.plot([], [], 'r-', label='X')
    line_gy, = ax2.plot([], [], 'g-', label='Y')
    line_gz, = ax2.plot([], [], 'b-', label='Z')
    ax2.legend(loc='center right')
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    start_time = time.time()
    
    # GUI 업데이트 루프
    while plt.fignum_exists(fig.number):
        try:
            # 큐에서 데이터 가져오기 (0.1초 타임아웃으로 블로킹)
            data = data_queue.get(timeout=0.1)

            timestamps.append(data['time'] - start_time)
            accel_x.append(data['ax'])
            accel_y.append(data['ay'])
            accel_z.append(data['az'])
            gyro_x.append(data['gx'])
            gyro_y.append(data['gy'])
            gyro_z.append(data['gz'])

            # 그래프 데이터 업데이트
            line_ax.set_data(timestamps, accel_x)
            line_ay.set_data(timestamps, accel_y)
            line_az.set_data(timestamps, accel_z)
            line_gx.set_data(timestamps, gyro_x)
            line_gy.set_data(timestamps, gyro_y)
            line_gz.set_data(timestamps, gyro_z)

            # X축 범위 자동 조정
            ax1.relim()
            ax1.autoscale_view(scalex=True, scaley=False)
            ax2.relim()
            ax2.autoscale_view(scalex=True, scaley=False)

        except queue.Empty:
            pass # 데이터가 없으면 그냥 넘어감
        except Exception as e:
            print(f"[Main Thread] GUI 업데이트 오류: {e}")
            break

        plt.pause(0.01)

    # GUI 창이 닫혔을 때
    print("그래프 창이 닫혔습니다. 프로그램을 종료합니다.")
    stop_event.set() # 블루투스 스레드에 종료 신호 전송
    bt_thread.join() # 스레드가 완전히 종료될 때까지 대기
    print("프로그램 종료 완료.")


if __name__ == "__main__":
    main()
