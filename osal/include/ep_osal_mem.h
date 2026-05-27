#ifndef EP_OSAL_MEM_H
#define EP_OSAL_MEM_H

#include <stddef.h>

void *ep_malloc(size_t size);
void ep_free(void *ptr);

#endif
