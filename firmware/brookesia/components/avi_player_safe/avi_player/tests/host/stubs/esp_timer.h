#pragma once

#include <stdint.h>

#include "esp_err.h"

typedef struct host_timer *esp_timer_handle_t;

typedef enum {
    ESP_TIMER_TASK = 0,
} esp_timer_dispatch_t;

typedef struct {
    void (*callback)(void *argument);
    void *arg;
    esp_timer_dispatch_t dispatch_method;
    const char *name;
} esp_timer_create_args_t;

esp_err_t esp_timer_create(const esp_timer_create_args_t *args, esp_timer_handle_t *handle);
esp_err_t esp_timer_start_periodic(esp_timer_handle_t handle, uint64_t period_us);
esp_err_t esp_timer_stop(esp_timer_handle_t handle);
esp_err_t esp_timer_delete(esp_timer_handle_t handle);
