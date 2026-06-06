#ifndef APP_CORE_H
#define APP_CORE_H

#include "app_context.h"

void app_context_init(app_context_t *app);
int app_core_start(app_context_t *app);
int app_core_run(app_context_t *app);

#endif
