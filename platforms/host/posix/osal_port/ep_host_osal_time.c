#define _POSIX_C_SOURCE 200809L

#include "ep_osal_time.h"

#include <errno.h>
#include <time.h>

uint64_t ep_time_now_ms(void)
{
    struct timespec now;

    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
        return 0;
    }

    return ((uint64_t)now.tv_sec * 1000u) + ((uint64_t)now.tv_nsec / 1000000u);
}

void ep_sleep_ms(unsigned int timeout_ms)
{
    struct timespec request;
    struct timespec remaining;

    request.tv_sec = (time_t)(timeout_ms / 1000u);
    request.tv_nsec = (long)(timeout_ms % 1000u) * 1000000L;

    while (nanosleep(&request, &remaining) != 0) {
        if (errno != EINTR) {
            return;
        }
        request = remaining;
    }
}
