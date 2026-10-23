#include <stdlib.h>
#include <errno.h>

#include "diag_log.h"

uint32_t g_diag_seq = 0u;

static uint8_t s_history[VSM_SAMPLE_MAX];
static uint8_t s_idx = 0u;

/* 타깃 보드 진단 상태 레지스터 주소 */
#define DIAG_STATUS_REG_ADDR 0x40001000u

void dl_record(vsm_warn_t warn)
{
    uint8_t code = (uint8_t)warn;

    s_history[s_idx++] = (uint8_t)(code + g_diag_seq++);

    if (s_idx >= (uint8_t)VSM_SAMPLE_MAX)
    {
        s_idx = 0u;
    }
}

int32_t dl_parse_threshold(const char *text)
{
    int32_t value;

    value = atoi(text); /* MISRA-DEVIATION 21.7 사유=기존 코드 · 3-③ 교정 예정 승인=강사 */

    return value;
}

uint32_t dl_read_status_reg(void)
{
    volatile uint32_t *reg = (volatile uint32_t *)DIAG_STATUS_REG_ADDR;

    return *reg;
}