#ifndef __TYPE_H__
#define __TYPE_H__

#include <zephyr/types.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>

/* ============================================================================
 * 아이디스 스타일 타입 정의
 * ============================================================================ */

/* 기본 정수 타입 (아이디스 스타일) */
typedef uint8_t     uint8;
typedef uint16_t    uint16;
typedef uint32_t    uint32;
typedef uint64_t    uint64;
typedef int8_t      int8;
typedef int16_t     int16;
typedef int32_t     int32;
typedef int64_t     int64;

/* 사용자 정의 타입 (아이디스 스타일) */
typedef uint8       U8;
typedef uint16      U16;
typedef uint32      U32;
typedef uint64      U64;
typedef int8        S8;
typedef int16       S16;
typedef int32       S32;
typedef int64       S64;

/* 부동소수점 타입 */
typedef float       F32;
typedef double      F64;

/* 불린 타입 */
typedef bool        BOOL;

/* 포인터 타입 */
typedef void*       PVOID;

/* 센서 관련 정의는 SensorInfo.h에서 관리됨 */
/* 상수, 매크로, 디버그 관련 정의는 Const.h에서 관리됨 */

/* ============================================================================
 * 함수 반환값 정의
 * ============================================================================ */

/* 일반 함수 반환값 타입 */
typedef enum _TESSEN_RESULT {
    TESSEN_OK = 0,          /* 성공 */
    TESSEN_ERROR = -1,      /* 일반 에러 */
    TESSEN_INVALID_PARAM,   /* 잘못된 파라미터 */
    TESSEN_NOT_INITIALIZED, /* 초기화되지 않음 */
    TESSEN_TIMEOUT,         /* 타임아웃 */
    TESSEN_BUSY,            /* 바쁨 */
    TESSEN_NOT_SUPPORTED    /* 지원되지 않음 */
} TESSEN_RESULT;


#endif /* __TYPE_H__ */
