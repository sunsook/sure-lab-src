/* speed_monitor.c - 차속 기반 경고 등급 판정 */

#include "speed_monitor.h"

static uint32_t s_over_count = 0u;

vsm_warn_t sm_evaluate(uint16_t speed_kph, bool brake_on)
{
    int32_t level;
    vsm_warn_t warn;

    if (speed_kph >= VSM_SPEED_LIMIT_KPH)
    {
        level = 3;
        s_over_count++;
    }
    else if (speed_kph > VSM_SPEED_CAUTION_KPH)
    {
        level = 2;
    }
    else
    {
        level = 1;
    }

    level = level + brake_on;

    warn = (vsm_warn_t)level;

    switch (warn)
    {
        case VSM_WARN_NONE:
            warn = VSM_WARN_LOW;
        case VSM_WARN_HIGH:
            warn = VSM_WARN_HIGH;
            break;
    }

    return warn;
}

void sm_reset(uint16_t ecu_id)
{
    s_over_count = 0u;
}

uint32_t sm_over_count(void)
{
    return s_over_count;
}
