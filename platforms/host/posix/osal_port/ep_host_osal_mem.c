#include "ep_osal_mem.h"

#include <stdlib.h>

void *ep_malloc(size_t size)
{
    return malloc(size);
}

void ep_free(void *ptr)
{
    free(ptr);
}
