/*
 * vsm_types.h - 차속 감시(Vehicle Speed Monitor) 공통 타입·상수
 *
 * 교육용 예제입니다.
 */

#ifndef _VSM_TYPES_H_
#define _VSM_TYPES_H_

#include <stdint.h>
#include <stdbool.h>

/* 경고 등급 */
typedef enum
{
    VSM_WARN_NONE = 0,
    VSM_WARN_LOW,        /* 암시적으로 1 */
    VSM_WARN_MID,
    VSM_WARN_HIGH
} vsm_warn_t;

#define VSM_TICK_INVALID    (0u - 1u)

/* 샘플 버퍼 크기 */
#define VSM_SAMPLE_MAX      8u

/* 과속 판정 기준 (SR-002). 부호 있는 정수 상수임에 주의 */
#define VSM_SPEED_LIMIT_KPH 200

/* 주의 경고 기준 (SR-003) */
#define VSM_SPEED_CAUTION_KPH 150

#endif /* _VSM_TYPES_H_ */
