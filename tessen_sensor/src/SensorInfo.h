#ifndef __SENSOR_INFO_H__
#define __SENSOR_INFO_H__

#include "Type.h"
#include "Const.h"

/* ============================================================================
 * 센서 관련 상수 정의
 * ============================================================================ */

/* LSM6DS 센서 I2C 주소 */
#define LSM6DS_I2C_ADDR         (0x6A)

/* LSM6DS 레지스터 주소 */
#define LSM6DSL_REG_CTRL1_XL    (0x10)
#define LSM6DSL_REG_CTRL2_G     (0x11)
#define LSM6DSL_REG_CTRL3_C     (0x12)
#define LSM6DSL_REG_WHO_AM_I    (0x0F)
#define LSM6DSL_REG_OUT_TEMP_L  (0x20)
#define LSM6DSL_REG_OUTX_L_G    (0x22)
#define LSM6DSL_REG_OUTX_L_XL   (0x28)

/* 센서 설정 값 */
#define LSM6DS_CTRL1_XL_104HZ_2G    (0x60)  /* ODR_XL = 104Hz, FS_XL = ±2g */
#define LSM6DS_CTRL2_G_104HZ_250DPS (0x60)  /* ODR_G = 104Hz, FS_G = ±250dps */
#define LSM6DS_CTRL3_C_DEFAULT      (0x44)  /* 기본 설정 */

/* 센서 샘플링 주기 */
#define SENSOR_SAMPLE_INTERVAL_MS   (10)    /* 100Hz */
#define SENSOR_POLL_INTERVAL_MS     (100)   /* 10Hz */

/* ============================================================================
 * 센서 데이터 구조체 정의
 * ============================================================================ */

/* 3축 벡터 구조체 */
typedef struct _Vector3DData{
    float x;
    float y;
    float z;
} Vector3DData;

/* 센서 원시 데이터 구조체 */
typedef struct {
    Vector3DData accel;        /* 가속도계 데이터 (m/s²) */
    Vector3DData gyro;         /* 자이로스코프 데이터 (rad/s) */
    float        temperature;  /* 온도 데이터 (°C) */
    uint32       timestamp;    /* 타임스탬프 (ms) */
    uint32       sample_count; /* 샘플 카운터 */
} SENSOR_DATA_T;

/* 센서 설정 구조체 */
typedef struct {
    uint8 ctrl1_xl;    /* CTRL1_XL 레지스터 값 */
    uint8 ctrl2_g;     /* CTRL2_G 레지스터 값 */
    uint8 ctrl3_c;     /* CTRL3_C 레지스터 값 */
} SENSOR_CONFIG_T;

/* 센서 상태 구조체 */
typedef struct {
    bool is_initialized;     /* 초기화 상태 */
    bool is_data_ready;      /* 데이터 준비 상태 */
    bool is_irq_enabled;     /* 인터럽트 활성화 상태 */
    uint32  error_count;        /* 에러 카운터 */
    uint32  sample_count;       /* 샘플 카운터 */
} SENSOR_STATUS_T;

/* ============================================================================
 * 센서 함수 반환값 정의
 * ============================================================================ */

/* 센서 함수 반환값 타입 */
typedef enum _SENSOR_RESULT {
    SENSOR_OK = 0,              /* 성공 */
    SENSOR_ERROR = -1,          /* 일반 에러 */
    SENSOR_INVALID_PARAM,       /* 잘못된 파라미터 */
    SENSOR_NOT_INITIALIZED,     /* 초기화되지 않음 */
    SENSOR_TIMEOUT,             /* 타임아웃 */
    SENSOR_BUSY,                /* 바쁨 */
    SENSOR_NOT_SUPPORTED,       /* 지원되지 않음 */
    SENSOR_I2C_ERROR,           /* I2C 통신 에러 */
    SENSOR_REGISTER_ERROR       /* 레지스터 접근 에러 */
} SENSOR_RESULT;

/* ============================================================================
 * 센서 관련 유틸리티 매크로
 * ============================================================================ */

/* 센서 데이터 유효성 검사 */
#define IS_VALID_SENSOR_DATA(data) \
    ((data) != NULL && (data)->sample_count > 0)

/* 센서 값 범위 검사 */
#define IS_VALID_ACCEL_RANGE(val) \
    ((val) >= -20.0f && (val) <= 20.0f)  /* ±20g 범위 */

#define IS_VALID_GYRO_RANGE(val) \
    ((val) >= -2000.0f && (val) <= 2000.0f)  /* ±2000dps 범위 */

#define IS_VALID_TEMP_RANGE(val) \
    ((val) >= -40.0f && (val) <= 85.0f)  /* -40°C ~ 85°C 범위 */

/* 센서 데이터 크기 */
#define SENSOR_DATA_SIZE         (sizeof(SENSOR_DATA_T))
#define VECTOR3D_DATA_SIZE       (sizeof(Vector3DData))

/* 센서 버퍼 크기 */
#define SENSOR_BUFFER_SIZE       (256)
#define SENSOR_QUEUE_SIZE        (32)

#endif /* __SENSOR_INFO_H__ */
