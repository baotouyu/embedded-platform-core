#include "beep_service.h"

#include "ep_log.h"
#include "ep_osal_err.h"

int beep_service_init(void)
{
    EP_LOGI("app", "beep service ready");
    return EP_OK;
}

int beep_service_beep_ms(unsigned int duration_ms)
{
    (void)duration_ms;
    return EP_ERR_UNSUPPORTED;
}
