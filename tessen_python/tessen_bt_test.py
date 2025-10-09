#!/usr/bin/env python3
"""
TESSEN Tennis Sensor Bluetooth LE 테스트 프로그램 (실시간 그래프 포함)
XIAO BLE nRF52840 + LSM6DSL 센서 데이터 수신 및 시각화 (asyncio.Queue 사용)
"""

# -----------------------------------------------------------------------------
# 라이브러리 임포트
# -----------------------------------------------------------------------------
import asyncio
# asyncio: 비동기 프로그래밍을 위한 라이브러리. 여러 작업을 동시에 처리하는 것처럼 보이게 하여 I/O 바운드 작업(네트워크, 파일 등)의 효율을 높임.

import struct
# struct: C 구조체 형식의 바이너리 데이터를 파이썬 데이터 형식으로 변환하거나 그 반대로 변환할 때 사용.

import time
from bleak import BleakClient, BleakScanner
# bleak: Bluetooth Low Energy (BLE) 장치와 통신하기 위한 비동기 라이브러리.

from collections import deque
# deque: 양쪽 끝에서 빠르게 데이터를 추가하거나 제거할 수 있는 리스트와 유사한 컨테이너. 여기서는 그래프에 표시할 데이터 포인트를 고정된 크기로 유지하는 데 사용.

import matplotlib
matplotlib.use('TkAgg') # GUI 백엔드를 TkAgg로 명시적 설정 (Windows 호환성)
import matplotlib.pyplot as plt
# matplotlib: 파이썬에서 데이터 시각화를 위한 그래프를 그리는 데 사용되는 대표적인 라이브러리.

# -----------------------------------------------------------------------------
# 상수 및 전역 변수 정의
# -----------------------------------------------------------------------------
TESSEN_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SENSOR_DATA_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"

MAX_DATA_POINTS = 100  # 그래프에 표시할 최대 데이터 포인트 수

# 데이터 저장을 위한 deque 생성
timestamps = deque(maxlen=MAX_DATA_POINTS)
accel_x = deque(maxlen=MAX_DATA_POINTS)
accel_y = deque(maxlen=MAX_DATA_POINTS)
accel_z = deque(maxlen=MAX_DATA_POINTS)
gyro_x = deque(maxlen=MAX_DATA_POINTS)
gyro_y = deque(maxlen=MAX_DATA_POINTS)
gyro_z = deque(maxlen=MAX_DATA_POINTS)

class TessenSensor:
    def __init__(self, data_queue):
        self.client = None
        self.device = None
        self.connected = False
        self.data_count = 0
        self.start_time = None
        self.data_queue = data_queue # 데이터 교환을 위한 asyncio.Queue

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

    async def notification_handler(self, sender, data):
        """BLE 알림을 받았을 때 호출되는 콜백 함수 (데이터 생산자 역할)"""
        try:
            if len(data) < 14:
                return

            # 14바이트 데이터를 7개의 short(h) 정수로 언패킹
            values = struct.unpack('<7h', data[:14])

            # 스케일링 적용
            parsed_data = {
                'ax': values[0] / 1000.0, 'ay': values[1] / 1000.0, 'az': values[2] / 1000.0,
                'gx': values[3] / 1000.0, 'gy': values[4] / 1000.0, 'gz': values[5] / 1000.0,
            }

            self.data_count += 1

            # 파싱된 데이터를 Queue에 넣음. await는 Queue가 가득 찼을 경우 비워질 때까지 기다리게 함.
            await self.data_queue.put(parsed_data)

        except Exception as e:
            print(f"데이터 파싱/큐 저장 오류: {e}")

    async def start_data_stream(self):
        if not self.connected:
            print("센서가 연결되지 않았습니다.")
            return False
        try:
            # notification_handler를 콜백으로 지정하여 데이터 스트림 시작
            await self.client.start_notify(SENSOR_DATA_CHAR_UUID, self.notification_handler)
            print("센서 데이터 스트림 시작됨.")
            return True
        except Exception as e:
            print(f"데이터 스트림 시작 실패: {e}")
            return False

    async def stop_data_stream(self):
        if self.client and self.connected:
            try:
                await self.client.stop_notify(SENSOR_DATA_CHAR_UUID)
            except Exception:
                pass

def setup_plot():
    """그래프 초기 설정"""
    plt.ion() # 대화형 모드 켜기
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle('TESSEN Sensor Real-time Data', fontsize=16)

    # 가속도계 그래프 설정
    ax1.set_title('Accelerometer')
    ax1.set_ylabel('Acceleration (g)')
    line_ax, = ax1.plot([], [], 'r-', label='X')
    line_ay, = ax1.plot([], [], 'g-', label='Y')
    line_az, = ax1.plot([], [], 'b-', label='Z')
    ax1.legend()
    ax1.grid(True)

    # 자이로스코프 그래프 설정
    ax2.set_title('Gyroscope')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Angular Velocity (dps)')
    line_gx, = ax2.plot([], [], 'r-', label='X')
    line_gy, = ax2.plot([], [], 'g-', label='Y')
    line_gz, = ax2.plot([], [], 'b-', label='Z')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig, (ax1, ax2), (line_ax, line_ay, line_az), (line_gx, line_gy, line_gz)

async def graph_updater(data_queue, start_time, lines):
    """Queue에서 데이터를 꺼내 그래프를 업데이트하는 함수 (데이터 소비자 역할)"""
    acc_lines, gyro_lines = lines
    fig = plt.gcf() # 현재 Figure 객체 가져오기
    (ax1, ax2) = fig.get_axes()

    while True:
        try:
            # Queue가 비어있으면 잠시 대기. asyncio.wait_for로 타임아웃(0.1초) 설정
            data = await asyncio.wait_for(data_queue.get(), timeout=0.1)

            # 데이터 저장
            current_time = time.time() - start_time
            timestamps.append(current_time)
            accel_x.append(data['ax'])
            accel_y.append(data['ay'])
            accel_z.append(data['az'])
            gyro_x.append(data['gx'])
            gyro_y.append(data['gy'])
            gyro_z.append(data['gz'])

            # 그래프 데이터 업데이트
            for i, line in enumerate(acc_lines):
                line.set_data(timestamps, [accel_x, accel_y, accel_z][i])
            for i, line in enumerate(gyro_lines):
                line.set_data(timestamps, [gyro_x, gyro_y, gyro_z][i])

            # 그래프 범위 재설정
            ax1.relim()
            ax1.autoscale_view()
            ax2.relim()
            ax2.autoscale_view()

            # UI 업데이트. flush_events()는 GUI 이벤트를 처리.
            fig.canvas.flush_events()

        except asyncio.TimeoutError:
            # 큐에 데이터가 없으면 그냥 통과. 이 부분이 blocking을 방지.
            pass
        except Exception as e:
            # 그래프 창이 닫히는 등 예외 발생 시 루프 종료
            print(f"그래프 업데이트 중단: {e}")
            break

async def main():
    """메인 실행 함수"""
    print("TESSEN Tennis Sensor 테스트 프로그램 (실시간 그래프, Queue 방식)")
    print("=" * 60)

    # 데이터 생산자(BLE)와 소비자(그래프) 사이의 통신을 위한 큐 생성
    data_queue = asyncio.Queue()

    sensor = TessenSensor(data_queue)
    graph_task = None

    try:
        device = await sensor.scan_devices()
        if not device: return

        if not await sensor.connect(device): return

        # 그래프 설정 및 라인 객체 가져오기
        fig, axes, acc_lines, gyro_lines = setup_plot()

        # 그래프 업데이트를 위한 비동기 태스크 생성 및 시작
        graph_task = asyncio.create_task(
            graph_updater(data_queue, sensor.start_time, (acc_lines, gyro_lines))
        )

        if not await sensor.start_data_stream(): return

        print("\n데이터 수신 및 그래프 출력 중... (Ctrl+C 또는 그래프 창 닫기로 종료)")

        # 센서 연결이 끊어지거나 graph_task가 끝날 때까지 대기
        while sensor.connected and not graph_task.done():
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        if graph_task:
            graph_task.cancel() # 그래프 태스크 확실히 종료
        await sensor.stop_data_stream()
        await sensor.disconnect()

        if sensor.data_count > 0 and sensor.start_time:
            duration = time.time() - sensor.start_time
            print(f"   총 {sensor.data_count}개 데이터 수신 ({duration:.2f}초 동안, 평균 {sensor.data_count/duration:.1f} Hz)")
        
        print("프로그램을 종료합니다.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        # Jupyter 등 이미 이벤트 루프가 실행중인 환경을 위한 처리
        if "cannot run loop while another loop is running" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.run(main())
        else:
            raise