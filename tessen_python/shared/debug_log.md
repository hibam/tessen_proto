# TESSEN 프로젝트 디버그 로그

## 📅 로그 타임라인

### **2025-09-09 15:30 - Python 프로젝트 시작**
```
[Python AI] Python 환경 구축 시작
- 가상환경 생성: tessen_env
- 패키지 설치: bleak, matplotlib, pandas, numpy
- 상태: ✅ 완료
```

### **2025-09-09 15:45 - Bluetooth 연결 테스트**
```
[Python AI] TESSEN 센서 스캔 시도
- 스캔 결과: TESSEN Tennis Sensor 발견 (D9:90:BF:B7:69:8F)
- 연결 상태: ✅ 성공
- 문제: GATT 서비스 구조 오류
```

### **2025-09-09 16:00 - GATT 서비스 구조 문제**
```
[Python AI] GATT 서비스 확인 시도
- 오류: 'BleakGATTServiceCollection' 구조 불일치
- 오류: 'int' object has no attribute 'uuid'
- 상태: ❌ 실패
```

### **2025-09-09 16:15 - 프로젝트 간 소통 시작**
```
[Python AI] 센서 쪽과 소통 필요성 인식
- 문제: 센서 데이터 구조 불명
- 해결: 공유 상태 파일 생성
- 상태: 🔄 진행 중
```

### **2025-09-09 16:30 - 센서 프로젝트 개선**
```
[센서 AI] Bluetooth 전송 오류 해결
- 문제: ENOBUFS 오류 발생
- 해결: CONFIG_BT_ATT_PREPARE_COUNT=10으로 버퍼 증가
- 개선: 100Hz → 20Hz 전송 속도 조정
- 상태: ✅ 완료
```

### **2025-09-09 16:45 - 데이터 구조 최적화**
```
[센서 AI] 데이터 구조 최적화
- 기존: 33바이트 (float 기반)
- 개선: 14바이트 (int16 기반)
- 구조: 7개 int16 값 (가속도3 + 자이로3 + 온도1)
- 상태: ✅ 완료
```

### **2025-09-09 17:00 - Python 코드 수정**
```
[Python AI] 데이터 파싱 로직 수정
- 기존: struct.unpack('<fff...', data[0:33])
- 수정: struct.unpack('<7h', data[:14])
- 개선: 실시간 데이터 파싱 및 출력
- 상태: ✅ 완료
```

## 🔍 **디버그 정보**

### **Bluetooth 연결 로그**
```
연결 시도: TESSEN Tennis Sensor (D9:90:BF:B7:69:8F)
연결 상태: ✅ 성공
GATT 서비스: 5개 발견
TESSEN 서비스: 12345678-1234-5678-1234-56789abcdef0
센서 데이터 특성: 12345678-1234-5678-1234-56789abcdef1
```

### **데이터 구조 변경 로그**
```
[센서] 기존 구조 (33바이트):
struct sensor_data {
    float accel_x, accel_y, accel_z;    // 12 bytes
    float gyro_x, gyro_y, gyro_z;       // 12 bytes
    float temperature;                  // 4 bytes
    uint32_t timestamp;                 // 4 bytes
    uint8_t sequence;                   // 1 byte
}

[센서] 개선된 구조 (14바이트):
int16_t data[7] = {
    accel_x * 1000,    // m/s²
    accel_y * 1000,    // m/s²
    accel_z * 1000,    // m/s²
    gyro_x * 1000,     // rad/s
    gyro_y * 1000,     // rad/s
    gyro_z * 1000,     // rad/s
    temperature * 100  // °C
};
```

### **Python 파싱 로직 변경**
```python
# 기존 (33바이트)
accel_x, accel_y, accel_z = struct.unpack('<fff', data[0:12])
gyro_x, gyro_y, gyro_z = struct.unpack('<fff', data[12:24])
temperature = struct.unpack('<f', data[24:28])[0]

# 수정 (14바이트)
values = struct.unpack('<7h', data[:14])
accel_x, accel_y, accel_z = values[0]/1000.0, values[1]/1000.0, values[2]/1000.0
gyro_x, gyro_y, gyro_z = values[3]/1000.0, values[4]/1000.0, values[5]/1000.0
temperature = values[6]/100.0
```

## ⚠️ **발견된 문제들**

### **1. GATT 서비스 구조 오류**
- **문제**: `BleakGATTServiceCollection` 구조 불일치
- **원인**: bleak 라이브러리 버전 차이
- **해결**: 서비스 순회 방식 수정

### **2. 데이터 크기 불일치**
- **문제**: Python에서 33바이트 예상, 센서에서 14바이트 전송
- **원인**: 센서 최적화로 인한 구조 변경
- **해결**: Python 파싱 로직 수정

### **3. Bluetooth 전송 오류**
- **문제**: ENOBUFS 오류로 인한 전송 실패
- **원인**: 버퍼 크기 부족
- **해결**: 버퍼 크기 증가 및 전송 속도 조정

## 📊 **성능 개선 로그**

### **전송 속도 최적화**
```
기존: 100Hz 전송 → ENOBUFS 오류
개선: 20Hz 전송 → 안정적 전송
결과: 연속 전송 성공
```

### **데이터 크기 최적화**
```
기존: 33바이트 → Bluetooth MTU 제한
개선: 14바이트 → 효율적 전송
결과: 전송 성공률 향상
```

---
**마지막 업데이트**: 2025-09-09 17:00
**상태**: 센서-Python 연동 완료, 통합 테스트 준비
