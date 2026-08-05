#pragma once

#include <stdio.h>

#define HOST_LOG(level, tag, format, ...) do { \
    fprintf(stderr, "%s (%s): ", (level), (tag)); \
    fprintf(stderr, (format), ##__VA_ARGS__); \
    fputc('\n', stderr); \
} while (0)

#define ESP_LOGE(tag, format, ...) HOST_LOG("E", (tag), (format), ##__VA_ARGS__)
#define ESP_LOGW(tag, format, ...) HOST_LOG("W", (tag), (format), ##__VA_ARGS__)
#define ESP_LOGI(tag, format, ...) HOST_LOG("I", (tag), (format), ##__VA_ARGS__)
#define ESP_LOGD(tag, format, ...) ((void)0)
