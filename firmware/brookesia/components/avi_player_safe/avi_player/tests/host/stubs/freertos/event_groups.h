#pragma once

#include "freertos/FreeRTOS.h"

typedef uint32_t EventBits_t;
typedef struct host_event_group *EventGroupHandle_t;

EventGroupHandle_t xEventGroupCreate(void);
EventBits_t xEventGroupSetBits(EventGroupHandle_t group, EventBits_t bits);
EventBits_t xEventGroupClearBits(EventGroupHandle_t group, EventBits_t bits);
EventBits_t xEventGroupWaitBits(
    EventGroupHandle_t group,
    EventBits_t bits,
    BaseType_t clear_on_exit,
    BaseType_t wait_for_all,
    TickType_t ticks_to_wait
);
void vEventGroupDelete(EventGroupHandle_t group);
