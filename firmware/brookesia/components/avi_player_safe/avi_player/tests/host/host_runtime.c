#include "host_runtime.h"

#include <assert.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#include "esp_err.h"
#include "esp_timer.h"
#include "freertos/event_groups.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

struct host_event_group {
    pthread_mutex_t mutex;
    pthread_cond_t condition;
    EventBits_t bits;
};

struct host_semaphore {
    pthread_mutex_t mutex;
};

struct host_task {
    pthread_t thread;
    TaskFunction_t function;
    void *argument;
};

struct host_timer {
    void (*callback)(void *argument);
    void *argument;
    bool running;
};

static _Thread_local TaskHandle_t s_current_task;
static atomic_int s_open_files;
static atomic_int s_fread_calls;
static atomic_int s_fread_fail_after = -1;

static void delay_milliseconds(long milliseconds)
{
    const struct timespec delay = {
        .tv_sec = milliseconds / 1000,
        .tv_nsec = (milliseconds % 1000) * 1000000L,
    };
    nanosleep(&delay, NULL);
}

const char *esp_err_to_name(esp_err_t error)
{
    switch (error) {
    case ESP_OK: return "ESP_OK";
    case ESP_FAIL: return "ESP_FAIL";
    case ESP_ERR_NO_MEM: return "ESP_ERR_NO_MEM";
    case ESP_ERR_INVALID_ARG: return "ESP_ERR_INVALID_ARG";
    case ESP_ERR_INVALID_STATE: return "ESP_ERR_INVALID_STATE";
    case ESP_ERR_INVALID_SIZE: return "ESP_ERR_INVALID_SIZE";
    case ESP_ERR_NOT_SUPPORTED: return "ESP_ERR_NOT_SUPPORTED";
    case ESP_ERR_TIMEOUT: return "ESP_ERR_TIMEOUT";
    default: return "ESP_ERR_UNKNOWN";
    }
}

FILE *host_tracked_fopen(const char *path, const char *mode)
{
    FILE *file = fopen(path, mode);
    if (file != NULL) {
        atomic_fetch_add(&s_open_files, 1);
    }
    return file;
}

int host_tracked_fclose(FILE *file)
{
    const int result = fclose(file);
    atomic_fetch_sub(&s_open_files, 1);
    return result;
}

size_t host_tracked_fread(void *buffer, size_t size, size_t count, FILE *file)
{
    const int call_index = atomic_fetch_add(&s_fread_calls, 1);
    const int fail_after = atomic_load(&s_fread_fail_after);
    if (fail_after >= 0 && call_index >= fail_after) {
        return 0;
    }
    return fread(buffer, size, count, file);
}

int host_open_file_count(void)
{
    return atomic_load(&s_open_files);
}

void host_fail_fread_after(int successful_calls)
{
    assert(successful_calls >= 0);
    atomic_store(&s_fread_calls, 0);
    atomic_store(&s_fread_fail_after, successful_calls);
}

void host_clear_fread_failure(void)
{
    atomic_store(&s_fread_fail_after, -1);
    atomic_store(&s_fread_calls, 0);
}

EventGroupHandle_t xEventGroupCreate(void)
{
    EventGroupHandle_t group = calloc(1, sizeof(*group));
    if (group != NULL) {
        pthread_mutex_init(&group->mutex, NULL);
        pthread_cond_init(&group->condition, NULL);
    }
    return group;
}

EventBits_t xEventGroupSetBits(EventGroupHandle_t group, EventBits_t bits)
{
    pthread_mutex_lock(&group->mutex);
    group->bits |= bits;
    const EventBits_t result = group->bits;
    pthread_cond_broadcast(&group->condition);
    pthread_mutex_unlock(&group->mutex);
    return result;
}

EventBits_t xEventGroupClearBits(EventGroupHandle_t group, EventBits_t bits)
{
    pthread_mutex_lock(&group->mutex);
    const EventBits_t previous = group->bits;
    group->bits &= ~bits;
    pthread_mutex_unlock(&group->mutex);
    return previous;
}

EventBits_t xEventGroupWaitBits(
    EventGroupHandle_t group,
    EventBits_t bits,
    BaseType_t clear_on_exit,
    BaseType_t wait_for_all,
    TickType_t ticks_to_wait
)
{
    pthread_mutex_lock(&group->mutex);
    while (true) {
        const EventBits_t matching = group->bits & bits;
        if ((wait_for_all && matching == bits) || (!wait_for_all && matching != 0)) {
            break;
        }
        if (ticks_to_wait == 0) {
            pthread_mutex_unlock(&group->mutex);
            return 0;
        }
        pthread_cond_wait(&group->condition, &group->mutex);
    }
    pthread_mutex_unlock(&group->mutex);

    // Let requests that were issued back-to-back coalesce, which exercises the
    // worker's explicit DEINIT > STOP > START precedence.
    delay_milliseconds(2);

    pthread_mutex_lock(&group->mutex);
    const EventBits_t result = group->bits;
    if (clear_on_exit) {
        group->bits &= ~bits;
    }
    pthread_mutex_unlock(&group->mutex);
    return result;
}

void vEventGroupDelete(EventGroupHandle_t group)
{
    pthread_cond_destroy(&group->condition);
    pthread_mutex_destroy(&group->mutex);
    free(group);
}

SemaphoreHandle_t xSemaphoreCreateMutex(void)
{
    SemaphoreHandle_t semaphore = calloc(1, sizeof(*semaphore));
    if (semaphore != NULL) {
        pthread_mutex_init(&semaphore->mutex, NULL);
    }
    return semaphore;
}

BaseType_t xSemaphoreTake(SemaphoreHandle_t semaphore, TickType_t ticks_to_wait)
{
    (void)ticks_to_wait;
    return pthread_mutex_lock(&semaphore->mutex) == 0 ? pdTRUE : pdFALSE;
}

BaseType_t xSemaphoreGive(SemaphoreHandle_t semaphore)
{
    return pthread_mutex_unlock(&semaphore->mutex) == 0 ? pdTRUE : pdFALSE;
}

void vSemaphoreDelete(SemaphoreHandle_t semaphore)
{
    pthread_mutex_destroy(&semaphore->mutex);
    free(semaphore);
}

static void *task_entry(void *argument)
{
    TaskHandle_t task = argument;
    s_current_task = task;
    task->function(task->argument);
    return NULL;
}

BaseType_t xTaskCreatePinnedToCore(
    TaskFunction_t function,
    const char *name,
    uint32_t stack_size,
    void *argument,
    UBaseType_t priority,
    TaskHandle_t *task_handle,
    BaseType_t core_id
)
{
    (void)name;
    (void)stack_size;
    (void)priority;
    (void)core_id;
    TaskHandle_t task = calloc(1, sizeof(*task));
    if (task == NULL) {
        return pdFAIL;
    }
    task->function = function;
    task->argument = argument;
    if (pthread_create(&task->thread, NULL, task_entry, task) != 0) {
        free(task);
        return pdFAIL;
    }
    pthread_detach(task->thread);
    *task_handle = task;
    return pdPASS;
}

TaskHandle_t xTaskGetCurrentTaskHandle(void)
{
    return s_current_task;
}

void vTaskDelete(TaskHandle_t task_handle)
{
    (void)task_handle;
    pthread_exit(NULL);
}

esp_err_t esp_timer_create(const esp_timer_create_args_t *args, esp_timer_handle_t *handle)
{
    if (args == NULL || args->callback == NULL || handle == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    esp_timer_handle_t timer = calloc(1, sizeof(*timer));
    if (timer == NULL) {
        return ESP_ERR_NO_MEM;
    }
    timer->callback = args->callback;
    timer->argument = args->arg;
    *handle = timer;
    return ESP_OK;
}

esp_err_t esp_timer_start_periodic(esp_timer_handle_t handle, uint64_t period_us)
{
    (void)period_us;
    if (handle == NULL || handle->running) {
        return ESP_ERR_INVALID_STATE;
    }
    handle->running = true;
    handle->callback(handle->argument);
    return ESP_OK;
}

esp_err_t esp_timer_stop(esp_timer_handle_t handle)
{
    if (handle == NULL || !handle->running) {
        return ESP_ERR_INVALID_STATE;
    }
    handle->running = false;
    return ESP_OK;
}

esp_err_t esp_timer_delete(esp_timer_handle_t handle)
{
    if (handle == NULL || handle->running) {
        return ESP_ERR_INVALID_STATE;
    }
    free(handle);
    return ESP_OK;
}
