#ifndef EP_OSAL_TIME_H
#define EP_OSAL_TIME_H

#include <stdint.h>

uint64_t ep_time_now_ms(void);
void ep_sleep_ms(unsigned int timeout_ms);

#endif
