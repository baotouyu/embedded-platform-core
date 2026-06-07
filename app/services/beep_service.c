#include "beep_service.h"

#include "ep_hal_pwm.h"
#include "ep_log.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"

#define BEEP_SERVICE_PERIOD_NS (1000000000u / BEEP_SERVICE_DEFAULT_FREQUENCY_HZ)
#define BEEP_SERVICE_DUTY_NS (BEEP_SERVICE_PERIOD_NS / 2u)

int beep_service_init(void)
{
    EP_LOGI("app", "beep service ready");
    return EP_OK;
}

int beep_service_beep_ms(unsigned int duration_ms)
{
    ep_pwm_t *pwm = 0;
    int rc;
    int cleanup_rc;

    if (duration_ms == 0u) {
        return EP_ERR_INVAL;
    }

    rc = ep_pwm_open(&pwm, "beep_pwm");
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_pwm_set(pwm, BEEP_SERVICE_PERIOD_NS, BEEP_SERVICE_DUTY_NS);
    if (rc != EP_OK) {
        cleanup_rc = ep_pwm_close(pwm);
        return cleanup_rc == EP_OK ? rc : cleanup_rc;
    }

    rc = ep_pwm_enable(pwm);
    if (rc != EP_OK) {
        cleanup_rc = ep_pwm_close(pwm);
        return cleanup_rc == EP_OK ? rc : cleanup_rc;
    }

    ep_sleep_ms(duration_ms);

    rc = ep_pwm_disable(pwm);
    cleanup_rc = ep_pwm_close(pwm);
    if (rc != EP_OK) {
        return rc;
    }

    return cleanup_rc;
}
