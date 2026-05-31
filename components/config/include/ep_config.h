#ifndef EP_CONFIG_H
#define EP_CONFIG_H

int ep_config_init(void);
int ep_config_load_file(const char *path);

int ep_config_set_int(const char *key, int value);
int ep_config_get_int(const char *key, int default_value);

int ep_config_set_bool(const char *key, int value);
int ep_config_get_bool(const char *key, int default_value);

int ep_config_set_string(const char *key, const char *value);
const char *ep_config_get_string(const char *key, const char *default_value);

#endif
