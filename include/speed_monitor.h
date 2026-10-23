/* speed_monitor.h - 차속 기반 경고 등급 판정 */

#ifndef VSM_SPEED_MONITOR_H
#define VSM_SPEED_MONITOR_H

#include "vsm_types.h"

/* 현재 차속과 제동 상태로 경고 등급을 판정한다 (SR-002, SR-003) */
vsm_warn_t sm_evaluate(uint16_t speed_kph, bool brake_on);

/* 과속 카운터를 초기화한다 (SR-005) */
void sm_reset(uint16_t ecu_id);

/* 누적 과속 횟수를 반환한다 */
uint32_t sm_over_count(void);

#endif /* VSM_SPEED_MONITOR_H */
