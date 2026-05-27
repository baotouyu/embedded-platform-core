#ifndef EP_HAL_ADC_H
#define EP_HAL_ADC_H

#include <stdint.h>

#include "ep_hal_types.h"

int ep_adc_open(ep_adc_t **adc, const char *name);
int ep_adc_read(ep_adc_t *adc, uint32_t *value);

#endif
