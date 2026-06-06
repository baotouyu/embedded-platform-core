#ifndef BEEP_SERVICE_H
#define BEEP_SERVICE_H

#define BEEP_SERVICE_DEFAULT_FREQUENCY_HZ 2700u

int beep_service_init(void);
int beep_service_beep_ms(unsigned int duration_ms);

#endif
