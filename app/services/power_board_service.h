#ifndef POWER_BOARD_SERVICE_H
#define POWER_BOARD_SERVICE_H

#include <stddef.h>

int power_board_service_init(void);
int power_board_service_write(const void *buf, size_t len);

#endif
