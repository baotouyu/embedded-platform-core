#include "power_board_service.h"

#include "ep_log.h"
#include "ep_osal_err.h"

int power_board_service_init(void)
{
    EP_LOGI("app", "power board service ready");
    return EP_OK;
}

int power_board_service_write(const void *buf, size_t len)
{
    (void)buf;
    (void)len;
    return EP_ERR_UNSUPPORTED;
}
