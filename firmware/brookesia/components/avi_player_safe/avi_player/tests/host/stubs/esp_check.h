#pragma once

#include "esp_log.h"

#define ESP_RETURN_ON_FALSE(condition, error, tag, format, ...) do { \
    if (!(condition)) { \
        ESP_LOGE((tag), (format), ##__VA_ARGS__); \
        return (error); \
    } \
} while (0)
