/* TC-02b — SR-002 경계: 차속 200 km/h 는 HIGH (요구사항 기반 시험 · ADS 에서 추가) */
#include "speed_monitor.h"

int tc_02b_sr002_boundary(void)
{
    return (sm_evaluate(200u, false) == VSM_WARN_HIGH) ? 0 : 1;
}
