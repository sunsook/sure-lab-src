/* diag_log.h - 진단 로그 기록 및 상태 레지스터 접근 */

#ifndef VSM_DIAG_LOG_H
#define VSM_DIAG_LOG_H

#include "vsm_types.h"

/* 경고 등급을 진단 이력에 기록한다 (SR-006) */
void dl_record(vsm_warn_t warn);

/* 문자열로 전달된 임계값을 파싱한다. 실패 시 -1 */
int32_t dl_parse_threshold(const char *text);

/* 진단 상태 레지스터를 읽는다 (타깃 보드 전용) */
uint32_t dl_read_status_reg(void);

#endif /* VSM_DIAG_LOG_H */
