#ifndef EP_HAL_PWM_H
#define EP_HAL_PWM_H

#include "ep_hal_types.h"

int ep_pwm_open(ep_pwm_t **pwm, const char *name);
int ep_pwm_set(ep_pwm_t *pwm, unsigned int period_ns, unsigned int duty_ns);
int ep_pwm_enable(ep_pwm_t *pwm);
int ep_pwm_disable(ep_pwm_t *pwm);
int ep_pwm_close(ep_pwm_t *pwm);

#endif
