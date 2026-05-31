#ifndef EP_LOG_H
#define EP_LOG_H

typedef enum {
    EP_LOG_LEVEL_ASSERT = 0,
    EP_LOG_LEVEL_ERROR = 1,
    EP_LOG_LEVEL_WARN = 2,
    EP_LOG_LEVEL_INFO = 3,
    EP_LOG_LEVEL_DEBUG = 4,
    EP_LOG_LEVEL_VERBOSE = 5
} ep_log_level_e;

int ep_log_init(void);
int ep_log_set_level(ep_log_level_e level);
ep_log_level_e ep_log_get_level(void);
int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...);

#define EP_LOGA(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ASSERT, tag, fmt, ##__VA_ARGS__)
#define EP_LOGE(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ERROR, tag, fmt, ##__VA_ARGS__)
#define EP_LOGW(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_WARN, tag, fmt, ##__VA_ARGS__)
#define EP_LOGI(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_INFO, tag, fmt, ##__VA_ARGS__)
#define EP_LOGD(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_DEBUG, tag, fmt, ##__VA_ARGS__)
#define EP_LOGV(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_VERBOSE, tag, fmt, ##__VA_ARGS__)

#endif
