#ifndef EP_OSAL_ERR_H
#define EP_OSAL_ERR_H

typedef enum {
    EP_OK = 0,
    EP_ERR_INVAL = -1,
    EP_ERR_TIMEOUT = -2,
    EP_ERR_BUSY = -3,
    EP_ERR_UNSUPPORTED = -4
} ep_err_e;

#endif
