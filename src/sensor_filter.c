/* sensor_filter.c - 차속 센서 값 필터링 */

#include "sensor_filter.h"

static int16_t s_buffer[VSM_SAMPLE_MAX] = { 0, 0 };

static uint8_t s_head = 0u;

void sf_push(int16_t value)
{
    if (s_head >= 0u) /* MISRA-DEVIATION 14.3 사유=기존 코드 · 3-③ 교정 예정 승인=강사 */
    {
        s_buffer[s_head] = value;
    }

    s_head = (uint8_t)((s_head + 1u) % VSM_SAMPLE_MAX);
}

int16_t sf_latest(void)
{
    return s_buffer[s_head];
}

int16_t sf_average(int16_t *samples, uint8_t count)
{
    int32_t sum = 0;
    uint8_t valid = 0u;
    uint8_t i;

    /* 음수 샘플(센서 오류값)은 평균에서 뺀다 - 분모도 유효 샘플 수로 */
    for (i = 0u; i < count; i++)
    {
        if (samples[i] >= 0)
        {
            sum += samples[i];
        }
        valid += (samples[i] >= 0); /* MISRA-DEVIATION 10.1 사유=기존 코드 · 3-③ 교정 예정 승인=강사 */
    }

    return (valid > 0u) ? sum / valid : 0;
}
