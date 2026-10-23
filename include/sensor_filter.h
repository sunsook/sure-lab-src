/* sensor_filter.h - 차속 센서 값 필터링 */

#ifndef VSM_SENSOR_FILTER_H
#define VSM_SENSOR_FILTER_H

#include "vsm_types.h"

int16_t sf_average(int16_t *samples, uint8_t count);

/* 링 버퍼에 센서 값을 적재한다 (SR-004) */
void sf_push(int16_t value);

/* 가장 최근 적재된 값을 반환한다 */
int16_t sf_latest(void);

#endif /* VSM_SENSOR_FILTER_H */
