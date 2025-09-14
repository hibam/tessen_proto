#ifndef __CONST_H__
#define __CONST_H__

#include "Type.h"

/* ============================================================================
 * 일반 상수 정의
 * ============================================================================ */

/* 불린 상수 */
#define TRUE        (1)
#define FALSE       (0)

/* NULL 포인터 */
#define NULL_PTR    ((void*)0)

/* 일반적인 크기 상수 */
#define BYTE_SIZE   (1)
#define WORD_SIZE   (2)
#define DWORD_SIZE  (4)
#define QWORD_SIZE  (8)

/* ============================================================================
 * 유틸리티 매크로
 * ============================================================================ */

/* 배열 크기 매크로는 Zephyr에서 제공됨 */

/* 절댓값 매크로 */
#define ABS(a) ((a) < 0 ? -(a) : (a))

/* 비트 조작 매크로 (Zephyr에서 제공하지 않는 것만) */
#define SET_BIT(reg, bit) ((reg) |= (bit))
#define CLEAR_BIT(reg, bit) ((reg) &= ~(bit))
#define TOGGLE_BIT(reg, bit) ((reg) ^= (bit))

/* 바이트 조작 매크로 */
#define HIGH_BYTE(word) ((uint8)((word) >> 8))
#define LOW_BYTE(word)  ((uint8)((word) & 0xFF))
#define MAKE_WORD(high, low) ((uint16)(((high) << 8) | (low)))

/* 메모리 조작 매크로 */
#define MEMSET(ptr, val, size) memset((ptr), (val), (size))
#define MEMCPY(dst, src, size) memcpy((dst), (src), (size))
#define MEMCMP(ptr1, ptr2, size) memcmp((ptr1), (ptr2), (size))

/* 문자열 조작 매크로 */
#define STRLEN(str) strlen(str)
#define STRCPY(dst, src) strcpy((dst), (src))
#define STRCMP(str1, str2) strcmp((str1), (str2))

/* ============================================================================
 * 디버그 관련 정의
 * ============================================================================ */

/* 디버그 레벨 */
typedef enum _DEBUG_LEVEL {
    DEBUG_LEVEL_NONE = 0,
    DEBUG_LEVEL_ERROR,
    DEBUG_LEVEL_WARNING,
    DEBUG_LEVEL_INFO,
    DEBUG_LEVEL_DEBUG
} DEBUG_LEVEL;

/* 디버그 매크로 (나중에 구현) */
#define DEBUG_PRINT(level, fmt, ...) \
    do { \
        if ((level) <= DEBUG_LEVEL_INFO) { \
            printk(fmt, ##__VA_ARGS__); \
        } \
    } while (0)

#define DEBUG_ERROR(fmt, ...)   DEBUG_PRINT(DEBUG_LEVEL_ERROR, fmt, ##__VA_ARGS__)
#define DEBUG_WARNING(fmt, ...) DEBUG_PRINT(DEBUG_LEVEL_WARNING, fmt, ##__VA_ARGS__)
#define DEBUG_INFO(fmt, ...)    DEBUG_PRINT(DEBUG_LEVEL_INFO, fmt, ##__VA_ARGS__)
#define DEBUG_DEBUG(fmt, ...)   DEBUG_PRINT(DEBUG_LEVEL_DEBUG, fmt, ##__VA_ARGS__)

#endif /* __CONST_H__ */